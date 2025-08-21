"""
Paper service layer for ScholarNet 2.0
"""

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import Dict, Any, Set

from ..models.paper import Paper, Author, Reference, PaperAuthor
import logging

logger = logging.getLogger(__name__)


from typing import List, Optional
from pydantic import BaseModel


class AuthorTemplate(BaseModel):
    name: str
    email: Optional[str] = None
    affiliation: Optional[str] = None
    orcid: Optional[str] = None

    class Config:
        orm_mode = True


class PaperTemplate(BaseModel):
    abstract: Optional[str] = None
    authors: List[AuthorTemplate] = []
    n_citation: int = 0
    references: List[str] = []
    title: Optional[str] = None
    venue: Optional[str] = None
    paper_id: str
    is_stub: bool = False

    class Config:
        orm_mode = True


class PaperService:
    """Service class for paper-related operations"""

    def __init__(self, db: Session):
        self.db = db

    async def bulk_create_papers(self, papers: List[PaperTemplate]) -> None:
        """Main method to create papers with all their relationships."""
        try:
            # Prepare data structures
            paper_data = self._prepare_paper_data(papers)
            author_data = self._prepare_author_data(papers)

            # Handle referenced papers that don't exist yet
            self._create_stub_papers(papers)

            # Insert main entities
            self._insert_papers(paper_data)
            self._insert_authors(author_data)

            # Insert relationships
            author_map = self._get_author_mapping(author_data)
            self._insert_paper_authors(papers, author_map)
            self._insert_paper_references(papers)

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            import traceback
            print("ERROR:", e)
            print(traceback.format_exc())
            raise

    def _prepare_paper_data(self, papers: List[PaperTemplate]) -> List[Dict[str, Any]]:
        """Convert paper templates to database-ready dictionaries (no authors here)."""
        return [
            {
                "id": paper.paper_id,
                "title": paper.title,
                "n_citation": paper.n_citation,
                "abstract": paper.abstract,
                "venue": paper.venue,
                "in_chroma": False,
                "is_stub": paper.is_stub,  # respected if explicitly set
            }
            for paper in papers
        ]

    def _prepare_author_data(self, papers: List[PaperTemplate]) -> List[Dict[str, Any]]:
        """Extract unique authors from papers (AuthorTemplate objects)."""
        seen = set()
        authors = []

        for paper in papers:
            for author in paper.authors:  # <- now AuthorTemplate
                if author.name not in seen:
                    authors.append({
                        "name": author.name,
                        "email": author.email,
                        "affiliation": author.affiliation,
                        "orcid": author.orcid,
                    })
                    seen.add(author.name)

        return authors

    def _create_stub_papers(self, papers: List[PaperTemplate]) -> None:
        """Create stub entries for referenced papers that don't exist."""
        missing_ids = self._find_missing_reference_ids(papers)

        if not missing_ids:
            return

        stub_papers = [
            {"id": stub_id, "is_stub": True}
            for stub_id in missing_ids
        ]

        stmt = pg_insert(Paper).values(stub_papers).on_conflict_do_nothing(
            index_elements=[Paper.id]
        )
        self.db.execute(stmt)

    def _find_missing_reference_ids(self, papers: List[PaperTemplate]) -> Set[str]:
        """Find paper IDs that are referenced but don't exist in the database."""
        # Collect all referenced IDs
        all_ref_ids = {ref_id for paper in papers for ref_id in paper.references}

        # Get existing IDs from database
        existing_ids = {
            str(row[0])
            for row in self.db.query(Paper.id).filter(
                Paper.id.in_(all_ref_ids)
            )
        }

        # Get IDs from current batch
        current_batch_ids = {paper.paper_id for paper in papers}

        # Return missing IDs
        return all_ref_ids - existing_ids - current_batch_ids

    def _insert_papers(self, paper_data: List[Dict[str, Any]]) -> None:
        """Insert papers with upsert logic."""
        stmt = pg_insert(Paper).values(paper_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Paper.id],
            set_={
                Paper.title: stmt.excluded.title,
                Paper.n_citation: stmt.excluded.n_citation,
                Paper.abstract: stmt.excluded.abstract,
                Paper.venue: stmt.excluded.venue,
                Paper.in_chroma: stmt.excluded.in_chroma
            }
        )
        self.db.execute(stmt)

    def _insert_authors(self, author_data: List[Dict[str, str]]) -> None:
        """Insert authors, ignoring conflicts."""
        if not author_data:
            return

        # First, check which authors already exist to avoid the constraint violation
        author_names = [author["name"] for author in author_data]
        existing_authors = set(
            row[0] for row in self.db.query(Author.name).filter(
                Author.name.in_(author_names)
            ).all()
        )

        # Filter out existing authors
        new_authors = [
            author for author in author_data
            if author["name"] not in existing_authors
        ]

        if new_authors:
            stmt = pg_insert(Author).values(new_authors).on_conflict_do_nothing(
                constraint="uq_authors_name"
            )
            self.db.execute(stmt)

    def _get_author_mapping(self, author_data: List[Dict[str, str]]) -> Dict[str, str]:
        """Get mapping from author names to their database IDs."""
        if not author_data:
            return {}

        author_names = [author["name"] for author in author_data]
        rows = self.db.query(Author.name, Author.id).filter(
            Author.name.in_(author_names)
        ).all()

        return {name: author_id for name, author_id in rows}

    def _insert_paper_authors(self, papers: List[PaperTemplate], author_map: Dict[str, str]) -> None:
        """Insert paper-author relationships with proper ordering."""
        rels = []
        for paper in papers:
            for i, author in enumerate(paper.authors, start=1):
                if author.name not in author_map:
                    continue
                rels.append({
                    "paper_id": paper.paper_id,
                    "author_id": author_map[author.name],
                    "order": i,
                })

        if rels:
            stmt = pg_insert(PaperAuthor).values(rels).on_conflict_do_nothing(
                index_elements=[PaperAuthor.paper_id, PaperAuthor.author_id]
            )
            self.db.execute(stmt)

    def _insert_paper_references(self, papers: List[PaperTemplate]) -> None:
        """Insert paper reference relationships."""
        references = []

        for paper in papers:
            for ref_id in paper.references:
                references.append({
                    "citing_paper_id": paper.paper_id,
                    "cited_paper_id": ref_id
                })

        if references:
            stmt = pg_insert(Reference).values(references).on_conflict_do_nothing(
                index_elements=[
                    Reference.citing_paper_id,
                    Reference.cited_paper_id
                ]
            )
            self.db.execute(stmt)

    def create_paper(self, paper_data: dict) -> Paper:
        """Create a new paper with authors"""
        try:
            # Create paper
            paper = Paper(
                title=paper_data.get('title'),
                abstract=paper_data.get('abstract'),
                venue=paper_data.get('venue'),
                year=paper_data.get('year'),
                n_citation=paper_data.get('n_citation', 0)
            )

            self.db.add(paper)
            self.db.flush()  # Get the paper ID

            # Create or get authors and link them
            if 'authors' in paper_data:
                for author_data in paper_data['authors']:
                    author = self._get_or_create_author(author_data)
                    paper.authors.append(author)

            # Create references if provided
            if 'references' in paper_data:
                for ref_paper_id in paper_data['references']:
                    # Check if referenced paper exists
                    ref_paper = self.get_paper_by_id(ref_paper_id)
                    if ref_paper:
                        reference = Reference(
                            citing_paper_id=paper.id,
                            cited_paper_id=ref_paper_id
                        )
                        self.db.add(reference)

            self.db.commit()
            self.db.refresh(paper)

            logger.info(f"Created paper: {paper.title} (ID: {paper.id})")
            return paper

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating paper: {e}")
            raise

    def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """Get paper by ID with all relationships"""
        return self.db.query(Paper).filter_by(id=paper_id).first()

    def get_all_papers(self, page: int = 1, size: int = 20) -> tuple[List[Paper], int]:
        """Get all papers with pagination"""
        try:
            # Get total count
            total_count = self.db.query(Paper).count()

            # Get papers with pagination
            papers = self.db.query(Paper) \
                .filter_by(is_stub=False) \
                .order_by(Paper.n_citation.desc(), Paper.year.desc()) \
                .offset((page - 1) * size) \
                .limit(size) \
                .all()

            logger.info(f"Retrieved {len(papers)} papers (page {page}, size {size})")
            return papers, total_count

        except Exception as e:
            logger.error(f"Error getting papers: {e}")
            raise


