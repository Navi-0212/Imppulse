import pytest
import datetime
from src.ingestion.app_store import AppStoreIngestor
from src.ingestion.play_store import PlayStoreScraper
from src.ingestion.scrub import PIIScrubber
from src.analytics.cluster import ReviewClusterer
from src.analytics.validate import GroundedQuoteValidator
from src.ingestion.filter import ReviewFilter
from src.ingestion.normalize import normalize_text, normalize_review, normalize_reviews

def test_pii_scrubber():
    scrubber = PIIScrubber()
    
    # Test email scrubbing
    text_with_email = "Please contact me at developer-help@groww.in for details."
    assert "[EMAIL]" in scrubber.scrub_text(text_with_email)
    
    # Test phone number scrubbing
    text_with_phone = "My phone number is +91-98765-43210. Help me."
    assert "[PHONE]" in scrubber.scrub_text(text_with_phone)
    
    # Test long number (ID) scrubbing
    text_with_id = "My transaction ticket reference is 99887766. Please resolve."
    assert "[ID]" in scrubber.scrub_text(text_with_id)

def test_date_parser():
    scraper = PlayStoreScraper()
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # Relative date checks
    parsed_days = scraper.parse_play_date("3 days ago")
    assert (now - parsed_days).days >= 2
    
    parsed_weeks = scraper.parse_play_date("2 weeks ago")
    assert (now - parsed_weeks).days >= 13
    
    # Absolute date check
    parsed_abs = scraper.parse_play_date("May 20, 2026")
    assert parsed_abs.year == 2026
    assert parsed_abs.month == 5
    assert parsed_abs.day == 20

def test_clustering_fallback():
    clusterer = ReviewClusterer()
    
    mock_reviews = [
        {"text": "App is freezing at market open 9:15 AM IST. Lag is too high.", "rating": 1},
        {"text": "Lag is very bad. App keeps freezing.", "rating": 1},
        {"text": "Worst support. Chatbot does not resolve the ticket.", "rating": 2},
        {"text": "Support took days to reply. Bad customer service.", "rating": 1},
        {"text": "I love Groww app. Excellent UI and super easy mutual funds.", "rating": 5},
        {"text": "Nice user interface, works perfectly for stock trading.", "rating": 5}
    ]
    
    clusters = clusterer.cluster_reviews(mock_reviews, min_cluster_size=2)
    assert len(clusters) > 0
    
    # Check structure
    for cid, details in clusters.items():
        assert "cluster_id" in details
        assert "reviews" in details
        assert "centroid_review" in details
        assert len(details["reviews"]) > 0

def test_grounded_quote_validator():
    validator = GroundedQuoteValidator()
    
    raw_reviews = [
        {"text": "App is freezing at market open 9:15 AM IST. Lag is too high.", "rating": 1},
        {"text": "Worst support. Chatbot does not resolve the ticket.", "rating": 2}
    ]
    
    # Valid report (Quotes exist character-for-character)
    valid_report = {
        "themes": [
            {
                "theme_name": "Freezes",
                "quotes": ["App is freezing at market open 9:15 AM IST."],
                "summary": "App freezes during open."
            }
        ]
    }
    
    is_valid, failed = validator.validate_report(valid_report, raw_reviews)
    assert is_valid
    assert len(failed) == 0
    
    # Invalid report (Quote has a typo/is hallucinated)
    invalid_report = {
        "themes": [
            {
                "theme_name": "Freezes",
                "quotes": ["App is freezing at market open 9:15 AM."], # missing " IST"
                "summary": "App freezes during open."
            }
        ]
    }
    
    is_valid_fail, failed_fail = validator.validate_report(invalid_report, raw_reviews)
    assert not is_valid_fail
    assert "App is freezing at market open 9:15 AM." in failed_fail

def test_force_grounding():
    validator = GroundedQuoteValidator()
    
    raw_reviews = [
        {"text": "App is freezing at market open 9:15 AM IST. Lag is too high.", "rating": 1},
        {"text": "Worst support. Chatbot does not resolve the ticket.", "rating": 2}
    ]
    
    invalid_report = {
        "themes": [
            {
                "theme_name": "Freezes",
                "quotes": ["This quote is completely hallucinated by LLM!"],
                "summary": "App freezes during open."
            }
        ]
    }
    
    fixed_report = validator._force_ground_quotes(invalid_report, raw_reviews)
    is_valid, failed = validator.validate_report(fixed_report, raw_reviews)
    
    # Should force match to one of the raw reviews and pass
    assert is_valid
    assert len(failed) == 0
    assert fixed_report["themes"][0]["quotes"][0] in [r["text"] for r in raw_reviews]

