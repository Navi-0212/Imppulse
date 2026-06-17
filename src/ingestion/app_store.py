import feedparser
import datetime
from typing import List, Dict, Any

class AppStoreIngestor:
    def __init__(self, app_id: str = "1402085352", region: str = "in"):
        self.app_id = app_id
        self.region = region
        self.url = f"https://itunes.apple.com/{region}/rss/customerreviews/id={app_id}/sortBy=mostRecent/xml"

    def fetch_reviews(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Fetches customer reviews from Apple App Store RSS feed.
        Filters by reviews updated within the specified start_date and end_date.
        """
        feed = feedparser.parse(self.url)
        reviews = []
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Calculate defaults if not provided
        if not start_date and not end_date:
            # Default to previous calendar week (or last 7 days as rolling fallback)
            start_dt = now - datetime.timedelta(days=7)
            end_dt = now
        else:
            default_start = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
            default_end = now
            
            # Helper to parse string dates
            def parse_date(d_str, default):
                if not d_str:
                    return default
                try:
                    if "t" in d_str.lower():
                        return datetime.datetime.fromisoformat(d_str.replace("Z", "+00:00")).astimezone(datetime.timezone.utc)
                    else:
                        dt = datetime.datetime.strptime(d_str, "%Y-%m-%d")
                        return dt.replace(tzinfo=datetime.timezone.utc)
                except Exception:
                    return default
            
            start_dt = parse_date(start_date, default_start)
            end_dt = parse_date(end_date, default_end)
            
            # Set times for simple YYYY-MM-DD boundaries
            if start_date and "t" not in start_date.lower():
                start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            if end_date and "t" not in end_date.lower():
                end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            
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
                
            if date_val < start_dt or date_val > end_dt:
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
