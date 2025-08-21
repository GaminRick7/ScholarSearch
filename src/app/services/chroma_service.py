"""
ChromaDB service for ScholarNet 2.0 - Basic connectivity only
"""

import chromadb
from chromadb.config import Settings
from typing import Dict, Any, List
import logging
from sentence_transformers import SentenceTransformer
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


class ChromaService:
    """Basic ChromaDB service for connectivity and status"""

    def __init__(self, host: str = "localhost", port: int = 8001, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.host = host
        self.port = port
        self.client = None
        self.collection = None
        self.model_name = model_name
        self.embedder: Optional[SentenceTransformer] = None

        try:
            self._initialize_client()
            self._initialize_collection()
            self._initialize_embedder()
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB service: {e}")
            raise

    def _initialize_client(self):
        """Initialize ChromaDB client"""
        try:
            # Connect to ChromaDB server
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(
                    chroma_api_impl="rest",
                    chroma_server_host=self.host,
                    chroma_server_http_port=self.port
                )
            )
            logger.info(f"Connected to ChromaDB at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise

    def _initialize_collection(self):
        """Initialize or get the papers collection"""
        try:
            collection_name = "scholarnet-papers"

            # Try to get existing collection
            try:
                self.collection = self.client.get_collection(collection_name)
                logger.info(f"Using existing collection: {collection_name}")
            except:
                # Create new collection if it doesn't exist
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": "Research papers collection (ready for future use)"}
                )
                logger.info(f"Created new collection: {collection_name}")

        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise

    def _initialize_embedder(self):
        """Load the local BERT/SBERT model for embeddings."""
        try:
            self.embedder = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model '{self.model_name}': {e}")
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the collection"""
        try:
            count = self.collection.count()
            return {
                'total_papers': count,
                'collection_name': self.collection.name,
                'chroma_host': f"{self.host}:{self.port}",
                'status': 'ready'
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {'error': str(e)}

    def is_healthy(self) -> bool:
        """Check if ChromaDB service is healthy"""
        try:
            # Simple health check
            self.collection.count()
            return True
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get service status information"""
        return {
            'service': 'ChromaDB',
            'host': self.host,
            'port': self.port,
            'healthy': self.is_healthy(),
            'collection': self.collection.name if self.collection else None,
            'ready_for_future': True,
            'embedding_model': self.model_name
        }

    async def query(self, query_texts: List[str], n_results: int = 10):
        if not query_texts:
            return {"ids": [], "distances": [], "documents": []}

        if self.embedder is None:
            raise RuntimeError("Embedding model not initialized")

        # Compute embeddings locally and query by embeddings to avoid server-side embedding dependency
        query_embeddings = self.embedder.encode(query_texts, convert_to_numpy=True, normalize_embeddings=True)
        if isinstance(query_embeddings, np.ndarray):
            query_embeddings = query_embeddings.tolist()

        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results
        )

        return results

    async def add_documents(self, paper_ids: List[str], paper_text: List[str]):
        if not paper_text or not paper_ids:
            return

        if self.embedder is None:
            raise RuntimeError("Embedding model not initialized")

        # Compute embeddings locally and upsert with embeddings
        embeddings = self.embedder.encode(paper_text, convert_to_numpy=True, normalize_embeddings=True)
        if isinstance(embeddings, np.ndarray):
            embeddings = embeddings.tolist()

        self.collection.upsert(
            documents=paper_text,
            ids=paper_ids,
            embeddings=embeddings
        )  # upsert only adds a document if it doesn't already exist
