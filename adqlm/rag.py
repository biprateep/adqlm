import numpy as np
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

class DocumentEmbedder:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.documents = []
        self.embeddings = None
        self.doc_sources = []

    def fetch_text_from_url(self, url):
        """Fetches text content from a URL."""
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

    def ingest_urls(self, urls):
        """Ingests content from a list of URLs and updates the index."""
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

    def retrieve(self, query, top_k=3):
        """Retrieves top_k documents relevant to the query."""
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
                'score': similarities[idx]
            })
        return results
