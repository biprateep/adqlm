import os
from google import genai

class LLMClient:
    def __init__(self, api_key=None, model_name='gemini-2.5-flash'):
        # Prefer GEMINI_API_KEY, fallback to GOOGLE_API_KEY
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY (or GOOGLE_API_KEY) is not set and not provided.")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name

    def generate_sql(self, user_query, context_docs):
        """
        Generates SQL query based on user query and retrieved context.
        """
        context_text = "\n\n".join([f"Source: {doc['source']}\nContent: {doc['text']}" for doc in context_docs])
        
        prompt = f"""
You are an expert SQL assistant for the NOIRLab Astro Data Lab.
Your goal is to convert a natural language query into a valid SQL query compatible with the Data Lab TAP service.

Context Information from Documentation:
{context_text}

User Query: {user_query}

Instructions:
1. Use the context provided to identify the correct table names and columns.
2. The SQL dialect is ADQL (Astronomical Data Query Language), which is similar to SQL.
3. Return ONLY the SQL query. Do not wrap it in markdown or code blocks. Do not add explanations.
4. If you cannot generate a valid query based on the context, return "ERROR: Insufficient context."

SQL Query:
"""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return response.text.strip()

    def explain_result(self, user_query, sql_query, data_sample):
        """
        Explains the result of the query execution to the user.
        """
        prompt = f"""
The user asked: "{user_query}"
We executed the SQL: "{sql_query}"
The result (first few rows) is:
{data_sample}

Please provide a concise summary of what this data represents in response to the user's question.
"""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return response.text.strip()
