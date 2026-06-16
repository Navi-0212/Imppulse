import json
import os
from src.analytics.cluster import ReviewClusterer

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
    
    print("\nInitializing ReviewClusterer with BAAI/bge-small-en-v1.5 model...")
    clusterer = ReviewClusterer()
    
    # We use a larger min_cluster_size for 2000 reviews to get clean high-level categories
    min_cluster_size = 25
    print(f"\nClustering reviews (Phase 2) with min_cluster_size={min_cluster_size}...")
    clusters = clusterer.cluster_reviews(reviews, min_cluster_size=min_cluster_size)
    
    print("\n=== Clustering Results ===")
    total_clusters = 0
    noise_count = 0
    
    # Sort clusters by size descending (excluding noise)
    sorted_clusters = []
    for cid, details in clusters.items():
        if details.get("is_noise", False):
            noise_count = details.get("size", 0)
        else:
            sorted_clusters.append((cid, details))
            
    sorted_clusters.sort(key=lambda x: x[1].get("size", 0), reverse=True)
    
    for cid, details in sorted_clusters:
        total_clusters += 1
        print(f"\nCluster {cid} (Size: {details.get('size')} reviews):")
        centroid = details.get("centroid_review", {})
        print(f"  - Representative Rating: {centroid.get('rating')} Stars")
        print(f"  - Representative Review: \"{centroid.get('text')}\"")
            
    print("\n==========================")
    print(f"Total Clusters Identified: {total_clusters}")
    print(f"Noise Reviews Isolated: {noise_count}")

if __name__ == "__main__":
    main()
