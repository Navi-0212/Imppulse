import html
import re
from datetime import datetime
from typing import Dict, Any, List

def normalize_text(text: str) -> str:
    """
    Normalizes review text by:
    1. Decoding HTML entities (e.g. &amp; -> &, &#39; -> ')
    2. Standardizing carriage returns and newlines (\r\n -> \n)
    3. Collapsing multiple spaces or tabs into a single space
    4. Trimming whitespace from lines and stripping empty lines
    """
    if not text:
        return ""
    
    # 1. Decode HTML entities
    text = html.unescape(text)
    
    # 2. Standardize carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # 3. Collapse horizontal whitespace (spaces/tabs)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # 4. Clean up leading/trailing line spacing and drop consecutive empty lines
    lines = [line.strip() for line in text.split('\n')]
    text = "\n".join([line for line in lines if line])
    
    return text.strip()

def normalize_review(review: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes a single review dictionary. Maps Google Play scraper keys to our clean structure
    and explicitly discards reviewId, userName, userImage, reviewCreatedVersion, at, replyContent, and repliedAt.
    """
    # 1. Map scraper keys if they exist
    review_id = review.get("id") or review.get("reviewId") or ""
    author = review.get("author") or review.get("userName") or "Anonymous"
    text = review.get("text") or review.get("content") or ""
    
    # Extract rating (supports "rating" or "score")
    rating_val = review.get("rating")
    if rating_val is None:
        rating_val = review.get("score")
    if rating_val is None:
        rating_val = 3
        
    # Extract date (supports "date" or "at")
    date_val = review.get("date") or review.get("at")
    if isinstance(date_val, datetime):
        date_str = date_val.isoformat()
    elif isinstance(date_val, str):
        date_str = date_val
    else:
        date_str = ""
        
    platform = review.get("platform") or "android"
    title = review.get("title") or ""
    
    # 2. Build final clean normalized dictionary (discards non-standard keys)
    normalized = {
        "id": str(review_id).strip(),
        "author": normalize_text(str(author)),
        "title": normalize_text(str(title)),
        "text": normalize_text(str(text)),
        "rating": 3,
        "date": str(date_str).strip(),
        "platform": str(platform).strip()
    }
    
    # Rating clamping
    try:
        rating = int(rating_val)
        normalized["rating"] = max(1, min(5, rating))
    except (ValueError, TypeError):
        normalized["rating"] = 3
        
    return normalized

def normalize_reviews(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalizes a list of review dictionaries.
    """
    return [normalize_review(r) for r in reviews]
