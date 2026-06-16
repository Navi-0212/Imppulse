import feedparser
import datetime
from typing import List, Dict, Any

class AppStoreIngestor:
    def __init__(self, app_id: str = "1402085352", region: str = "in"):
        self.app_id = app_id
        self.region = region
        self.url = f"https://itunes.apple.com/{region}/rss/customerreviews/id={app_id}/sortBy=mostRecent/xml"

    def fetch_reviews(self, window_weeks: int = 12) -> List[Dict[str, Any]]:
        """
        Fetches customer reviews from Apple App Store RSS feed.
        Filters by reviews updated within the window_weeks rolling window.
        """
        feed = feedparser.parse(self.url)
        reviews = []
        
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff_date = now - datetime.timedelta(weeks=window_weeks)
        
        if not feed.entries:
            return []
            
        for entry in feed.entries:
            # Skip the first entry if it's the main app metadata entry
            if "im_rating" not in entry and "im_price" in entry:
                continue
                
            # Date Parsing
            # Feedparser updated_parsed is a time struct
            if hasattr(entry, "updated_parsed") and entry.updated_parsed:
                date_val = datetime.datetime(*entry.updated_parsed[:6], tzinfo=datetime.timezone.utc)
            elif hasattr(entry, "updated"):
                try:
                    date_val = datetime.datetime.fromisoformat(entry.updated.replace("Z", "+00:00"))
                except ValueError:
                    date_val = now
            else:
                date_val = now
                
            if date_val < cutoff_date:
                continue
                
            # Rating Parsing (e.g. entry.im_rating)
            rating = 5
            if hasattr(entry, "im_rating"):
                try:
                    rating = int(entry.im_rating)
                except (ValueError, TypeError):
                    pass
            
            # Content Parsing
            # App Store RSS usually places body text in content
            content_text = ""
            if hasattr(entry, "content") and entry.content:
                content_text = entry.content[0].value
            elif hasattr(entry, "summary"):
                content_text = entry.summary
                
            reviews.append({
                "id": entry.get("id", ""),
                "author": entry.get("author", {}).get("name", "Anonymous") if hasattr(entry, "author") else "Anonymous",
                "title": entry.get("title", ""),
                "text": content_text,
                "rating": rating,
                "date": date_val.isoformat(),
                "platform": "ios"
            })
            
        return reviews