def test_review_filter():
    review_filter = ReviewFilter(min_word_count=8)
    
    # Test 1: Under 8 words (7 words)
    assert not review_filter.should_keep("This app is really very bad support")
    # Test 2: Exactly 8 words
    assert review_filter.should_keep("This app is really very bad support service")
    # Test 3: Over 8 words
    assert review_filter.should_keep("I have been using this app for mutual funds and stock trading for two years now")
    
    # Test 4: Emojis
    assert not review_filter.should_keep("Excellent UI and super easy mutual funds invest 😊")
    assert not review_filter.should_keep("App freezes during market open hours 🚀 and timeouts")
    
    # Test 5: Non-English Script (Devanagari/Hindi)
    assert not review_filter.should_keep("यह ऐप बहुत अच्छा है और आसानी से निवेश हो जाता है") # Hindi characters
    assert review_filter.should_keep("Yeh app bohot accha hai aur aasaani se invest ho jata hai") # Hinglish (using Latin letters)
    
    # Test 6: Permitted characters (standard punctuation, smart quotes, accents)
    assert review_filter.should_keep("Excellent UI and super easy mutual funds invest! Works, doesn't crash.")
    assert review_filter.should_keep("This is a 'great' app—runs smoothly; highly recommended.")
    
    # Test 7: Bulk filter_reviews
    mock_reviews = [
        {"text": "Short text"}, # filtered (less than 8 words)
        {"text": "This app is really very bad support service"}, # kept (8 words)
        {"text": "This app is really very bad support service 😊"}, # filtered (emoji)
        {"text": "यह ऐप बहुत अच्छा है और आसानी से निवेश हो जाता है"}, # filtered (Hindi)
        {"text": "Yeh app bohot accha hai aur aasaani se invest ho jata hai"} # kept (Hinglish, 11 words, no emoji)
    ]
    filtered = review_filter.filter_reviews(mock_reviews)
    assert len(filtered) == 2
    assert filtered[0]["text"] == "This app is really very bad support service"
    assert filtered[1]["text"] == "Yeh app bohot accha hai aur aasaani se invest ho jata hai"

def test_review_normalization():
    # Test 1: HTML entity decoding
    html_text = "Groww&#39;s stock analysis is great &amp; simple."
    assert normalize_text(html_text) == "Groww's stock analysis is great & simple."
    
    # Test 2: Carriage returns and spaces collapsing
    cr_text = "First line.\r\nSecond line.   With many    spaces.\rThird line."
    expected_text = "First line.\nSecond line. With many spaces.\nThird line."
    assert normalize_text(cr_text) == expected_text
    
    # Test 3: Clamping rating
    mock_review_good = {"text": "Good", "rating": 10, "author": " Priya  "}
    normalized = normalize_review(mock_review_good)
    assert normalized["rating"] == 5
    assert normalized["author"] == "Priya"
    
    mock_review_bad = {"text": "Bad", "rating": -5, "author": "Amit\n"}
    normalized_bad = normalize_review(mock_review_bad)
    assert normalized_bad["rating"] == 1
    assert normalized_bad["author"] == "Amit"
    
    # Test 4: List normalization
    reviews_list = [
        {"text": "A &amp; B", "rating": 4},
        {"text": "C &amp; D", "rating": 7}
    ]
    normalized_list = normalize_reviews(reviews_list)
    assert normalized_list[0]["text"] == "A & B"
    assert normalized_list[1]["rating"] == 5

    # Test 5: Key mappings and scrubbing of non-standard keys
    gp_scraper_review = {
        "reviewId": "gp_112233",
        "userName": "Rohan Sharma",
        "userImage": "https://play-lh.googleusercontent.com/avatar",
        "content": "Excellent app for trading &amp; investing.",
        "score": 5,
        "thumbsUpCount": 14,
        "reviewCreatedVersion": "5.4.0",
        "at": "2026-06-11T12:00:00Z",
        "replyContent": "Thank you for the review!",
        "repliedAt": "2026-06-11T14:00:00Z"
    }
    normalized_gp = normalize_review(gp_scraper_review)
    
    # Check that keys are correctly mapped
    assert normalized_gp["id"] == "gp_112233"
    assert normalized_gp["author"] == "Rohan Sharma"
    assert normalized_gp["text"] == "Excellent app for trading & investing."
    assert normalized_gp["rating"] == 5
    assert normalized_gp["date"] == "2026-06-11T12:00:00Z"
    assert normalized_gp["platform"] == "android"
    
    # Check that non-standard/unwanted keys are deleted/not present in output
    unwanted_keys = ["reviewId", "userName", "userImage", "reviewCreatedVersion", "at", "replyContent", "repliedAt", "thumbsUpCount"]
    for key in unwanted_keys:
        assert key not in normalized_gp


def test_token_tracker(tmp_path):
    from src.analytics.summarize import TokenTracker
    
    # Use a temporary file for testing
    temp_log = tmp_path / "token_usage_test.json"
    tracker = TokenTracker(limit_per_day=5000, log_path=str(temp_log))
    
    # Initial usage should be 0
    assert tracker.get_today_usage() == 0
    assert tracker.check_limit(2000) is True
    
    # Add some usage
    tracker.add_usage(3000)
    assert tracker.get_today_usage() == 3000
    
    # Check limit when close
    assert tracker.check_limit(1500) is True  # 3000 + 1500 = 4500 <= 5000
    assert tracker.check_limit(2500) is False # 3000 + 2500 = 5500 > 5000
    
    # Add more usage to exceed
    tracker.add_usage(2500)
    assert tracker.get_today_usage() == 5500
    assert tracker.check_limit(100) is False


