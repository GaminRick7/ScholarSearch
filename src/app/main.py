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
import requests
from urllib.parse import quote

# Import our new modules
from .core.database import get_db, create_tables
from .models.paper import Paper
from .services.paper_service import PaperService, PaperTemplate
from .services.chroma_service import ChromaService
from .services.bm25_service import BM25Service

# Initialize services at module level
chroma_service = ChromaService()

# Redis configuration with Docker support
import os
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

redis_client = redis.Redis(
    host=REDIS_HOST, 
    port=REDIS_PORT, 
    db=REDIS_DB,
    decode_responses=True,  # Automatically decode responses to strings
    socket_connect_timeout=5,  # 5 second connection timeout
    socket_timeout=5,  # 5 second socket timeout
    retry_on_timeout=True,  # Retry on timeout
    health_check_interval=30  # Health check every 30 seconds
)

# Test Redis connection
try:
    redis_client.ping()
    print(f"✅ Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    print(f"⚠️ Redis connection failed: {e}")
    print("   Make sure Redis is running (docker-compose up redis)")
    print("   Or set REDIS_HOST/REDIS_PORT environment variables")

# Cache performance tracking
cache_stats = {
    "hits": 0,
    "misses": 0,
    "total_requests": 0
}

def log_cache_hit(cache_key: str):
    """Log cache hit and update statistics"""
    cache_stats["hits"] += 1
    cache_stats["total_requests"] += 1
    print(f"Cache HIT: {cache_key}")

def log_cache_miss(cache_key: str):
    """Log cache miss and update statistics"""
    cache_stats["misses"] += 1
    cache_stats["total_requests"] += 1
    print(f"Cache MISS: {cache_key}")

def get_cache_stats():
    """Get current cache statistics"""
    total = cache_stats["total_requests"]
    hit_rate = (cache_stats["hits"] / total * 100) if total > 0 else 0
    return {
        "hits": cache_stats["hits"],
        "misses": cache_stats["misses"],
        "total_requests": total,
        "hit_rate_percent": round(hit_rate, 2)
    }

# Initialize BM25 service (will be set up when first needed)
bm25_service = None

def get_bm25_service(db: Session = Depends(get_db)) -> BM25Service:
    """Get BM25Service instance with database session"""
    global bm25_service
    if bm25_service is None:
        bm25_service = BM25Service(db)
    return bm25_service


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
        "features": ["PostgreSQL", "ChromaDB", "Redis", "Hybrid Search (BM25 + BERT)", "Redis Caching"],
        "search_plan": "Multi-stage retrieval with BM25 + BERT vectors, result fusion, enhanced ranking, and Redis caching for performance",
        "cache_endpoints": {
            "status": "/api/v1/cache/status",
            "clear_all": "/api/v1/cache/clear",
            "clear_specific": "/api/v1/cache/clear/{cache_key}",
            "warm": "/api/v1/cache/warm"
        }
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


@app.get("/api/v1/cache/status")
async def cache_status():
    """Get cache status and statistics"""
    try:
        # Get Redis info
        redis_info = redis_client.info()
        
        # Count search caches
        search_keys = redis_client.keys("search:*")
        search_cache_count = len(search_keys)
        
        # Get memory usage
        memory_usage = redis_info.get('used_memory_human', 'Unknown')
        
        # Get cache performance stats
        performance_stats = get_cache_stats()
        
        return {
            "status": "healthy",
            "redis_info": {
                "version": redis_info.get('redis_version', 'Unknown'),
                "memory_usage": memory_usage,
                "connected_clients": redis_info.get('connected_clients', 0),
                "total_commands_processed": redis_info.get('total_commands_processed', 0)
            },
            "cache_stats": {
                "search_caches": search_cache_count,
                "total_keys": redis_info.get('db0', {}).get('keys', 0)
            },
            "performance": performance_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.delete("/api/v1/cache/clear")
async def clear_cache():
    """Clear all search caches"""
    try:
        search_keys = redis_client.keys("search:*")
        if search_keys:
            deleted_count = redis_client.delete(*search_keys)
            return {
                "message": f"Cleared {deleted_count} search caches",
                "caches_cleared": deleted_count,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "message": "No search caches to clear",
                "caches_cleared": 0,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@app.delete("/api/v1/cache/clear/{cache_key}")
async def clear_specific_cache(cache_key: str):
    """Clear a specific cache by key"""
    try:
        # Ensure the key starts with 'search:' for security
        if not cache_key.startswith('search:'):
            raise HTTPException(status_code=400, detail="Invalid cache key format")
        
        deleted = redis_client.delete(cache_key)
        if deleted:
            return {
                "message": f"Cache {cache_key} cleared successfully",
                "cache_key": cache_key,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "message": f"Cache {cache_key} not found",
                "cache_key": cache_key,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@app.post("/api/v1/cache/warm")
async def warm_cache():
    """Warm up cache with popular search queries"""
    try:
        popular_queries = [
            "machine learning",
            "deep learning", 
            "natural language processing",
            "computer vision",
            "artificial intelligence",
            "neural networks",
            "data science",
            "big data",
            "blockchain",
            "cybersecurity"
        ]
        
        warmed_count = 0
        for query in popular_queries:
            try:
                # Create a search request for each popular query
                search_request = SearchRequest(
                    query=query,
                    page=1,
                    size=20,
                    bert_weight=2.0,
                    citation_weight=0.5
                )
                
                # This will trigger the search and cache the results
                await search_papers(search_request, db=next(get_db()))
                warmed_count += 1
                
            except Exception as e:
                print(f"Failed to warm cache for query '{query}': {e}")
                continue
        
        return {
            "message": f"Cache warming completed",
            "queries_warmed": warmed_count,
            "total_queries": len(popular_queries),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache warming failed: {str(e)}")


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
        paper_service: PaperService = Depends(get_paper_service),
        db: Session = Depends(get_db)
):
    """Create new papers"""
    try:
        await paper_service.bulk_create_papers(papers=papers)

        # Add new papers to BM25 index
        bm25 = get_bm25_service(db)
        for paper_template in papers:
            # Get the created paper from database
            paper = db.query(Paper).filter_by(id=paper_template.paper_id).first()
            if paper and not paper.is_stub:
                bm25.add_paper(paper)

        # Invalidate search caches when new papers are added
        try:
            # Clear all search caches since new papers might affect existing search results
            search_keys = redis_client.keys("search:*")
            if search_keys:
                redis_client.delete(*search_keys)
                print(f"Cleared {len(search_keys)} search caches after adding new papers")
        except Exception as e:
            print(f"Failed to clear search caches: {e}")

        return {
            "message": "Papers created successfully",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create papers: {str(e)}")


class SearchRequest(BaseModel):
    query: str
    page: int = 1
    size: int = 20
    bert_weight: float = 2.0  # weight for BERT results (default: 2x)
    citation_weight: float = 0.5  # weight for citation count (default: 0.5x)


@app.post('/api/v1/search')
async def search_papers(payload: SearchRequest, db: Session = Depends(get_db)):
    """hybrid search combining BM25 keyword search and BERT semantic search with Redis caching"""
    try:
        start = time.perf_counter()
        
        # Generate cache key based on search parameters
        import hashlib
        import json
        
        # Create a unique cache key for this search
        cache_params = {
            "query": payload.query.lower().strip() if payload.query else "",
            "page": payload.page,
            "size": payload.size,
            "bert_weight": round(payload.bert_weight, 2),
            "citation_weight": round(payload.citation_weight, 2)
        }
        
        # Create hash of parameters for cache key
        try:
            cache_key = f"search:{hashlib.md5(json.dumps(cache_params, sort_keys=True).encode()).hexdigest()}"
        except Exception as e:
            # Fallback to simple cache key if hashing fails
            cache_key = f"search:{payload.query[:50]}:{payload.page}:{payload.size}"
            print(f"Cache key generation failed, using fallback: {e}")
        
        # Check Redis cache first
        try:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                cached_data = json.loads(cached_result)
                # Add cache hit indicator
                cached_data["cached"] = True
                cached_data["cache_key"] = cache_key
                log_cache_hit(cache_key)
                return cached_data
        except Exception as e:
            # Log cache error but continue with search
            print(f"Cache check failed: {e}")
            log_cache_miss(cache_key)
        
        # get BM25 results
        bm25 = get_bm25_service(db)
        bm25_results = await bm25.search(payload.query, payload.size * 2)  # get more for better fusion
        
        # get BERT results from ChromaDB
        n_results = max(1, min(200, payload.size * 2))
        chroma_results = await chroma_service.query(query_texts=[payload.query], n_results=n_results)
        
        ids_groups = chroma_results.get('ids') or []
        distances_groups = chroma_results.get('distances') or []
        
        matched_ids = ids_groups[0] if ids_groups else []
        matched_distances = distances_groups[0] if distances_groups else []
        
        # combine results using reciprocal rank fusion
        combined_results = combine_bm25_and_bert(
            bm25_results, 
            matched_ids, 
            matched_distances, 
            payload.size,
            payload.bert_weight,
            payload.citation_weight
        )
        
        if not combined_results:
            result = {
                "query": payload.query,
                "total_results": 0,
                "page": 1,
                "size": payload.size,
                "results": [],
                "search_time_ms": (time.perf_counter() - start) * 1000.0,
                "search_type": "hybrid-bm25-bert-citations",
                "cached": False,
                "cache_key": cache_key
            }
            
            # Cache empty results for a shorter time
            try:
                redis_client.setex(cache_key, 300, json.dumps(result))  # 5 minutes for empty results
            except Exception as e:
                print(f"Failed to cache empty results: {e}")
            
            log_cache_miss(cache_key)
            return result

        # fetch paper details for combined results
        paper_ids = [result["paper_id"] for result in combined_results]
        papers = db.query(Paper).filter(Paper.id.in_(paper_ids)).all()
        paper_by_id = {str(p.id): p for p in papers}

        # calculate citation statistics for normalization
        citation_counts = [p.n_citation for p in papers if p.n_citation is not None]
        max_citations = max(citation_counts) if citation_counts else 1
        min_citations = min(citation_counts) if citation_counts else 0

        # build final response with citation boost or citation-only sorting
        final_results = []
        for result in combined_results:
            paper = paper_by_id.get(result["paper_id"])
            if paper:
                author_names = [author.name for author in paper.authors]
                
                # calculate citation boost (normalized between 0 and 1)
                citation_count = paper.n_citation or 0
                if max_citations > min_citations:
                    citation_normalized = (citation_count - min_citations) / (max_citations - min_citations)
                else:
                    citation_normalized = 0.0
                
                # Check if we're at maximum citation weight (citation-only sorting)
                if payload.citation_weight >= 1.0:
                    # At maximum weight, sort purely by citation count
                    final_score = citation_count
                    citation_boost = citation_count  # Use actual citation count for display
                    search_type = "citation-only-sorting"
                else:
                    # Normal hybrid scoring with citation boost
                    citation_boost = citation_normalized * payload.citation_weight * 0.05
                    final_score = result["hybrid_score"] + citation_boost
                    search_type = "hybrid-bm25-bert-citations"
                
                final_results.append({
                    "paper_id": paper.id,
                    "title": paper.title,
                    "abstract": paper.abstract,
                    "authors": author_names,
                    "venue": paper.venue,
                    "year": paper.year,
                    "n_citation": paper.n_citation,
                    "doi": paper.doi,
                    "score": final_score,
                    "bm25_score": result.get("bm25_score"),
                    "bert_score": result.get("bert_score"),
                    "citation_boost": citation_boost,
                    "citation_normalized": citation_normalized,
                    "search_type": search_type,
                })

        # Sort results by final score (descending)
        final_results.sort(key=lambda x: x["score"], reverse=True)

        result = {
            "query": payload.query,
            "total_results": len(final_results),
            "page": 1,
            "size": payload.size,
            "results": final_results,
            "search_time_ms": (time.perf_counter() - start) * 1000.0,
            "search_type": final_results[0]["search_type"] if final_results else "hybrid-bm25-bert-citations",
            "cached": False,
            "cache_key": cache_key
        }
        
        # Cache the search results
        try:
            # Determine TTL based on query characteristics
            if len(final_results) > 0:
                # Popular queries with results get longer cache time
                ttl = 1800  # 30 minutes
            else:
                # Queries with no results get shorter cache time
                ttl = 300   # 5 minutes
                
            redis_client.setex(cache_key, ttl, json.dumps(result))
        except Exception as e:
            print(f"Failed to cache search results: {e}")
        
        log_cache_miss(cache_key)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


def combine_bm25_and_bert(bm25_results: List[Dict], bert_ids: List[str], bert_distances: List[float], limit: int, bert_weight: float = 2.0, citation_weight: float = 0.5) -> List[Dict]:
    """combine BM25 and BERT results using reciprocal rank fusion with configurable weights and citation boost"""
    
    # create lookup for BM25 results
    bm25_lookup = {result["paper_id"]: result for result in bm25_results}
    
    # create lookup for BERT results
    bert_lookup = {}
    for idx, paper_id in enumerate(bert_ids):
        if idx < len(bert_distances):
            bert_lookup[paper_id] = {
                "paper_id": paper_id,
                "bert_score": bert_distances[idx],
                "bert_rank": idx + 1
            }
    
    # combine all unique papers
    all_papers = set(bm25_lookup.keys()) | set(bert_lookup.keys())
    
    # calculate hybrid scores using weighted RRF
    combined_results = []
    for paper_id in all_papers:
        bm25_data = bm25_lookup.get(paper_id, {})
        bert_data = bert_lookup.get(paper_id, {})
        
        # get ranks (1-based)
        bm25_rank = bm25_data.get("rank", len(bm25_results) + 1)
        bert_rank = bert_data.get("bert_rank", len(bert_ids) + 1)
        
        # RRF formula: 1 / (60 + rank)
        bm25_rrf = 1 / (60 + bm25_rank)
        bert_rrf = 1 / (60 + bert_rank)
        
        # weighted hybrid score: BM25 + (BERT * weight)
        hybrid_score = bm25_rrf + (bert_rrf * bert_weight)
        
        combined_results.append({
            "paper_id": paper_id,
            "hybrid_score": hybrid_score,
            "bm25_score": bm25_data.get("score"),
            "bert_score": bert_data.get("bert_score"),
            "bm25_rank": bm25_rank,
            "bert_rank": bert_rank,
            "bm25_rrf": bm25_rrf,
            "bert_rrf": bert_rrf,
            "bert_weight": bert_weight,
            "citation_weight": citation_weight
        })
    
    # sort by hybrid score (descending) and return top results
    combined_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return combined_results[:limit]



@app.get('/api/v1/bm25/stats')
async def bm25_stats(db: Session = Depends(get_db)):
    """Get BM25 index statistics"""
    try:
        bm25_service = get_bm25_service(db)
        return bm25_service.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get BM25 stats: {str(e)}")


@app.put("/api/v1/papers/{paper_id}")
async def update_paper(
        paper_id: str,
        paper_data: dict,
        paper_service: PaperService = Depends(get_paper_service),
        db: Session = Depends(get_db)
):
    """Update an existing paper"""
    try:
        paper = paper_service.update_paper(paper_id, paper_data)

        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        # Update paper in BM25 index
        bm25 = get_bm25_service(db)
        bm25.update_paper(paper)

        # Invalidate search caches when papers are updated
        try:
            # Clear all search caches since updated papers might affect existing search results
            search_keys = redis_client.keys("search:*")
            if search_keys:
                redis_client.delete(*search_keys)
                print(f"Cleared {len(search_keys)} search caches after updating paper {paper_id}")
        except Exception as e:
            print(f"Failed to clear search caches: {e}")

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

        # Remove paper from BM25 index
        bm25 = get_bm25_service(db)
        bm25.remove_paper(paper_id)

        # Invalidate search caches when papers are deleted
        try:
            # Clear all search caches since deleted papers might affect existing search results
            search_keys = redis_client.keys("search:*")
            if search_keys:
                redis_client.delete(*search_keys)
                print(f"Cleared {len(search_keys)} search caches after deleting paper {paper_id}")
        except Exception as e:
            print(f"Failed to clear search caches: {e}")

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


@app.post('/api/v1/papers/access')
async def access_paper(request: dict):
    """
    Smart paper access endpoint that tries DOI first, then falls back to Google Scholar.
    """
    try:
        title = request.get('title', '')
        authors = request.get('authors', [])
        
        if not title:
            raise HTTPException(status_code=400, detail="Paper title is required")
        
        # Try to find DOI via CrossRef API
        primary_author = authors[0] if authors else ""
        url = f"https://api.crossref.org/works?query.title={quote(title)}&query.author={quote(primary_author)}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            items = data.get('message', {}).get('items', [])
            if items:
                doi_title = items[0].get('title', [''])[0]
                doi_url = items[0].get('URL', None)
                
                # Check if titles are similar (partial match)
                if doi_url and _is_partial_match(title, doi_title):
                    return {
                        "success": True,
                        "url": doi_url,
                        "source": "doi",
                        "message": "Found paper via DOI"
                    }
        except Exception as e:
            print(f"CrossRef API error: {e}")
            # Continue to fallback
        
        # Fallback to Google Scholar
        author_query = f" {primary_author}" if primary_author else ""
        scholar_query = f"{title}{author_query}"
        encoded_query = quote(scholar_query)
        google_scholar_url = f'https://scholar.google.com/scholar?q={encoded_query}'
        
        return {
            "success": True,
            "url": google_scholar_url,
            "source": "google_scholar",
            "message": "Redirecting to Google Scholar"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to access paper: {str(e)}")


def _is_partial_match(query_title: str, doi_title: str) -> bool:
    """
    Check if two titles are partially matching (case-insensitive).
    """
    query_words = set(query_title.lower().split())
    doi_words = set(doi_title.lower().split())
    
    # Check if at least 60% of query words are in DOI title
    if not query_words:
        return False
    
    common_words = query_words.intersection(doi_words)
    match_ratio = len(common_words) / len(query_words)
    
    return match_ratio >= 0.6


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
