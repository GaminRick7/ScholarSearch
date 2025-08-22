"""
BM25 implementation for research paper search
"""

import math
import re
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models.paper import Paper


class BM25Service:
    """BM25 implementation for research paper search"""
    
    def __init__(self, db: Session, k1: float = 1.2, b: float = 0.75):
        self.db = db
        self.k1 = k1  # term frequency saturation parameter
        self.b = b    # length normalization parameter
        self._build_index()
    
    def _build_index(self):
        """build the BM25 index from papers in the database"""
        print("Building BM25 index...")
        
        papers = self.db.query(Paper).filter_by(is_stub=False).all()
        
        self.documents = []
        self.paper_ids = []
        self.doc_lengths = []
        self.avg_doc_length = 0
        
        for paper in papers:
            text = f"{paper.title or ''} {paper.abstract or ''}"
            tokens = self._tokenize(text)
            
            self.documents.append(tokens)
            self.paper_ids.append(paper.id)
            self.doc_lengths.append(len(tokens))
        
        if self.doc_lengths:
            self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)
        
        self._build_term_indexes()
        
        print(f"BM25 index built with {len(self.documents)} documents")
    
    def add_paper(self, paper: Paper):
        """add a single paper to the BM25 index"""
        text = f"{paper.title or ''} {paper.abstract or ''}"
        tokens = self._tokenize(text)
        
        self.documents.append(tokens)
        self.paper_ids.append(paper.id)
        self.doc_lengths.append(len(tokens))
        
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)
        self._update_indexes_for_paper(len(self.documents) - 1, tokens)
        
        print(f"Added paper {paper.id} to BM25 index")
    
    def remove_paper(self, paper_id: str):
        """remove a paper from the BM25 index"""
        try:
            doc_index = self.paper_ids.index(paper_id)
            
            del self.documents[doc_index]
            del self.paper_ids[doc_index]
            del self.doc_lengths[doc_index]
            
            self._build_term_indexes()
            
            if self.doc_lengths:
                self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)
            
            print(f"Removed paper {paper_id} from BM25 index")
            
        except ValueError:
            print(f"Paper {paper_id} not found in BM25 index")
    
    def update_paper(self, paper: Paper):
        """update a paper in the BM25 index"""
        self.remove_paper(paper.id)
        self.add_paper(paper)
    
    def _update_indexes_for_paper(self, doc_index: int, tokens: List[str]):
        """update term frequency and document frequency indexes for a new paper"""
        term_counts = {}
        for token in tokens:
            term_counts[token] = term_counts.get(token, 0) + 1
        
        for term, freq in term_counts.items():
            if term not in self.term_freq:
                self.term_freq[term] = {}
            self.term_freq[term][doc_index] = freq
            
            if term not in self.doc_freq:
                self.doc_freq[term] = 0
            self.doc_freq[term] += 1
        
        self.total_docs = len(self.documents)
    
    def _tokenize(self, text: str) -> List[str]:
        """tokenize text into words"""
        if not text:
            return []
        
        tokens = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        
        return [token for token in tokens if token not in stop_words and len(token) > 2]
    
    def _build_term_indexes(self):
        """build term frequency and document frequency indexes"""
        self.term_freq = {}
        self.doc_freq = {}
        self.total_docs = len(self.documents)
        
        for doc_id, tokens in enumerate(self.documents):
            term_counts = {}
            for token in tokens:
                term_counts[token] = term_counts.get(token, 0) + 1
            
            for term, freq in term_counts.items():
                if term not in self.term_freq:
                    self.term_freq[term] = {}
                self.term_freq[term][doc_id] = freq
                
                if term not in self.doc_freq:
                    self.doc_freq[term] = 0
                self.doc_freq[term] += 1
    
    def _calculate_idf(self, term: str) -> float:
        """calculate inverse document frequency for a term"""
        if term not in self.doc_freq:
            return 0
        
        N = self.total_docs
        df = self.doc_freq[term]
        
        return math.log((N + 1) / (df + 1))
    
    def _calculate_bm25_score(self, doc_id: int, query_terms: List[str]) -> float:
        """calculate BM25 score for a document given query terms"""
        score = 0.0
        
        for term in query_terms:
            if term not in self.term_freq:
                continue
                
            if doc_id not in self.term_freq[term]:
                continue
            
            tf = self.term_freq[term][doc_id]
            doc_length = self.doc_lengths[doc_id]
            idf = self._calculate_idf(term)
            
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
            
            term_score = idf * (numerator / denominator)
            score += term_score
        
        return score
    
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """search for papers using BM25 ranking"""
        query_terms = self._tokenize(query)
        
        if not query_terms:
            return []
        
        scores = []
        for doc_id in range(len(self.documents)):
            score = self._calculate_bm25_score(doc_id, query_terms)
            if score > 0:
                scores.append((doc_id, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        top_results = scores[:limit]
        
        results = []
        for rank, (doc_id, score) in enumerate(top_results, 1):
            paper = self.db.query(Paper).filter_by(id=self.paper_ids[doc_id]).first()
            if paper:
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
                    "rank": rank,
                    "search_type": "bm25"
                })
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """get statistics about the BM25 index"""
        return {
            "total_documents": self.total_docs,
            "average_document_length": self.avg_doc_length,
            "unique_terms": len(self.term_freq),
            "parameters": {
                "k1": self.k1,
                "b": self.b
            }
        }
