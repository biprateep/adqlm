import numpy as np
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
import json
from typing import List, Dict, Any, Optional

class DocumentEmbedder:
    """
    Handles document embedding, ingestion, and retrieval using Sentence Transformers.
    """
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the embedder with a specific transformer model.

        Args:
            model_name (str): The name of the sentence-transformer model to use.
        """
        self.model = SentenceTransformer(model_name)
        self.documents: List[str] = []
        self.embeddings: Optional[np.ndarray] = None
        self.doc_sources: List[str] = []

    def load_json_docs(self, file_path: str):
        """
        Loads pre-built documents (schema or reference) from a JSON file.

        The JSON file is expected to be a list of dictionaries, each containing
        'text' and 'source' keys.

        Args:
            file_path (str): Path to the JSON file.
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            new_docs = [item['text'] for item in data]
            new_sources = [item['source'] for item in data]
            
            if not new_docs:
                return

            self.documents.extend(new_docs)
            self.doc_sources.extend(new_sources)
            
            print(f"Embedding {len(new_docs)} documents from {file_path}...")
            new_embeddings = self.model.encode(new_docs)
            
            if self.embeddings is None:
                self.embeddings = new_embeddings
            else:
                self.embeddings = np.vstack([self.embeddings, new_embeddings])
            print(f"Loaded {file_path}.")
            
        except FileNotFoundError:
            print(f"File not found at {file_path}")
        except Exception as e:
            print(f"Error loading docs from {file_path}: {e}")

    def fetch_text_from_url(self, url: str) -> str:
        """
        Fetches text content from a URL.

        Args:
            url (str): The URL to scrape.

        Returns:
            str: Cleaned text content from the page.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            # Kill all script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text()
            # Break into lines and remove leading/trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""

    def ingest_urls(self, urls: List[str]):
        """
        Ingests content from a list of URLs and updates the index.

        Args:
            urls (List[str]): List of URLs to process.
        """
        new_docs = []
        new_sources = []
        
        for url in urls:
            text = self.fetch_text_from_url(url)
            # Simple chunking by paragraphs or length
            # Here we just split by double newlines for simplicity
            chunks = [c.strip() for c in text.split('\n\n') if len(c.strip()) > 50]
            if not chunks:
                 chunks = [text] # Fallback
            
            new_docs.extend(chunks)
            new_sources.extend([url] * len(chunks))

        if not new_docs:
            return

        self.documents.extend(new_docs)
        self.doc_sources.extend(new_sources)
        
        new_embeddings = self.model.encode(new_docs)
        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves top_k documents relevant to the query.

        Args:
            query (str): The user query.
            top_k (int): Number of documents to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of results, each containing 'text', 'source', and 'score'.
        """
        if self.embeddings is None or len(self.documents) == 0:
            return []
            
        query_embedding = self.model.encode([query])
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                'text': self.documents[idx],
                'source': self.doc_sources[idx],
                'score': float(similarities[idx]) # Ensure python float
            })
        return results
