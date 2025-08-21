"""
ScholarNet 2.0 - FastAPI Application with ChromaDB Integration
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime
import redis

# Import our new modules
from .core.database import get_db, create_tables
from .models.paper import Paper
from .services.paper_service import PaperService, PaperTemplate
from .services.chroma_service import ChromaService

# Initialize services at module level
chroma_service = ChromaService()
redis_client = redis.Redis(host='localhost', port=6379, db=0)
redis_client.ping()  # Test connection


# Dependency functions for services
def get_paper_service(db: Session = Depends(get_db)) -> PaperService:
    """Get PaperService instance with database session"""
    return PaperService(db)


# Initialize FastAPI app
app = FastAPI(
    title="ScholarNet 2.0 API (ChromaDB Edition)",
    description="Modern research paper platform with ChromaDB integration",
    version="2.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        create_tables()
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
        print("This is normal if the database is not yet running")


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "ScholarNet 2.0 API (ChromaDB Edition)",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "features": ["PostgreSQL", "ChromaDB", "Redis", "Hybrid Search (BM25 + BERT)"],
        "search_plan": "Multi-stage retrieval with BM25 + BERT vectors, result fusion, and enhanced ranking"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db = next(get_db())
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    # Check ChromaDB status
    try:
        chroma_stats = chroma_service.get_collection_stats()
        chroma_status = "healthy" if 'error' not in chroma_stats else "unhealthy"
    except Exception:
        chroma_status = "unhealthy"

    # Check Redis status
    try:
        redis_client.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "services": {
            "api": "healthy",
            "database": db_status,
            "chromadb": chroma_status,
            "redis": redis_status
        },
        "database_status": db_status,
        "search_engine_status": chroma_status,
        "cache_status": redis_status
    }


@app.get("/api/v1/papers/{paper_id}")
async def get_paper(
        paper_id: str,
        paper_service: PaperService = Depends(get_paper_service)
):
    """Get detailed information about a specific paper"""
    try:
        paper = paper_service.get_paper_by_id(paper_id)

        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        # Convert to response format
        author_responses = []
        for author in paper.authors:
            author_responses.append({
                "id": author.id,
                "name": author.name,
                "email": author.email,
                "affiliation": author.affiliation,
                "orcid": author.orcid,
                "paper_count": author.paper_count,
                "citation_count": author.citation_count,
                "h_index": author.h_index
            })

        # Get references (cited paper IDs)
        references = [ref.cited_paper_id for ref in paper.references]

        return {
            "id": paper.id,
            "title": paper.title,
            "abstract": paper.abstract,
            "venue": paper.venue,
            "year": paper.year,
            "n_citation": paper.n_citation,
            "authors": author_responses,
            "references": references,
            "created_at": paper.created_at.isoformat() if paper.created_at else None,
            "updated_at": paper.updated_at.isoformat() if paper.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve paper: {str(e)}")


@app.get("/api/v1/papers")
async def list_papers(
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
        db: Session = Depends(get_db),
        paper_service: PaperService = Depends(get_paper_service)
):
    """List all papers with pagination"""
    try:
        papers, total_count = paper_service.get_all_papers(page=page, size=size)

        # Convert to response format
        paper_responses = []
        for paper in papers:
            author_names = [author.name for author in paper.authors]

            paper_responses.append({
                "id": paper.id,
                "title": paper.title,
                "abstract": paper.abstract,
                "authors": author_names,
                "references": paper.references,
                "venue": paper.venue,
                "year": paper.year,
                "n_citation": paper.n_citation
            })

        return {
            "papers": paper_responses,
            "total": total_count,
            "page": page,
            "size": size,
            "pages": (total_count + size - 1) // size
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list papers: {str(e)}")


@app.post("/api/v1/papers")
async def create_papers(
        papers: List[PaperTemplate],
        paper_service: PaperService = Depends(get_paper_service)
):
    """Create new papers"""
    try:
        await paper_service.bulk_create_papers(papers=papers)

        return {
            "message": "Papers created successfully",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create papers: {str(e)}")


@app.put("/api/v1/papers/{paper_id}")
async def update_paper(
        paper_id: str,
        paper_data: dict,
        paper_service: PaperService = Depends(get_paper_service)
):
    """Update an existing paper"""
    try:
        paper = paper_service.update_paper(paper_id, paper_data)

        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        return {
            "message": "Paper updated successfully",
            "paper_id": paper.id,
            "title": paper.title
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update paper: {str(e)}")


@app.post('/api/v1/papers/vectors/')
async def add_papers_to_chroma(db: Session = Depends(get_db),):

    # get all unembedded non-stub papers
    unembedded_papers = db.query(Paper).filter_by(in_chroma=False, is_stub=False)

    paper_text = [f'{p.title}. {p.abstract}' for p in unembedded_papers.all()]
    paper_ids = [str(p.id) for p in unembedded_papers]

    print(paper_text)

    await chroma_service.add_documents(paper_text=paper_text, paper_ids=paper_ids)

    unembedded_papers.update(
        {
            Paper.in_chroma: True
        },
        synchronize_session=False
    )

    db.commit()


@app.get('/query/{query_text}')
async def get_query(query_text: str):
    results = await chroma_service.query(query_texts=[query_text], n_results=50)

    return results


@app.delete("/api/v1/papers/{paper_id}")
async def delete_paper(
        paper_id: str,
        db: Session = Depends(get_db),
        paper_service: PaperService = Depends(get_paper_service)
):
    """Delete a paper"""
    try:
        success = paper_service.delete_paper(paper_id)

        if not success:
            raise HTTPException(status_code=404, detail="Paper not found")

        return {
            "message": "Paper deleted successfully",
            "paper_id": paper_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete paper: {str(e)}")


@app.get("/api/v1/chromadb/status")
async def chromadb_status():
    """Check ChromaDB status and collection info"""
    try:
        status = chroma_service.get_status()

        return {
            "status": "available" if status['healthy'] else "unavailable",
            "service_info": status,
            "message": "ChromaDB is running and ready for future use"
        }

    except Exception as e:
        return {
            "status": "unavailable",
            "error": str(e),
            "message": "ChromaDB is not accessible"
        }


@app.get("/api/v1/chromadb/collection")
async def chromadb_collection():
    """Get basic information about the ChromaDB collection"""
    try:
        stats = chroma_service.get_collection_stats()

        return {
            "collection_name": stats.get('collection_name', 'Unknown'),
            "total_papers": stats.get('total_papers', 0),
            "chroma_host": stats.get('chroma_host', 'Unknown'),
            "status": stats.get('status', 'unknown'),
            "ready_for_future": True
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "ready_for_future": False
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
