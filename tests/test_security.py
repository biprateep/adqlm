import unittest
import os
import sys
from unittest.mock import MagicMock, patch

class TestSecurityConfig(unittest.TestCase):
    def setUp(self):
        # Save original environment
        self.original_env = os.environ.copy()
        if "SECRET_KEY" in os.environ:
            del os.environ["SECRET_KEY"]

        # Mock Flask and AdqlmAssistant to avoid missing dependency errors
        self.flask_patcher = patch.dict('sys.modules', {
            'flask': MagicMock(),
            'adqlm.client': MagicMock(),
            'pandas': MagicMock(),
            'numpy': MagicMock()
        })
        self.flask_patcher.start()

    def tearDown(self):
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
        self.flask_patcher.stop()

    def test_missing_secret_key_production(self):
        # We need to simulate the import of web.app
        # Since it's already in sys.modules (potentially), we might need to reload it or use a different approach
        if 'web.app' in sys.modules:
            del sys.modules['web.app']

        with self.assertRaises(RuntimeError) as cm:
            import web.app
        self.assertEqual(str(cm.exception), "SECRET_KEY environment variable is not set. Please set it for production.")

    def test_provided_secret_key(self):
        os.environ["SECRET_KEY"] = "test_secret_key"
        if 'web.app' in sys.modules:
            del sys.modules['web.app']

        import web.app
        self.assertEqual(web.app.app.secret_key, "test_secret_key")

if __name__ == "__main__":
    unittest.main()
