import unittest
import os
from unittest.mock import patch, MagicMock
from adqlm.client import ADQLMAssistant
import pandas as pd

class TestQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @unittest.skipIf(not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"), "Skipping LLM tests because API key is not set.")
    def test_desi_dr1_quasars(self):
        """
        Test the specific user query: "give me the top 10 highest redshift quasars in DESI DR1 catalog"
        """
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        assistant = ADQLMAssistant(google_api_key=api_key)

        query = "give me the top 10 highest redshift quasars in DESI DR1 catalog"
        result = assistant.generate_query(query, model_name="gemini-2.5-flash")

        self.assertNotIn("error", result, f"Query generation failed: {result.get('error')}")
        self.assertIn("sql", result)

        sql = result["sql"].lower()
        self.assertIn("desi_dr1", sql, "SQL should query DESI DR1")
        self.assertIn("z", sql, "SQL should query redshift (usually 'z')")
        self.assertIn("desc", sql, "SQL should sort descending for 'highest'")
        self.assertIn("limit 10", sql, "SQL should limit to 10")

        # Test execution - actually hitting the NOIRLab service to verify data fetching
        exec_result = assistant.execute_and_preview(result["sql"], result.get("service", "noirlab"))
        self.assertNotIn("error", exec_result, f"Execution failed: {exec_result.get('error')} for SQL: {result['sql']}")
        self.assertTrue(exec_result.get("success"), "Execution should be successful")
        self.assertEqual(len(exec_result.get("preview", [])), 10, "Should return exactly 10 rows")

if __name__ == '__main__':
    unittest.main()
