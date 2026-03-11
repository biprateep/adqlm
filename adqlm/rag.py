import numpy as np
import requests
from bs4 import BeautifulSoup
from google import genai
import re
import json
import os
from typing import List, Dict, Any, Optional

class DocumentEmbedder:
    """
    Handles document embedding, ingestion, and retrieval using Google Gemini Embeddings.
    """
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        model_name = model_name or os.environ.get('EMBEDDING_MODEL_NAME', 'models/text-embedding-004')
        """
        Initialize the embedder with a specific embedding model.

        Args:
            api_key (str): API key for Gemini.
            model_name (str): The name of the embedding model to use.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
             # In a real scenario, we might raise an error or warn, but let's just print for now
             # so the app doesn't crash on start if key is missing (though it won't work well)
             print("Warning: No API key provided for DocumentEmbedder.")
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

        self.model_name = model_name
        self.documents: List[str] = []
        self.embeddings: Optional[np.ndarray] = None
        self.doc_sources: List[str] = []

    def _embed(self, texts: List[str]) -> np.ndarray:
        """Helper to embed a list of texts using the API."""
        if not self.client:
            print("Error: Client not initialized. Cannot embed.")
            return np.array([])
            
        try:
            # Batch embedding might be needed if list is huge, but for now assumption is reasonable chunks
            # The python SDK supports batching automatically? Let's assume standard usage.
            # Actually, genai.Client.models.embed_content usually takes one or list?
            # Looking at SDK, we iterate or check if it supports list.
            # To be safe and efficient, we'll embed one by one or in small batches if the SDK demands,
            # but usually 'contents' can be a list.
            
            # Note: For 'models/text-embedding-004', the output dimensionality is 768 usually.
            
            embeddings = []
            # Simple loop for robustnes. Can optimize later.
            for text in texts:
                result = self.client.models.embed_content(
                    model=self.model_name,
                    contents=text
                )
                embeddings.append(result.embeddings[0].values)
            
            return np.array(embeddings)
        except Exception as e:
            print(f"Embedding error: {e}")
            return np.array([])

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
            new_embeddings = self._embed(new_docs)
            
            if new_embeddings.size > 0:
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
        
        new_embeddings = self._embed(new_docs)
        if new_embeddings.size > 0:
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
            
        query_vec = self._embed([query])
        if query_vec.size == 0:
            return []
            
        # Cosine similarity using numpy
        # sim = (A . B) / (||A|| * ||B||)
        # Assuming embeddings are not guaranteed to be normalized, though API often returns normalized ones.
        # Let's normalize just in case for correctness.
        
        def normalize(v):
            norm = np.linalg.norm(v, axis=1, keepdims=True)
            return v / (norm + 1e-10)
            
        norm_query = normalize(query_vec)
        norm_embeddings = normalize(self.embeddings)
        
        similarities = np.dot(norm_query, norm_embeddings.T).flatten()
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                'text': self.documents[idx],
                'source': self.doc_sources[idx],
                'score': float(similarities[idx])
            })
        return results