def update_paper(self, paper_id: str, paper_data: dict) -> Optional[Paper]:
    """Update paper information"""
    try:
        paper = self.get_paper_by_id(paper_id)
        if not paper:
            return None

        # Update fields
        for field, value in paper_data.items():
            if hasattr(paper, field):
                setattr(paper, field, value)

        self.db.commit()
        self.db.refresh(paper)

        logger.info(f"Updated paper: {paper.title} (ID: {paper.id})")
        return paper

    except Exception as e:
        self.db.rollback()
        logger.error(f"Error updating paper: {e}")
        raise


def delete_paper(self, paper_id: str) -> bool:
    """Delete a paper and its relationships"""
    try:
        paper = self.get_paper_by_id(paper_id)
        if not paper:
            return False

        self.db.delete(paper)
        self.db.commit()

        logger.info(f"Deleted paper: {paper.title} (ID: {paper.id})")
        return True

    except Exception as e:
        self.db.rollback()
        logger.error(f"Error deleting paper: {e}")
        raise


def _get_or_create_author(self, author_data: dict) -> Author:
    """Get existing author or create new one"""
    author = self.db.query(Author).filter_by(name=author_data.get('name')).first()
    if not author:
        author = Author(
            name=author_data.get('name'),
            email=author_data.get('email'),
            affiliation=author_data.get('affiliation'),
            orcid=author_data.get('orcid')
        )
        self.db.add(author)
        self.db.flush()
    return author
