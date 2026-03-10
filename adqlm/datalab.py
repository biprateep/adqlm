from dl import queryClient as qc
import pandas as pd
from typing import Optional, Union, Any
from .base_service import AstronomicalDataService

class NOIRLabService(AstronomicalDataService):
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

    def get_name(self) -> str:
        return "NOIRLab Data Lab"

    def get_description(self) -> str:
        return (
            "Use this service to query NOIRLab datasets such as Gaia, DES (Dark Energy Survey), "
            "LS (Legacy Surveys), NSC (NOIRLab Source Catalog), and others using ADQL (Astronomical Data Query Language). "
            "Ideal for spatial queries, table joins, and accessing large astronomical catalogs."
        )

    def execute_query(self, query: str, fmt: str = 'pandas', **kwargs) -> Union[pd.DataFrame, Any, None]:
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
            sql = query.replace('```sql', '').replace('```', '').strip()
            
            # Execute query
            result = qc.query(sql, fmt=fmt, **kwargs)
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
