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
from app.models.paper import Paper
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
        
        # Create sample data using bulk create
        logger.info("Creating sample data...")
        create_sample_data(db)
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def init_db():
    """Initialize the database with tables and sample data"""
    asyncio.run(init_db_async())

def create_sample_data(db: Session):
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
    
    async def create_papers_async():
        await paper_service.bulk_create_papers(papers=paper_templates)
    
    asyncio.run(create_papers_async())
    
    logger.info(f"Created {len(paper_templates)} sample papers using bulk create")
    
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

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Run initialization
    init_db()
