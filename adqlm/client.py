from .rag import DocumentEmbedder
from .llm import LLMClient
from .datalab import DataLabClient
import os
import uuid
from typing import Optional, List, Dict, Any

class AdqlmAssistant:
    """
    Main controller for the ADQLM assistant.
    
    Coordinating the RAG system, LLM client, and DataLab execution interactively.
    """
    def __init__(self, google_api_key: Optional[str] = None, datalab_token: Optional[str] = None):
        """
        Initialize the assistant components.

        Args:
            google_api_key (str, optional): API key for Gemini. 
            datalab_token (str, optional): Token for Data Lab access.
        """
        self.rag = DocumentEmbedder()
        self.llm = LLMClient(api_key=google_api_key)
        self.datalab = DataLabClient(token=datalab_token)
        
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
        
        # 2. Retrieve Context (using refined query)
        context_docs = self.rag.retrieve(refined_query)
        
        # 3. Generate SQL (using refined query and context)
        try:
            sql_query = self.llm.generate_query(refined_query, context_docs, model_name=model_name)
        except Exception as e:
            return {"error": f"Error generating SQL: {str(e)}"}

        if sql_query.startswith("ERROR"):
             return {"error": sql_query}
             
        return {"sql": sql_query}

    def execute_and_save(self, sql_query: str, output_dir: str = "web/static/downloads") -> Dict[str, Any]:
        """
        Phase 2: Execute SQL, save to CSV, and return preview.

        Args:
            sql_query (str): valid ADQL query.
            output_dir (str, optional): Directory to save result CSVs.

        Returns:
             Dict[str, Any]: execution result including status, preview data, and csv url.
        """
        
        # Smart LIMIT check
        # ADQL supports 'TOP' (e.g. SELECT TOP 100 ...) and 'LIMIT' (VSQL style).
        # We shouldn't add LIMIT if either exists.
        upper_sql = sql_query.upper()
        if "LIMIT " not in upper_sql and "TOP " not in upper_sql:
            # Assuming if no limit/top, we safeguard with 100 for the preview/run 
            # OR we trust the user. The user said "file download starts automatically".
            # If they want a download, maybe they want ALL data?
            # But for safety/speed, let's keep a sane default if looks unlimited,
            # or maybe just run it. The user has explicitly approved it.
            # Let's trust the approved SQL but maybe warn? 
            # Actually, let's stick to the previous safety but smarter:
            # Only append LIMIT if strictly necessary for a *preview*, 
            # but here we are doing a "download". 
            # Use original SQL for full execution.
            execution_sql = sql_query
        else:
            execution_sql = sql_query

        try:
            # Execute
            print(f"Executing: {execution_sql}")
            df = self.datalab.execute_query(execution_sql)
            
            # Save to CSV
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            # Generate unique filename
            filename = f"results_{uuid.uuid4().hex[:8]}.csv"
            filepath = os.path.join(output_dir, filename)
            
            # We need to handle if df is None or not a dataframe (e.g. string error)
            # execute_query usually returns DataFrame
            if df is not None:
                df.to_csv(filepath, index=False)
                
                # Preview
                data_preview = df.head(10).to_dict(orient='records')
                row_count = len(df)
            else:
                return {"error": "No data returned."}

            return {
                "success": True,
                "csv_url": f"/static/downloads/{filename}",
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
        exec_result = self.execute_and_save(sql)
        
        if "error" in exec_result:
             return {"explanation": exec_result["error"], "sql": sql, "data": None}
             
        return {
            "sql": sql,
            "data": exec_result["preview"],
            "explanation": f"Executed successfully. {exec_result['rows']} rows retrieved."
        }
