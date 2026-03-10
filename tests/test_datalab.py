import sys
from unittest.mock import MagicMock, patch

# In this specific environment, pandas, numpy, and dl are not installed.
# To test the logic in DataLabClient without installing heavy dependencies,
# we use a targeted mocking approach for these modules.
mock_qc = MagicMock()
mock_dl = MagicMock(queryClient=mock_qc)
mock_pd = MagicMock()
mock_np = MagicMock()

# Patch sys.modules to mock external dependencies
with patch.dict('sys.modules', {
    'dl': mock_dl,
    'pandas': mock_pd,
    'numpy': mock_np,
    'google': MagicMock(),
    'google.genai': MagicMock(),
    'bs4': MagicMock(),
    'requests': MagicMock()
}):
    import unittest
    # We use a context manager to ensure the environment is correct for the import
    from adqlm.datalab import NOIRLabService as DataLabClient

    class TestDataLabClient(unittest.TestCase):
        def setUp(self):
            # Reset mocks before each test
            mock_qc.reset_mock(return_value=True, side_effect=True)
            mock_qc.query.side_effect = None
            mock_qc.schema.side_effect = None

        def test_init_with_token(self):
            token = "test-token"
            # Ensure the module uses our mock_qc
            with patch('adqlm.datalab.qc', mock_qc):
                client = DataLabClient(token=token)
                mock_qc.set_auth_token.assert_called_once_with(token)

        def test_init_without_token(self):
            with patch('adqlm.datalab.qc', mock_qc):
                client = DataLabClient(token=None)
                mock_qc.set_auth_token.assert_not_called()

        def test_execute_query_markdown_cleaning(self):
            with patch('adqlm.datalab.qc', mock_qc):
                client = DataLabClient()
                sql_with_markdown = "```sql\nSELECT * FROM table\n```"
                client.execute_query(sql_with_markdown)
                mock_qc.query.assert_called_once_with("SELECT * FROM table", fmt='pandas')

        def test_execute_query_success(self):
            with patch('adqlm.datalab.qc', mock_qc):
                client = DataLabClient()
                mock_qc.query.return_value = "dummy_dataframe"
                result = client.execute_query("SELECT * FROM table", fmt='pandas')
                mock_qc.query.assert_called_once_with("SELECT * FROM table", fmt='pandas')
                self.assertEqual(result, "dummy_dataframe")

        def test_execute_query_exception(self):
            with patch('adqlm.datalab.qc', mock_qc):
                client = DataLabClient()
                mock_qc.query.side_effect = Exception("Database error")
                result = client.execute_query("SELECT * FROM table")
                self.assertIsNone(result)

        def test_get_table_schema_success(self):
            with patch('adqlm.datalab.qc', mock_qc):
                client = DataLabClient()
                expected_schema = {"table": "columns"}
                mock_qc.schema.return_value = expected_schema
                result = client.get_table_schema("ls_dr9.tractor")
                mock_qc.schema.assert_called_once_with("ls_dr9.tractor")
                self.assertEqual(result, expected_schema)

        def test_get_table_schema_exception(self):
            with patch('adqlm.datalab.qc', mock_qc):
                client = DataLabClient()
                mock_qc.schema.side_effect = Exception("Schema error")
                result = client.get_table_schema("invalid_table")
                self.assertIsNone(result)

    if __name__ == '__main__':
        unittest.main()
