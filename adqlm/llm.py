import os
from google import genai
import json
from typing import List, Dict, Any, Optional

class LLMClient:
    """
    Manages interactions with the LLM (Gemini) for query refinement, generation, and explanation.
    """
    def __init__(self, api_key: Optional[str] = None, model_name: str = 'gemini-2.5-flash'):
        """
        Initialize the LLM client.

        Args:
            api_key (str, optional): API key for Gemini. Defaults to environment variable.
            model_name (str, optional): Default model to use.
        """
        # Prefer GEMINI_API_KEY, fallback to GOOGLE_API_KEY
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY (or GOOGLE_API_KEY) is not set and not provided.")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name
        self.few_shot_examples = self._load_few_shot_examples()

    def route_query(self, user_query: str, services: Dict[str, Any], model_name: Optional[str] = None) -> str:
        """
        Uses the LLM to route the query to the best available service.

        Args:
            user_query (str): The refined user query.
            services (Dict[str, AstronomicalDataService]): A dictionary of registered services.
            model_name (str, optional): Override model.

        Returns:
            str: The key of the selected service.
        """
        service_descriptions = "\n".join([f"- **{key}** ({svc.get_name()}): {svc.get_description()}" for key, svc in services.items()])

        prompt = f"""
You are an intelligent router for an astronomical data assistant. Your job is to select the BEST data service to answer the user's query.

Available Services:
{service_descriptions}

User Query: "{user_query}"

Instructions:
1. Read the user's query and the descriptions of the available services.
2. Decide which service is best equipped to handle the query based on the data sets they provide and query capabilities.
3. Return ONLY the key of the selected service (e.g., 'noirlab', 'astroquery'). Do not return any other text or explanation. If none seem appropriate, default to the first one.

Service Key:
"""
        model_to_use = model_name if model_name else self.model_name
        try:
            response = self.client.models.generate_content(
                model=model_to_use,
                contents=prompt
            )
            selected_key = response.text.strip().lower()
            if selected_key in services:
                 return selected_key
            else:
                 # Fallback to the first available service if the LLM hallucinated
                 return list(services.keys())[0]
        except Exception as e:
            print(f"Routing error: {e}")
            return list(services.keys())[0] # Fallback

    def _load_few_shot_examples(self) -> str:
        """Loads few-shot examples from local JSON file."""
        try:
            # Assuming file is in the same directory as this module
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, 'few_shot_examples.json')
            with open(file_path, 'r') as f:
                data = json.load(f)
            return "\n\n".join([f"Q: \"{item['question']}\"\nA: {item['sql']}" for item in data])
        except Exception as e:
            print(f"Warning: Could not load few-shot examples: {e}")
            return ""

    def refine_query(self, user_query: str, model_name: Optional[str] = None) -> str:
        """
        Refines the user query to correct spelling and make it clearer for RAG/SQL generation.

        Args:
            user_query (str): The raw input from the user.
            model_name (str, optional): Override model.

        Returns:
            str: Refined query text.
        """
        prompt = f"""
You are an expert astronomical assistant. Your task is to refine the user's natural language query to be clearer, correct any spelling mistakes, and disambiguate terms for a SQL generation system.

1. Correct astronomical terms (e.g. "gaaia" -> "gaia", "radiel" -> "radial").
2. Ensure specific values (RA, Dec, radius) are preserved exactly.
3. Make the intent of the query explicit (e.g. "count stars" -> "Count the number of sources").
4. If the query is completely nonsensical or unrelated to astronomy/data, return "ERROR: Irrelevant query."

User Query: "{user_query}"

Refined Query:
"""
        model_to_use = model_name if model_name else self.model_name
        try:
            response = self.client.models.generate_content(
                model=model_to_use,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return user_query # Fallback

    def generate_query(self, user_query: str, context_docs: List[Dict[str, Any]], model_name: Optional[str] = None) -> str:
        """
        Generates SQL query based on user query and retrieved context.

        Args:
            user_query (str): The refined user query.
            context_docs (List[Dict]): List of retrieved context documents.
            model_name (str, optional): Override model.

        Returns:
            str: Generated SQL query.
        """
        context_text = "\n\n".join([f"Source: {doc['source']}\nContent: {doc['text']}" for doc in context_docs])
        
        prompt = f"""
You are an expert query assistant for astronomical databases.
Your goal is to convert a natural language query into a valid query (e.g. ADQL/SQL) for the selected service.

Context Information from Documentation:
{context_text}

Few-Shot Examples:
{self.few_shot_examples}

User Query: {user_query}

Instructions:
1. Use the context provided to identify the correct table names, columns, and query syntax.
2. If querying NOIRLab or a standard TAP service, the SQL dialect is ADQL (Astronomical Data Query Language).
3. Use Q3C functions (q3c_radial_query, q3c_join, etc.) for spatial queries when using NOIRLab/PostgreSQL based services.
4. Return ONLY the query string. No markdown, no corrections.
5. **Anti-Hallucination**: If the context does not contain enough information (missing table names, unknown columns) to form a valid query with high confidence, you MUST return "ERROR: Insufficient context to generate query." Do not guess table names unless it's a standard table (like standard tap_schema).

Query:
"""
        # Use provided model_name or fallback to default
        model_to_use = model_name if model_name else self.model_name
        
        response = self.client.models.generate_content(
            model=model_to_use,
            contents=prompt
        )
        return response.text.strip()

    def explain_result(self, user_query: str, sql_query: str, data_sample: Any, model_name: Optional[str] = None) -> str:
        """
        Explains the result of the query execution to the user.

        Args:
            user_query (str): Original user query.
            sql_query (str): Executed SQL.
            data_sample (Any): Sample data (list of dicts or dataframe).
            model_name (str, optional): Override model.

        Returns:
            str: Explanation text.
        """
        prompt = f"""
The user asked: "{user_query}"
We executed the SQL: "{sql_query}"
The result (first few rows) is:
{data_sample}

Please provide a concise summary of what this data represents in response to the user's question.
"""
        model_to_use = model_name if model_name else self.model_name
        
        response = self.client.models.generate_content(
            model=model_to_use,
            contents=prompt
        )
        return response.text.strip()
