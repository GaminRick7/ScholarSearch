"""
Database models for ScholarNet 2.0 research papers
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Table, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

# Association table for many-to-many relationship between papers and authors
paper_author = Table(
    'paper_author',
    Base.metadata,
    Column('paper_id', String, ForeignKey('papers.id'), primary_key=True),
    Column('author_id', String, ForeignKey('authors.id'), primary_key=True)
)

class Paper(Base):
    """Research paper model"""
    __tablename__ = "papers"

    # Primary key using UUID for scalability
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Paper metadata - matching the specified format
    title = Column(String(500), nullable=False, index=True)
    abstract = Column(Text, nullable=True)
    
    # Publication details
    venue = Column(String(255), nullable=True, index=True)
    year = Column(Integer, nullable=True, index=True)
    
    # Citation count
    n_citation = Column(Integer, default=0, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    authors = relationship("Author", secondary=paper_author, back_populates="papers")
    references = relationship("Reference", foreign_keys="Reference.citing_paper_id", back_populates="citing_paper")
    cited_by = relationship("Reference", foreign_keys="Reference.cited_paper_id", back_populates="cited_paper")

    def __repr__(self):
        return f"<Paper(id='{self.id}', title='{self.title[:50]}...')>"

class Author(Base):
    """Author model"""
    __tablename__ = "authors"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Author information
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    affiliation = Column(String(500), nullable=True)
    orcid = Column(String(50), nullable=True, unique=True, index=True)

    # Metrics
    paper_count = Column(Integer, default=0, index=True)
    citation_count = Column(Integer, default=0, index=True)
    h_index = Column(Integer, default=0, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    papers = relationship("Paper", secondary=paper_author, back_populates="authors")

    def __repr__(self):
        return f"<Author(id='{self.id}', name='{self.name}')>"

class Reference(Base):
    """Reference relationship model"""
    __tablename__ = "references"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Reference relationship
    citing_paper_id = Column(String, ForeignKey('papers.id'), nullable=False, index=True)
    cited_paper_id = Column(String, ForeignKey('papers.id'), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    citing_paper = relationship("Paper", foreign_keys=[citing_paper_id], back_populates="references")
    cited_paper = relationship("Paper", foreign_keys=[cited_paper_id], back_populates="cited_by")

    def __repr__(self):
        return f"<Reference(citing='{self.citing_paper_id}', cited='{self.cited_paper_id}')>"

# Create indexes for hybrid search performance (BM25 + BERT vectors)
Index('idx_papers_title', 'title')
Index('idx_papers_year_venue', 'year', 'venue')
Index('idx_papers_citations', 'n_citation')
Index('idx_authors_name', 'name')
Index('idx_references_papers', 'citing_paper_id', 'cited_paper_id')
