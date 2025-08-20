"""
Paper service layer for ScholarNet 2.0
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.models.paper import Paper, Author, Reference
import logging

logger = logging.getLogger(__name__)

class PaperService:
    """Service class for paper-related operations"""

    def __init__(self, db: Session):
        self.db = db

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
        return self.db.query(Paper).filter(Paper.id == paper_id).first()

    def get_all_papers(self, page: int = 1, size: int = 20) -> tuple[List[Paper], int]:
        """Get all papers with pagination"""
        try:
            # Get total count
            total_count = self.db.query(Paper).count()

            # Get papers with pagination
            papers = self.db.query(Paper)\
                          .order_by(Paper.n_citation.desc(), Paper.year.desc())\
                          .offset((page - 1) * size)\
                          .limit(size)\
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
        author = self.db.query(Author).filter(Author.name == author_data.get('name')).first()
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
