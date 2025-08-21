"""
Database initialization script for ScholarNet 2.0
"""
import asyncio
import logging
from typing import List

from sqlalchemy.orm import Session
from ..core.database import SessionLocal, create_tables, get_db
from ..models.paper import Paper, Author
from ..services.paper_service import PaperTemplate, AuthorTemplate
from ..services.paper_service import PaperService

import json
from datetime import datetime
import os

logger = logging.getLogger(__name__)

db_gen = get_db()   # this is a generator
db = next(db_gen)   # this gives you the actual Session

try:
    paper_service = PaperService(db)
    # call service methods here
finally:
    db_gen.close()  # this runs the generator's cleanup (db.close())



async def init_db():
    """Initialize the database with tables and sample data"""
    try:
        # Create tables
        logger.info("Creating database tables...")
        create_tables()
        logger.info("Database tables created successfully")

        # Check if data already exists
        db = SessionLocal()
        if db.query(Paper).count() > 0:
            logger.info("Database already contains data, skipping initialization")
            db.close()
            return

        # Create sample data
        logger.info("Creating sample data...")
        await create_sample_data(db)
        db.close()

        logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def create_sample_data(db: Session):
    """Create sample research papers data"""

    # Create sample authors
    authors = [
        Author(
            name="Yann LeCun",
            email="yann.lecun@nyu.edu",
            affiliation="New York University",
            orcid="0000-0001-8663-5578"
        ),
        Author(
            name="Yoshua Bengio",
            email="yoshua.bengio@umontreal.ca",
            affiliation="Université de Montréal",
            orcid="0000-0002-8084-1234"
        ),
        Author(
            name="Geoffrey Hinton",
            email="geoffrey.hinton@utoronto.ca",
            affiliation="University of Toronto",
            orcid="0000-0001-8663-5579"
        ),
        Author(
            name="Ashish Vaswani",
            email="ashish.vaswani@google.com",
            affiliation="Google Research",
            orcid="0000-0001-8663-5580"
        ),
        Author(
            name="Noam Shazeer",
            email="noam.shazeer@google.com",
            affiliation="Google Research",
            orcid="0000-0001-8663-5581"
        )
    ]

    for author in authors:
        db.add(author)
    db.flush()

    # Create sample papers

    example_papers: List[PaperTemplate] = [
        PaperTemplate(
            abstract="This paper introduces a novel graph neural network model for social network analysis.",
            authors=[
                AuthorTemplate(name="Alice Smith", affiliation="University of Toronto", orcid="0000-0001-2345-6789"),
                AuthorTemplate(name="Bob Johnson", affiliation="MIT"),
            ],
            n_citation=23,
            references=["paper_002", "paper_003"],
            title="Graph Neural Networks for Social Network Analysis",
            venue="Journal of Machine Learning Research",
            paper_id="paper_001",
            is_stub=False
        ),
        PaperTemplate(
            abstract="We survey recent advances in natural language processing, focusing on transformer models.",
            authors=[
                AuthorTemplate(name="Carol White", affiliation="Stanford University"),
            ],
            n_citation=150,
            references=["paper_001"],
            title="A Survey of Transformer Architectures in NLP",
            venue="ACL Conference",
            paper_id="paper_002",
            is_stub=False
        ),
        PaperTemplate(
            abstract="An empirical evaluation of recommendation systems for streaming services.",
            authors=[
                AuthorTemplate(name="David Lee", affiliation="Netflix Research"),
                AuthorTemplate(name="Eve Kim", affiliation="University of Waterloo"),
            ],
            n_citation=75,
            references=["paper_001", "paper_002"],
            title="Evaluation of Recommender Systems in Streaming",
            venue="KDD",
            paper_id="paper_003",
            is_stub=False
        )
    ]

    await paper_service.bulk_create_papers(papers=example_papers)

    # Commit all changes
    db.commit()
    logger.info(f"Created {len(example_papers)} sample papers with {len(authors)} authors")


if __name__ == "__main__":
    asyncio.run(init_db())
