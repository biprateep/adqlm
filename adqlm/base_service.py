from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
import pandas as pd

class AstronomicalDataService(ABC):
    """
    Abstract base class for all astronomical data services.
    """

    @abstractmethod
    def get_name(self) -> str:
        """Returns the name of the service."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Returns a description of what data this service provides and what it should be used for."""
        pass

    @abstractmethod
    def execute_query(self, query: str, **kwargs) -> Union[pd.DataFrame, Any, None]:
        """
        Executes a query against the service.

        Args:
            query (str): The query string (e.g., ADQL, SQL, or specific API parameters).

        Returns:
            The execution result, ideally as a pandas DataFrame or standard format, or None on error.
        """
        pass