def test_idempotency_and_logging(tmp_path):
    from src.cli import check_already_delivered, record_delivery
    import os
    
    # Path inside the temporary directory
    history_file = tmp_path / "delivery_history.json"
    history_path = str(history_file)
    
    # Initially should not be delivered
    assert not check_already_delivered("groww", "2026-W24", "user@groww.in", history_path=history_path)
    
    # Record a delivery
    record_delivery("groww", "2026-W24", "user@groww.in", history_path=history_path)
    
    # Should now detect as delivered
    assert check_already_delivered("groww", "2026-W24", "user@groww.in", history_path=history_path)
    
    # Different product should not be marked delivered
    assert not check_already_delivered("groww-other", "2026-W24", "user@groww.in", history_path=history_path)
    
    # Different week should not be marked delivered
    assert not check_already_delivered("groww", "2026-W25", "user@groww.in", history_path=history_path)
    
    # Different recipient should not be marked delivered
    assert not check_already_delivered("groww", "2026-W24", "other@groww.in", history_path=history_path)

    # Test corrupted file handling
    with open(history_path, "w", encoding="utf-8") as f:
        f.write("{invalid json}")
        
    # check_already_delivered should handle failure and return False
    assert not check_already_delivered("groww", "2026-W24", "user@groww.in", history_path=history_path)
    
    # record_delivery should reset/create clean list on corrupted file
    record_delivery("groww", "2026-W24", "user@groww.in", history_path=history_path)
    assert check_already_delivered("groww", "2026-W24", "user@groww.in", history_path=history_path)


def test_workspace_delivery():
    from unittest.mock import patch, MagicMock
    import json
    from click.testing import CliRunner
    from src.cli import run

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
    # First response: Google Docs tool response
    mock_doc_resp = MagicMock()
    mock_doc_resp.__enter__.return_value = mock_doc_resp
    mock_doc_resp.read.return_value = json.dumps({
        "status": "success",
        "result": {
            "document_url": "https://docs.google.com/document/d/mock_doc_id/edit#heading=pulse-anchor-2026-W24",
            "header_anchor_id": "pulse-anchor-2026-W24"
        }
    }).encode('utf-8')
    
    # Second response: Gmail tool response
    mock_gmail_resp = MagicMock()
    mock_gmail_resp.__enter__.return_value = mock_gmail_resp
    mock_gmail_resp.read.return_value = json.dumps({
        "status": "success",
        "result": {
            "message_id": "gmail_mock_12345"
        }
    }).encode('utf-8')

    # Run the click CLI command in mock environment
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
        
        # Configure mock_urlopen to return these two in sequence
        mock_urlopen.side_effect = [mock_doc_resp, mock_gmail_resp]
        
        result = runner.invoke(run, [
            '--product', 'groww',
            '--window-weeks', '12',
            '--recipients', 'test@groww-analytics.internal'
        ])
        
        # Assertions
        assert result.exit_code == 0
        assert "Calling Google Docs Tool" in result.output
        assert "Google Doc updated successfully with formatting" in result.output
        assert "Calling Gmail Tool" in result.output
        assert "Gmail draft created successfully" in result.output
        
        # Check that urlopen was called twice (once for Docs and once for Gmail)
        assert mock_urlopen.call_count == 2


def test_server_endpoints():
    from fastapi.testclient import TestClient
    from src.server import app
    from unittest.mock import patch
    import os
    
    client = TestClient(app)
    
    # Test Root Endpoint
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    
    # Test Status Endpoint
    response = client.get("/api/status")
    assert response.status_code == 200
    assert "status" in response.json()
    assert "token_usage_today" in response.json()
    
    # Test Reviews Endpoint
    response = client.get("/api/reviews")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # Test Runs Endpoint
    response = client.get("/api/runs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # Test Trigger Run Endpoint (mock background execution)
    with patch('src.server.execute_pipeline_task') as mock_execute:
        response = client.post("/api/run", json={
            "product": "groww",
            "window_weeks": 8,
            "dry_run": True,
            "recipients": "test@groww.in"
        })
        assert response.status_code == 200
        assert response.json()["status"] == "accepted"
        mock_execute.assert_called_once()


def test_execution_lock():
    from click.testing import CliRunner
    from src.cli import run, FileLock
    import os
    
    lock_file = os.path.join("logs", "impullse.lock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
        except Exception:
            pass
            
    runner = CliRunner()
    
    # 1. Acquire lock manually to mock another running process
    os.makedirs(os.path.dirname(lock_file), exist_ok=True)
    with open(lock_file, "w") as f:
        f.write(str(os.getppid()))
        
    try:
        # 2. Run CLI command - should abort early due to file lock
        result = runner.invoke(run, ['--dry-run'])
        assert result.exit_code != 0
        assert "Another pipeline execution is already running" in result.output
    finally:
        # 3. Clean up lock
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
            except Exception:
                pass







