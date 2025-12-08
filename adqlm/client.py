from .rag import DocumentEmbedder
from .llm import LLMClient
from .datalab import DataLabClient
import os

class AdqlmAssistant:
    def __init__(self, google_api_key=None, datalab_token=None):
        self.rag = DocumentEmbedder()
        self.llm = LLMClient(api_key=google_api_key)
        self.datalab = DataLabClient(token=datalab_token)
        
        # Pre-load some documentation URLs (can be expanded)
        self.default_docs = [
            "https://datalab.noirlab.edu/docs/manual/UsingAstroDataLab/DataAccessInterfaces/CatalogDataAccessTAPSCS/CatalogDataAccessTAPSCS.html",
            "https://datalab.noirlab.edu/docs/manual/UsingAstroDataLab/WebPortal/Overview/Overview.html",
            # Add more relevant URLs
        ]
        
    def ingest_docs(self, urls=None):
        """Loads documentation into memory."""
        targets = urls if urls else self.default_docs
        print(f"Ingesting documentation from {len(targets)} sources...")
        self.rag.ingest_urls(targets)
        print("Ingestion complete.")

    def process_query(self, user_query):
        """
        Full pipeline: Retrieve -> Generate SQL -> Execute -> Explain
        """
        # 1. Retrieve Context
        context_docs = self.rag.retrieve(user_query)
        
        # 2. Generate SQL
        sql_query = self.llm.generate_sql(user_query, context_docs)
        if sql_query.startswith("ERROR"):
            return {
                "sql": None,
                "data": None,
                "explanation": "Could not generate a valid query based on available documentation."
            }
            
        # 3. Execute SQL
        # Note: Depending on query size, this might be large.
        # We might want to limit rows for the 'chat' interface.
        try:
            # Check if LIMIT is present, if not add it for safety in preview
            # This is a naive check.
            if "LIMIT" not in sql_query.upper():
                execution_sql = f"{sql_query} LIMIT 50"
            else:
                execution_sql = sql_query
                
            data = self.datalab.execute_query(execution_sql)
        except Exception as e:
            return {
                "sql": sql_query,
                "data": None,
                "explanation": f"Execution error: {str(e)}"
            }

        # 4. Explain
        # Convert data sample to string for LLM
        if hasattr(data, 'head'):
            data_sample = data.head().to_string()
        else:
            data_sample = str(data)[:1000] # Fallback
            
        explanation = self.llm.explain_result(user_query, sql_query, data_sample)
        
        return {
            "sql": sql_query,
            "data": data, # Return the dataframe/object
            "explanation": explanation
        }
