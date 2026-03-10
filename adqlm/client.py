from .rag import DocumentEmbedder
from .llm import LLMClient
from .datalab import NOIRLabService
from .base_service import AstronomicalDataService
import os
import uuid
from typing import Optional, List, Dict, Any

class ADQLMAssistant:
    """
    Main controller for the ADQLM assistant.
    
    Coordinating the RAG system, LLM client, and dynamic execution across services interactively.
    """
    def __init__(self, google_api_key: Optional[str] = None, datalab_token: Optional[str] = None):
        """
        Initialize the assistant components.

        Args:
            google_api_key (str, optional): API key for Gemini. 
            datalab_token (str, optional): Token for Data Lab access.
        """
        self.rag = DocumentEmbedder(api_key=google_api_key)
        self.llm = LLMClient(api_key=google_api_key)

        # Registry of available data services
        self.services: Dict[str, AstronomicalDataService] = {
            "noirlab": NOIRLabService(token=datalab_token),
            # Add future services here, e.g., "astroquery": AstroqueryService()
        }
        
        # Pre-load some documentation URLs (can be expanded)
        self.default_docs = [
            "https://datalab.noirlab.edu/docs/manual/UsingAstroDataLab/DataAccessInterfaces/CatalogDataAccessTAPSCS/CatalogDataAccessTAPSCS.html",
            "https://datalab.noirlab.edu/docs/manual/UsingAstroDataLab/WebPortal/Overview/Overview.html",
            # Add more relevant URLs
        ]
        
    def ingest_docs(self, urls: Optional[List[str]] = None):
        """
        Loads documentation into memory from local JSON DBs and/or URLs.

        Args:
            urls (List[str], optional): Additional URLs to scrape.
        """
        # Load local schema DB if available
        schema_path = "schema_docs.json"
        if os.path.exists(schema_path):
            print(f"Loading local schema database from {schema_path}...")
            self.rag.load_json_docs(schema_path)
            
        # Load local reference DB (Q3C, SQL, etc.)
        ref_path = "reference_docs.json"
        if os.path.exists(ref_path):
            print(f"Loading local reference database from {ref_path}...")
            self.rag.load_json_docs(ref_path)
            
        targets = urls if urls else self.default_docs
        print(f"Ingesting documentation from {len(targets)} sources...")
        self.rag.ingest_urls(targets)
        print("Ingestion complete.")

    def generate_query(self, user_query: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Phase 1: Generate SQL from user query.

        Args:
            user_query (str): The user's request.
            model_name (str, optional): Override LLM model.

        Returns:
            Dict[str, Any]: Result dictionary with 'sql' or 'error'.
        """
        # 1. Refine Query (Spelling, Intent)
        print("Refining user query...")
        refined_query = self.llm.refine_query(user_query, model_name=model_name)
        
        if refined_query.startswith("ERROR"):
             return {"error": f"Query Error: {refined_query}"}
             
        print(f"Refined Query: {refined_query}")
        
        # 2. Route Query to appropriate service
        print("Routing query to best service...")
        selected_service_key = self.llm.route_query(refined_query, self.services, model_name=model_name)
        print(f"Selected Service: {selected_service_key}")

        # 3. Retrieve Context (using refined query)
        # Ideally we'd filter RAG context based on the selected service, but retrieving generally is okay for now.
        context_docs = self.rag.retrieve(refined_query)
        
        # 4. Generate Query (using refined query and context)
        try:
            generated_query = self.llm.generate_query(refined_query, context_docs, model_name=model_name)
        except Exception as e:
            return {"error": f"Error generating query: {str(e)}"}

        if generated_query.startswith("ERROR"):
             return {"error": generated_query}
             
        return {
            "sql": generated_query,  # Keeping "sql" key for backward compatibility in frontend
            "service": selected_service_key
        }

    def execute_and_preview(self, sql_query: str, service_key: str = "noirlab") -> Dict[str, Any]:
        """
        Phase 2: Execute SQL and return preview.
        
        Args:
            sql_query (str): valid ADQL query.

        Returns:
             Dict[str, Any]: execution result including status and preview data.
        """
        
        execution_sql = sql_query
        # Smart LIMIT could go here but skipping for now to rely on user/predefined logic


        if service_key not in self.services:
            return {"error": f"Unknown service: {service_key}"}

        service = self.services[service_key]

        try:
            # Execute
            print(f"Executing for preview on {service.get_name()}: {execution_sql}")
            df = service.execute_query(execution_sql)
            
            # We need to handle if df is None or not a dataframe
            # Assuming services return pandas DataFrames for standard tabular preview
            if df is not None and hasattr(df, 'head'):
                row_count = len(df)
                
                # Preview
                import numpy as np
                df_clean = df.replace({np.nan: None})
                # Limit preview to 10 rows
                data_preview = df_clean.head(10).to_dict(orient='records')
            else:
                return {"error": "No data returned."}

            return {
                "success": True,
                "preview": data_preview,
                "rows": row_count
            }
            
        except Exception as e:
            return {"error": f"Execution error: {str(e)}"}

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility if needed.
        Combines generation and execution (beware: auto-executes!).
        """
        gen_result = self.generate_query(user_query)
        if "error" in gen_result:
            return {"explanation": gen_result["error"], "sql": None, "data": None}
            
        sql = gen_result["sql"]
        service_key = gen_result.get("service", "noirlab")
        exec_result = self.execute_and_preview(sql, service_key=service_key)
        
        if "error" in exec_result:
             return {"explanation": exec_result["error"], "sql": sql, "data": None, "service": service_key}
             
        return {
            "sql": sql,
            "data": exec_result["preview"],
            "service": service_key,
            "explanation": f"Executed successfully via {self.services[service_key].get_name()}. {exec_result['rows']} rows retrieved."
        }
