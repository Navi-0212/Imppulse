import unittest
from unittest.mock import patch, MagicMock

# We use standard unittest to verify server logic.
# Mock imports of tools so we don't hit the real google APIs or OAuth files.
import sys

# Mock modules that might not be installed in the current environment yet (e.g. googleapiclient)
sys.modules['googleapiclient'] = MagicMock()
sys.modules['googleapiclient.discovery'] = MagicMock()
sys.modules['google_auth_oauthlib'] = MagicMock()
sys.modules['google_auth_oauthlib.flow'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.auth'] = MagicMock()
sys.modules['google.auth.transport'] = MagicMock()
sys.modules['google.auth.transport.requests'] = MagicMock()
sys.modules['google.oauth2'] = MagicMock()
sys.modules['google.oauth2.credentials'] = MagicMock()

try:
    from fastapi.testclient import TestClient
    from server import app
    HAS_TESTCLIENT = True
except ImportError:
    HAS_TESTCLIENT = False

class TestMCPServer(unittest.TestCase):
    def setUp(self):
        if not HAS_TESTCLIENT:
            self.skipTest("fastapi or testclient not installed.")
        self.client = TestClient(app)

    @patch('server.ask_user_approval')
    @patch('server.append_to_doc')
    def test_append_to_doc_approved(self, mock_append, mock_approve):
        mock_approve.return_value = True
        mock_append.return_value = {"updated": True}
        
        response = self.client.post("/append_to_doc", json={
            "doc_id": "test_doc_123",
            "content": "some content"
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "result": {"updated": True}})
        mock_approve.assert_called_once()
        mock_append.assert_called_once_with("test_doc_123", "some content")

    @patch('server.ask_user_approval')
    def test_append_to_doc_rejected(self, mock_approve):
        mock_approve.return_value = False
        
        response = self.client.post("/append_to_doc", json={
            "doc_id": "test_doc_123",
            "content": "some content"
        })
        
        self.assertEqual(response.status_code, 403)
        self.assertIn("rejected", response.json()["detail"])

    @patch('server.ask_user_approval')
    @patch('server.create_email_draft')
    def test_create_email_draft_approved(self, mock_draft, mock_approve):
        mock_approve.return_value = True
        mock_draft.return_value = {"draft_id": "draft_abc"}
        
        response = self.client.post("/create_email_draft", json={
            "to": "test@example.com",
            "subject": "Hello",
            "body": "World"
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "result": {"draft_id": "draft_abc"}})
        mock_approve.assert_called_once()
        mock_draft.assert_called_once_with("test@example.com", "Hello", "World")

if __name__ == '__main__':
    unittest.main()
