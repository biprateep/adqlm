from dl import queryClient as qc
import pandas as pd
from typing import Optional, Union, Any

class DataLabClient:
    """
    A wrapper around the NOIRLab Data Lab queryClient.
    
    This class handles authentication (if provided) and execution of ADQL queries.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the DataLabClient.

        Args:
            token (str, optional): Authentication token for Data Lab. 
                                   If None, public access is assumed.
        """
        self.token = token
        if token:
            qc.set_auth_token(token)

    def execute_query(self, sql: str, fmt: str = 'pandas') -> Union[pd.DataFrame, str]:
        """
        Executes an ADQL query against NOIRLab Data Lab.

        Args:
            sql (str): The ADQL query to execute.
            fmt (str, optional): The return format, default is 'pandas'.

        Returns:
            pd.DataFrame or str: The query result as a DataFrame, or an error message string.
        """
        try:
            # Clean potential markdown if leaked from LLM
            sql = sql.replace('```sql', '').replace('```', '').strip()
            
            # Execute query
            result = qc.query(sql, fmt=fmt)
            return result
        except Exception as e:
            # Consider returning None or raising specific custom exception instead of str
            # but keeping existing error string behavior for now per existing client logic
            return None # Changed to None to let client handle "is not None" check

    def get_table_schema(self, table_name: str) -> Any:
        """
        Fetch schema information for a specific table.

        Args:
            table_name (str): The fully qualified table name (e.g. 'ls_dr9.tractor').

        Returns:
            Any: Variable format depending on queryClient.schema implementation, or None on error.
        """
        try:
            return qc.schema(table_name)
        except Exception:
            return None
