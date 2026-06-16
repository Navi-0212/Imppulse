import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Regex to detect common emoji ranges and symbols in Unicode
EMOJI_PATTERN = re.compile(
    r'[\u2600-\u27BF]|'           # Miscellaneous Symbols and Dingbats
    r'[\U0001F300-\U0001F6FF]|'   # Miscellaneous Symbols and Pictographs / Transport
    r'[\U0001F900-\U0001F9FF]|'   # Supplemental Symbols and Pictographs
    r'[\U0001F600-\U0001F64F]|'   # Emoticons
    r'[\U0001F680-\U0001F6FF]|'   # Transport and Map Symbols
    r'[\U00010000-\U0010FFFF]'    # Supplementary Multilingual Plane (almost all modern emojis)
)

# Regex to match non-English scripts while permitting Latin characters, numbers, and standard punctuation.
# Matches Devanagari (Hindi), Bengali, Gurmukhi, Gujarati, Oriya, Tamil, Telugu, Kannada, Malayalam,
# Thai, Cyrillic (Russian), Arabic, and CJK (Chinese, Japanese, Korean) characters.
NON_ENGLISH_SCRIPT_PATTERN = re.compile(
    r'[\u0900-\u097F]|'           # Devanagari (Hindi)
    r'[\u0980-\u09FF]|'           # Bengali
    r'[\u0A00-\u0A7F]|'           # Gurmukhi
    r'[\u0A80-\u0AFF]|'           # Gujarati
    r'[\u0B00-\u0B7F]|'           # Oriya
    r'[\u0B80-\u0BFF]|'           # Tamil
    r'[\u0C00-\u0C7F]|'           # Telugu
    r'[\u0C80-\u0CFF]|'           # Kannada
    r'[\u0D00-\u0D7F]|'           # Malayalam
    r'[\u0E00-\u0E7F]|'           # Thai
    r'[\u0400-\u04FF]|'           # Cyrillic
    r'[\u0600-\u06FF]|'           # Arabic
    r'[\u3000-\u303F]|'           # CJK Punctuation
    r'[\u3040-\u309F]|'           # Hiragana
    r'[\u30A0-\u30FF]|'           # Katakana
    r'[\u4E00-\u9FFF]'            # Chinese Ideographs
)

class ReviewFilter:
    def __init__(self, min_word_count: int = 8):
        self.min_word_count = min_word_count

    def should_keep(self, text: str) -> bool:
        """
        Determines if a review should be kept based on:
        1. Length (must have at least min_word_count words)
        2. No emojis
        3. No non-English script characters
        """
        if not text:
            return False
            
        # 1. Word Count Check
        words = text.split()
        if len(words) < self.min_word_count:
            return False
            
        # 2. Emoji Check
        if EMOJI_PATTERN.search(text):
            return False
            
        # 3. Non-English Script Check
        if NON_ENGLISH_SCRIPT_PATTERN.search(text):
            return False
            
        return True

    def filter_reviews(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filters a list of review dictionaries. Returns the filtered list.
        """
        filtered = []
        for r in reviews:
            text = r.get("text", "")
            if self.should_keep(text):
                filtered.append(r)
        
        logger.info(f"Filtered reviews: {len(reviews)} raw -> {len(filtered)} remaining.")
        return filtered
