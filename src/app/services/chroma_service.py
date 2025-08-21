"""
ChromaDB service for ScholarNet 2.0 - Basic connectivity only
"""

import chromadb
from chromadb.config import Settings
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ChromaService:
    """Basic ChromaDB service for connectivity and status"""

    def __init__(self, host: str = "localhost", port: int = 8001):
        self.host = host
        self.port = port
        self.client = None
        self.collection = None

        try:
            self._initialize_client()
            self._initialize_collection()
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
            'ready_for_future': True
        }

    async def query(self, query_texts: List[str], n_results: int = 10):
        results = self.collection.query(
            query_texts=query_texts,
            n_results=n_results
        )

        return results

    async def add_documents(self, paper_ids: List[str], paper_text: List[str]):
        if not paper_text or not paper_ids:
            return

        self.collection.upsert(documents=paper_text,
                                     ids=paper_ids)  # upsert only adds a document if it doesn't already exist
