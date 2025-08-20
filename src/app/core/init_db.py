"""
Database initialization script for ScholarNet 2.0
"""

import logging
from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal, create_tables
from app.models.paper import Paper, Author, Reference
import json
from datetime import datetime
import os

logger = logging.getLogger(__name__)

def init_db():
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
        create_sample_data(db)
        db.close()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def create_sample_data(db: Session):
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
    papers = [
        Paper(
            title="Deep Learning",
            abstract="Deep learning allows computational models that are composed of multiple processing layers to learn representations of data with multiple levels of abstraction.",
            venue="Nature",
            year=2015,
            n_citation=52000
        ),
        Paper(
            title="Attention Is All You Need",
            abstract="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder.",
            venue="NeurIPS",
            year=2017,
            n_citation=45000
        ),
        Paper(
            title="BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            abstract="We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers.",
            venue="NAACL",
            year=2019,
            n_citation=38000
        ),
        Paper(
            title="Generative Adversarial Networks",
            abstract="We propose a new framework for estimating generative models via an adversarial process in which we simultaneously train two models.",
            venue="NeurIPS",
            year=2014,
            n_citation=35000
        ),
        Paper(
            title="ResNet: Deep Residual Learning for Image Recognition",
            abstract="Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks.",
            venue="CVPR",
            year=2016,
            n_citation=42000
        )
    ]
    
    for paper in papers:
        db.add(paper)
    db.flush()
    
    # Link papers to authors
    papers[0].authors = [authors[0], authors[1], authors[2]]  # Deep Learning
    papers[1].authors = [authors[3], authors[4]]  # Attention Is All You Need
    papers[2].authors = [authors[3]]  # BERT
    papers[3].authors = [authors[1]]  # GAN
    papers[4].authors = [authors[0]]  # ResNet
    
    # Create some reference relationships
    references = [
        Reference(
            citing_paper_id=papers[1].id,  # Attention Is All You Need
            cited_paper_id=papers[0].id,   # Deep Learning
        ),
        Reference(
            citing_paper_id=papers[2].id,  # BERT
            cited_paper_id=papers[1].id,   # Attention Is All You Need
        ),
        Reference(
            citing_paper_id=papers[4].id,  # ResNet
            cited_paper_id=papers[0].id,   # Deep Learning
        )
    ]
    
    for reference in references:
        db.add(reference)
    
    # Update author metrics
    for author in authors:
        author.paper_count = len(author.papers)
        author.citation_count = sum(paper.n_citation for paper in author.papers)
    
    # Commit all changes
    db.commit()
    logger.info(f"Created {len(papers)} sample papers with {len(authors)} authors")

if __name__ == "__main__":
    init_db()
