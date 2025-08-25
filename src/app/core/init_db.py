"""
Database initialization script for ScholarNet 2.0
"""

import logging
import asyncio
from sqlalchemy.orm import Session
import sys
import os

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.core.database import SessionLocal, create_tables, drop_tables
from app.models.paper import Paper, Author, Reference, PaperAuthor
from app.services.paper_service import PaperService, PaperTemplate, AuthorTemplate

logger = logging.getLogger(__name__)


async def init_db_async():
    """Initialize the database with tables and sample data"""
    try:
        # Drop existing tables to ensure clean schema
        logger.info("Dropping existing tables...")
        drop_tables()

        # Create tables with new schema
        logger.info("Creating database tables...")
        create_tables()
        logger.info("Database tables created successfully")

        # Check if data already exists
        db = SessionLocal()
        if db.query(Paper).count() > 0:
            logger.info("Database already contains data, skipping initialization")
            db.close()
            return

        # Load papers from CSV file
        logger.info("Loading papers from CSV file...")
        await load_papers_from_csv_async(db)

        logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def init_db():
    """Initialize the database with tables and sample data"""
    asyncio.run(init_db_async())


async def create_sample_data_async(db: Session):
    """Create sample research papers data using bulk create"""

    # Create paper templates for bulk insert
    paper_templates = [
        PaperTemplate(
            paper_id="paper_001",
            title="Deep Learning",
            abstract="Deep learning allows computational models that are composed of multiple processing layers to learn representations of data with multiple levels of abstraction.",
            venue="Nature",
            n_citation=52000,
            authors=[
                AuthorTemplate(
                    name="Yann LeCun",
                    email="yann.lecun@nyu.edu",
                    affiliation="New York University",
                    orcid="0000-0001-8663-5578"
                ),
                AuthorTemplate(
                    name="Yoshua Bengio",
                    email="yoshua.bengio@umontreal.ca",
                    affiliation="Université de Montréal",
                    orcid="0000-0002-8084-1234"
                ),
                AuthorTemplate(
                    name="Geoffrey Hinton",
                    email="geoffrey.hinton@utoronto.ca",
                    affiliation="University of Toronto",
                    orcid="0000-0001-8663-5579"
                )
            ],
            references=[]
        ),
        PaperTemplate(
            paper_id="paper_002",
            title="Attention Is All You Need",
            abstract="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder.",
            venue="NeurIPS",
            n_citation=45000,
            authors=[
                AuthorTemplate(
                    name="Ashish Vaswani",
                    email="ashish.vaswani@google.com",
                    affiliation="Google Research",
                    orcid="0000-0001-8663-5580"
                ),
                AuthorTemplate(
                    name="Noam Shazeer",
                    email="noam.shazeer@google.com",
                    affiliation="Google Research",
                    orcid="0000-0001-8663-5581"
                )
            ],
            references=["paper_001"]  # References Deep Learning
        ),
        PaperTemplate(
            paper_id="paper_003",
            title="BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            abstract="We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers.",
            venue="NAACL",
            n_citation=38000,
            authors=[
                AuthorTemplate(
                    name="Ashish Vaswani",
                    email="ashish.vaswani@google.com",
                    affiliation="Google Research",
                    orcid="0000-0001-8663-5580"
                )
            ],
            references=["paper_002"]
        ),
        PaperTemplate(
            paper_id="paper_004",
            title="Generative Adversarial Networks",
            abstract="We propose a new framework for estimating generative models via an adversarial process in which we simultaneously train two models.",
            venue="NeurIPS",
            n_citation=35000,
            authors=[
                AuthorTemplate(
                    name="Yoshua Bengio",
                    email="yoshua.bengio@umontreal.ca",
                    affiliation="Université de Montréal",
                    orcid="0000-0002-8084-1234"
                )
            ],
            references=[]
        ),
        PaperTemplate(
            paper_id="paper_005",
            title="ResNet: Deep Residual Learning for Image Recognition",
            abstract="Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks.",
            venue="CVPR",
            n_citation=42000,
            authors=[
                AuthorTemplate(
                    name="Yann LeCun",
                    email="yann.lecun@nyu.edu",
                    affiliation="New York University",
                    orcid="0000-0001-8663-5578"
                )
            ],
            references=["paper_001"]
        )
    ]

    paper_service = PaperService(db)

    # Create papers
    await paper_service.bulk_create_papers(papers=paper_templates)

    logger.info(f"Created {len(paper_templates)} sample papers using bulk create")

    # Add papers to ChromaDB
    await add_papers_to_chroma_async(db)


