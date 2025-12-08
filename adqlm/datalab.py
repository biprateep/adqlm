from dl import queryClient as qc
import pandas as pd

class DataLabClient:
    def __init__(self, token=None):
        self.token = token
        # If token is provided, we might want to set it in the client
        # qc.set_svc_url(...) or auth logic if needed. 
        # For public data, no token is often needed or anonymous access is used.
        if token:
            qc.set_auth_token(token)

    def execute_query(self, sql, fmt='pandas'):
        """
        Executes an ADQL query against NOIRLab Data Lab.
        """
        try:
            # removing any potential markdown code blocks if the LLM leaked them
            sql = sql.replace('```sql', '').replace('```', '').strip()
            
            # Using queryClient to execute
            # We default to pandas for easy handling
            result = qc.query(sql, fmt=fmt)
            return result
        except Exception as e:
            return f"Error executing query: {str(e)}"

    def get_table_schema(self, table_name):
        """
        Helper to fetch schema for a table (could be used for RAG context too).
        """
        try:
            return qc.schema(table_name)
        except Exception:
            return None
