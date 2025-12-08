import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from adqlm.client import AdqlmAssistant

class TestAdqlmAssistant(unittest.TestCase):
    def setUp(self):
        # Mock Google API key
        self.api_key = "fake_key"
        self.assistant = AdqlmAssistant(google_api_key=self.api_key)

    @patch('adqlm.rag.DocumentEmbedder.retrieve')
    @patch('adqlm.llm.LLMClient.generate_sql')
    @patch('adqlm.datalab.DataLabClient.execute_query')
    @patch('adqlm.llm.LLMClient.explain_result')
    def test_process_query_success(self, mock_explain, mock_execute, mock_generate_sql, mock_retrieve):
        # Setup mocks
        mock_retrieve.return_value = [{'text': 'context', 'source': 'url'}]
        mock_generate_sql.return_value = "SELECT * FROM stars LIMIT 10"
        
        # Mocking a DataFrame return
        mock_df = pd.DataFrame({'id': [1, 2], 'mag': [10.5, 11.2]})
        mock_execute.return_value = mock_df
        
        mock_explain.return_value = "Here are the stars you requested."

        # Execute
        result = self.assistant.process_query("Find me some stars")

        # Verify
        self.assertEqual(result['sql'], "SELECT * FROM stars LIMIT 10")
        self.assertTrue(result['data'].equals(mock_df))
        self.assertEqual(result['explanation'], "Here are the stars you requested.")
        
        mock_retrieve.assert_called_once()
        mock_generate_sql.assert_called_once()
        mock_execute.assert_called_once()
        mock_explain.assert_called_once()

    @patch('adqlm.rag.DocumentEmbedder.retrieve')
    @patch('adqlm.llm.LLMClient.generate_sql')
    def test_process_query_sql_generation_failure(self, mock_generate_sql, mock_retrieve):
        # Setup mocks
        mock_retrieve.return_value = []
        mock_generate_sql.return_value = "ERROR: Insufficient context."

        # Execute
        result = self.assistant.process_query("Unknown query")

        # Verify
        self.assertIsNone(result['sql'])
        self.assertIsNone(result['data'])
        self.assertIn("Could not generate", result['explanation'])

if __name__ == '__main__':
    unittest.main()
