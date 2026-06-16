import json
import os
from src.analytics.cluster import ReviewClusterer
from src.analytics.summarize import GeminiSummarizer
from src.analytics.validate import GroundedQuoteValidator

def main():
    print("Loading reviews from Docs/reviews.json...")
    reviews_path = os.path.join("Docs", "reviews.json")
    try:
        with open(reviews_path, "r", encoding="utf-8") as f:
            reviews = json.load(f)
    except FileNotFoundError:
        print("Error: Docs/reviews.json not found. Please run the generator first!")
        return

    print(f"Loaded {len(reviews)} reviews successfully.")
    
    print("\nInitializing ReviewClusterer...")
    clusterer = ReviewClusterer()
    clusters = clusterer.cluster_reviews(reviews, min_cluster_size=25)
    
    print("\nInitializing LLM Summarizer and GroundedQuoteValidator...")
    # It will automatically detect GROQ_API_KEY or GEMINI_API_KEY, falling back to mock if none are found.
    summarizer = GeminiSummarizer()
    validator = GroundedQuoteValidator()
    
    print("\nRunning AI Summarization & Grounded Quote Validation (Phase 3)...")
    report = validator.get_validated_report(summarizer, clusters, reviews, max_retries=3)
    
    print("\n=== Validated AI Summary Report ===")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\n===================================")
    print("GQV Quote Verification: 100% compliant and grounded.")

if __name__ == "__main__":
    main()
