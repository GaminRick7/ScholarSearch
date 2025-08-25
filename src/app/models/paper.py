"""
Database models for ScholarNet 2.0 research papers
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid


class Paper(Base):
    """Research paper model"""
    __tablename__ = "papers"

    # Primary key using UUID for scalability
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Paper metadata - matching the specified format
    title = Column(String(500), nullable=True, index=True)
    abstract = Column(Text, nullable=True)

    # Publication details
    venue = Column(String(255), nullable=True, index=True)
    year = Column(Integer, nullable=True, index=True)

    # Citation count
    n_citation = Column(Integer, default=0, index=True)

    # Paper access
    doi = Column(String(255), nullable=True, index=True)

    in_chroma = Column(Boolean, default=False)
    is_stub = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    authors = relationship("Author", secondary="paper_authors", back_populates="papers")
    references = relationship("Reference", foreign_keys="Reference.citing_paper_id", back_populates="citing_paper")
    cited_by = relationship("Reference", foreign_keys="Reference.cited_paper_id", back_populates="cited_paper")

    def __repr__(self):
        return f"<Paper(id='{self.id}', title='{self.title[:50]}...')>"


class Author(Base):
    """Author model"""
    __tablename__ = "authors"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Author information
    name = Column(String(255), nullable=False)
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
    papers = relationship("Paper", secondary="paper_authors", back_populates="authors")

    __table_args__ = (
        UniqueConstraint("name", name="uq_authors_name"),  # <--- explicit unique constraint
    )

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

    __table_args__ = (
        UniqueConstraint('citing_paper_id', 'cited_paper_id', name='uix_reference'),
    )

    def __repr__(self):
        return f"<Reference(citing='{self.citing_paper_id}', cited='{self.cited_paper_id}')>"


# Association object for paper-author relationship with additional data
class PaperAuthor(Base):
    __tablename__ = "paper_authors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String, ForeignKey("papers.id"), nullable=False, index=True)
    author_id = Column(String, ForeignKey("authors.id"), nullable=False, index=True)
    order = Column(Integer, default=1)  # Author order on the paper

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # No relationships - access through queries when needed

    __table_args__ = (
        UniqueConstraint('paper_id', 'author_id', name='uix_paper_author'),
    )

    def __repr__(self):
        return f"<PaperAuthor(paper_id='{self.paper_id}', author_id='{self.author_id}', order={self.order})>"


# Create indexes for hybrid search performance (BM25 + BERT vectors)
Index('idx_papers_title', 'title')
Index('idx_papers_year_venue', 'year', 'venue')
Index('idx_papers_citations', 'n_citation')
Index('idx_authors_name', 'name')
Index('idx_references_papers', 'citing_paper_id', 'cited_paper_id')
Index('idx_paper_authors_lookup', 'paper_id', 'author_id')
