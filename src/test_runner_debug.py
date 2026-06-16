import os
import sys
import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.cli import run

def main():
    # Mock App Store reviews
    app_store_reviews = [
        {
            "id": "ios_1",
            "author": "User One",
            "title": "Need help",
            "text": "The app is freezing at market open 9:15 AM IST. Lag is too high.",
            "rating": 1,
            "date": "2026-06-16T12:00:00Z",
            "platform": "ios"
        }
    ]
    
    # Mock Play Store reviews
    play_store_reviews = [
        {
            "id": "gp_1",
            "author": "User Two",
            "title": "",
            "text": "Worst support. Chatbot does not resolve the ticket at all.",
            "rating": 2,
            "date": "2026-06-16T12:00:00Z",
            "platform": "android"
        }
    ]
    
    # Mock report returned by GeminiSummarizer
    mock_report = {
        "themes": [
            {
                "theme_name": "App Stability & Market Open Performance",
                "summary": "Users report that the app suffers from lag, freezes, and session timeouts during peak market open hours around 9:15 AM IST.",
                "quotes": ["The app is freezing at market open 9:15 AM IST. Lag is too high."],
                "action_ideas": [
                    "Scale infrastructure capacity during peak trading open windows (9:00 AM - 9:30 AM IST).",
                    "Optimize session validation timeouts to prevent users from being locked out during active positions."
                ]
            }
        ]
    }

    # Setup mock HTTP responses for urllib.request.urlopen
    mock_doc_resp = MagicMock()
    mock_doc_resp.__enter__.return_value = mock_doc_resp
    mock_doc_resp.read.return_value = json.dumps({
        "status": "success",
        "result": {
            "document_url": "https://docs.google.com/document/d/mock_doc_id/edit#heading=pulse-anchor-2026-W24",
            "header_anchor_id": "pulse-anchor-2026-W24"
        }
    }).encode('utf-8')
    
    mock_gmail_resp = MagicMock()
    mock_gmail_resp.__enter__.return_value = mock_gmail_resp
    mock_gmail_resp.read.return_value = json.dumps({
        "status": "success",
        "result": {
            "message_id": "gmail_mock_12345"
        }
    }).encode('utf-8')

    runner = CliRunner()
    
    with patch('urllib.request.urlopen') as mock_urlopen, \
         patch('src.cli.AppStoreIngestor.fetch_reviews', return_value=app_store_reviews), \
         patch('src.cli.PlayStoreScraper.scrape_reviews', return_value=play_store_reviews), \
         patch('src.cli.GeminiSummarizer.generate_report', return_value=mock_report), \
         patch('src.cli.check_already_delivered', return_value=False), \
         patch.dict('os.environ', {
             'GOOGLE_DOC_ID': 'test_doc_id',
             'GOOGLE_MCP_SERVER_URL': 'https://my-mcp-server-production-1f3f.up.railway.app'
         }):
        
        mock_urlopen.side_effect = [mock_doc_resp, mock_gmail_resp]
        
        result = runner.invoke(run, [
            '--product', 'groww',
            '--window-weeks', '12',
            '--recipients', 'test@groww-analytics.internal'
        ])
        
        # Write results to a file so we can view it
        with open("logs/test_run_output.txt", "w", encoding="utf-8") as f:
            f.write(f"Exit Code: {result.exit_code}\n")
            if result.exception:
                f.write(f"Exception: {str(result.exception)}\n")
            f.write("Output:\n")
            f.write(result.output)
            
    print("Debug script completed. Output written to logs/test_run_output.txt")

if __name__ == "__main__":
    main()