async def add_papers_to_chroma_async(db: Session):
    """Add papers to ChromaDB for vector search"""
    try:

        # import here to avoid circular imports
        from app.services.chroma_service import ChromaService

        chroma_service = ChromaService()

        unembedded_papers = db.query(Paper).filter_by(in_chroma=False, is_stub=False).all()

        if not unembedded_papers:
            logger.info("No new papers to add to ChromaDB")
            return

        paper_text = [f'{p.title}. {p.abstract}' for p in unembedded_papers]
        paper_ids = [str(p.id) for p in unembedded_papers]

        logger.info(f"Adding {len(paper_text)} papers to ChromaDB...")

        # add documents to chromadb
        await chroma_service.add_documents(paper_text=paper_text, paper_ids=paper_ids)

        for paper in unembedded_papers:
            paper.in_chroma = True

        db.commit()

        logger.info(f"Successfully added {len(paper_text)} papers to ChromaDB with BERT embeddings")

    except Exception as e:
        logger.error(f"Failed to add papers to ChromaDB: {e}")


async def load_papers_from_csv_async(db: Session, csv_file: str = "dblp-v10-2.csv"):
    """Load papers from CSV file into the database"""
    import csv
    import os

    if not os.path.exists(csv_file):
        logger.error(f"CSV file not found: {csv_file}")
        logger.info("Falling back to sample data...")
        await create_sample_data_async(db)
        return

    logger.info(f"Loading papers from {csv_file} (limited to first 10,000 papers)...")

    try:
        with open(csv_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            papers_batch = []
            batch_size = 1000
            total_loaded = 0
            batch_count = 0

            for row_num, row in enumerate(reader, 1):
                # Stop after loading 10,000 papers
                if total_loaded >= 10000:
                    logger.info(f"Reached limit of 10,000 papers. Stopping CSV processing.")
                    break

                try:
                    # Skip rows with missing essential data
                    if not row.get('id') or not row.get('title'):
                        continue

                    # Clean and parse the data
                    title = row.get('title', '').strip().replace('\n', ' ').replace('\r', ' ')
                    abstract = row.get('abstract', '').strip().replace('\n', ' ').replace('\r', ' ')
                    venue = row.get('venue', '').strip()
                    year_str = row.get('year', '')

                    # Parse year
                    year = None
                    if year_str and year_str.strip():
                        try:
                            year = int(year_str.strip())
                        except ValueError:
                            year = None

                    # Parse citation count
                    n_citation = 0
                    try:
                        n_citation = int(row.get('n_citation', 0))
                    except (ValueError, TypeError):
                        n_citation = 0

                    # Parse authors
                    authors_str = row.get('authors', '')
                    author_names = []
                    if authors_str and authors_str != '[]':
                        author_names = authors_str.strip('[]').replace("'", "").split(', ')
                        author_names = [name.strip() for name in author_names if name.strip()]

                    # Parse references
                    refs_str = row.get('references', '')
                    reference_ids = []
                    if refs_str and refs_str != '[]':
                        reference_ids = refs_str.strip('[]').replace("'", "").split(', ')
                        reference_ids = [ref.strip() for ref in reference_ids if ref.strip()]

                    # Create paper object
                    paper = Paper(
                        id=row.get('id', ''),
                        title=title,
                        abstract=abstract,
                        venue=venue,
                        year=year,
                        n_citation=n_citation
                    )

                    # Store additional data for later processing
                    paper_data = {
                        'paper': paper,
                        'author_names': author_names,
                        'reference_ids': reference_ids
                    }

                    papers_batch.append(paper_data)

                    # Process batch when it reaches the batch size
                    if len(papers_batch) >= batch_size:
                        batch_count += 1
                        logger.info(f"Processing batch {batch_count} (rows {row_num - batch_size + 1}-{row_num})")

                        loaded = await load_papers_batch_async(db, papers_batch)
                        total_loaded += loaded
                        papers_batch = []

                        # Progress update every 10 batches
                        if batch_count % 10 == 0:
                            logger.info(f"Progress: {total_loaded} papers loaded so far")

                        # Check if we've reached the limit
                        if total_loaded >= 10000:
                            logger.info(f"Reached limit of 10,000 papers. Stopping batch processing.")
                            break

                except Exception as e:
                    logger.error(f"Error processing row {row_num}: {e}")
                    continue

            # Process remaining papers in the last batch
            if papers_batch:
                batch_count += 1
                logger.info(f"Processing final batch {batch_count} ({len(papers_batch)} papers)")
                loaded = await load_papers_batch_async(db, papers_batch)
                total_loaded += loaded

            logger.info(f"CSV loading completed. Total papers loaded: {total_loaded}")

            # Update search indexes
            await update_search_indexes_async(db)

    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        logger.info("Falling back to sample data...")
        await create_sample_data_async(db)


async def load_papers_batch_async(db: Session, papers_batch: list) -> int:
    """Load a batch of papers with authors and references into the database"""
    try:
        # First, add all papers
        paper_objects = [data['paper'] for data in papers_batch]
        db.add_all(paper_objects)
        db.commit()
        logger.info(f"Successfully loaded batch of {len(paper_objects)} papers")

        # Now handle authors and references
        logger.info("Processing authors and references for batch...")

        # Create authors lookup for this batch
        authors_lookup = {}

        for paper_data in papers_batch:
            paper = paper_data['paper']
            author_names = paper_data['author_names']

            # Create or get authors
            for order, author_name in enumerate(author_names, 1):
                if author_name not in authors_lookup:
                    # Check if author already exists
                    existing_author = db.query(Author).filter_by(name=author_name).first()
                    if existing_author:
                        authors_lookup[author_name] = existing_author
                    else:
                        # Create new author
                        author = Author(name=author_name)
                        db.add(author)
                        db.flush()  # Get the ID
                        authors_lookup[author_name] = author

                # Create paper-author relationship
                paper_author = PaperAuthor(
                    paper_id=paper.id,
                    author_id=authors_lookup[author_name].id,
                    order=order
                )
                db.add(paper_author)

        # Handle references (only for papers that exist in our dataset)
        existing_paper_ids = {p.id for p in paper_objects}

        for paper_data in papers_batch:
            paper = paper_data['paper']
            reference_ids = paper_data['reference_ids']

            for ref_id in reference_ids:
                if ref_id in existing_paper_ids:
                    # Create reference relationship
                    reference = Reference(
                        citing_paper_id=paper.id,
                        cited_paper_id=ref_id
                    )
                    db.add(reference)

        db.commit()
        logger.info("Authors and references processed successfully for batch")
        return len(paper_objects)

    except Exception as e:
        db.rollback()
        logger.error(f"Error loading batch: {e}")
        return 0


async def update_search_indexes_async(db: Session):
    """Update ChromaDB and BM25 indexes after loading papers"""
    logger.info("Updating search indexes...")

    try:
        # Update ChromaDB
        logger.info("Updating ChromaDB index...")
        from app.services.chroma_service import ChromaService
        chroma_service = ChromaService()

        papers = db.query(Paper).all()

        # Process in smaller batches for ChromaDB
        chroma_batch_size = 100
        for i in range(0, len(papers), chroma_batch_size):
            batch = papers[i:i + chroma_batch_size]
            logger.info(f"Adding batch {i//chroma_batch_size + 1} to ChromaDB ({len(batch)} papers)")

            # Convert to documents format for ChromaDB
            documents = []
            metadatas = []
            ids = []

            for paper in batch:
                documents.append(f"{paper.title} {paper.abstract}")
                metadatas.append({
                    "paper_id": paper.id,
                    "title": paper.title,
                    "venue": paper.venue,
                    "year": paper.year
                })
                ids.append(paper.id)

            # Add to ChromaDB
            await chroma_service.add_documents(ids, documents)

        # Update BM25 index
        logger.info("Updating BM25 index...")
        from app.services.bm25_service import BM25Service
        bm25_service = BM25Service(db)
        bm25_service._build_index()

        logger.info("Search indexes updated successfully")

    except Exception as e:
        logger.error(f"Error updating indexes: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Run initialization
    init_db()
