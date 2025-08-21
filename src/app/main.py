"""
ScholarNet 2.0 - FastAPI Application with ChromaDB Integration
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime
import redis
import time
from pydantic import BaseModel

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


class SearchRequest(BaseModel):
    query: str
    page: int = 1
    size: int = 20


@app.post('/api/v1/search')
async def search_papers(payload: SearchRequest, db: Session = Depends(get_db)):
    """Semantic search using ChromaDB embeddings; returns a single page of results."""
    try:
        start = time.perf_counter()

        # Single-page: ask Chroma for up to `size` results only
        n_results = max(1, min(200, payload.size))
        chroma_results = await chroma_service.query(query_texts=[payload.query], n_results=n_results)

        ids_groups = chroma_results.get('ids') or []
        distances_groups = chroma_results.get('distances') or []

        matched_ids = ids_groups[0] if ids_groups else []
        matched_distances = distances_groups[0] if distances_groups else []

        # Single-page selection
        selected_ids = matched_ids[:payload.size]
        selected_distances = matched_distances[:payload.size]

        if not selected_ids:
            return {
                "query": payload.query,
                "total_results": 0,
                "page": 1,
                "size": payload.size,
                "results": [],
                "search_time_ms": (time.perf_counter() - start) * 1000.0,
                "search_type": "semantic-bert",
            }

        # Fetch papers and preserve Chroma order
        papers = db.query(Paper).filter(Paper.id.in_(selected_ids)).all()
        paper_by_id = {str(p.id): p for p in papers}

        results = []
        for idx, pid in enumerate(selected_ids):
            paper = paper_by_id.get(pid)
            if not paper:
                continue
            score = selected_distances[idx] if idx < len(selected_distances) else None
            author_names = [author.name for author in paper.authors]
            results.append({
                "paper_id": paper.id,
                "title": paper.title,
                "abstract": paper.abstract,
                "authors": author_names,
                "venue": paper.venue,
                "year": paper.year,
                "n_citation": paper.n_citation,
                "score": score,
                "search_type": "semantic-bert",
            })

        return {
            "query": payload.query,
            "total_results": len(results),
            "page": 1,
            "size": payload.size,
            "results": results,
            "search_time_ms": (time.perf_counter() - start) * 1000.0,
            "search_type": "semantic-bert",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


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


@app.get('/query')
async def get_query(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Search for papers similar to the provided text using ChromaDB, then fetch full paper records from the database."""
    try:
        chroma_results = await chroma_service.query(query_texts=[q], n_results=2)

        ids_groups = chroma_results.get('ids') or []
        distances_groups = chroma_results.get('distances') or []
        documents_groups = chroma_results.get('documents') or []

        matched_ids = ids_groups[0] if ids_groups else []
        matched_distances = distances_groups[0] if distances_groups else []
        matched_docs = documents_groups[0] if documents_groups else []

        if not matched_ids:
            return {"query": q, "total_results": 0, "results": []}

        papers = db.query(Paper).filter(Paper.id.in_(matched_ids)).all()
        paper_by_id = {str(p.id): p for p in papers}

        results = []
        for idx, pid in enumerate(matched_ids):
            paper = paper_by_id.get(pid)
            if not paper:
                continue
            score = matched_distances[idx] if idx < len(matched_distances) else None
            results.append({
                "id": paper.id,
                "title": paper.title,
                "abstract": paper.abstract,
                "venue": paper.venue,
                "year": paper.year,
                "n_citation": paper.n_citation,
                "score": score,
            })

        return {"query": q, "total_results": len(results), "results": results}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query papers: {str(e)}")


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
