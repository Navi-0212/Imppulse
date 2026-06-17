import logging
import numpy as np
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ReviewClusterer:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        self.embedding_model = None
        self.umap_available = False
        self.hdbscan_available = False
        
        # Try importing sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded SentenceTransformer: {self.model_name}")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer: {str(e)}. Will use fallback TF-IDF/KMeans representation.")
            
        # Try importing UMAP & HDBSCAN
        try:
            import umap
            import hdbscan
            self.umap_available = True
            self.hdbscan_available = True
            logger.info("UMAP and HDBSCAN imported successfully.")
        except Exception as e:
            logger.warning(f"UMAP/HDBSCAN not available: {str(e)}. Falling back to pure scikit-learn KMeans clustering.")

    def cluster_reviews(self, reviews: List[Dict[str, Any]], min_cluster_size: int = 2) -> Dict[str, Any]:
        """
        Clusters a list of review dicts into semantic themes.
        Returns a dictionary mapping cluster IDs to cluster details (reviews, centroid review, size).
        """
        if not reviews:
            return {}
            
        # If there are too few reviews, put them in a single cluster
        if len(reviews) < 3:
            return {
                "0": {
                    "cluster_id": 0,
                    "reviews": reviews,
                    "centroid_review": reviews[0],
                    "size": len(reviews)
                }
            }

        texts = [r["text"] for r in reviews]

        # Check if we can run UMAP + HDBSCAN
        if self.embedding_model and self.umap_available and self.hdbscan_available:
            try:
                import umap
                import hdbscan
                
                logger.info("Generating embeddings...")
                embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
                
                logger.info("Reducing dimensions with UMAP...")
                # Set random_state for reproducible clustering
                reducer = umap.UMAP(n_neighbors=min(15, len(reviews) - 1), n_components=2, min_dist=0.0, random_state=42)
                reduced_embeddings = reducer.fit_transform(embeddings)
                
                logger.info("Clustering with HDBSCAN...")
                clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, gen_min_span_tree=True)
                labels = clusterer.fit_predict(reduced_embeddings)
                
                return self._group_by_labels(reviews, embeddings, labels)
            except Exception as e:
                logger.error(f"UMAP/HDBSCAN clustering failed: {str(e)}. Retrying with TF-IDF and KMeans...")

        # Fallback 1: TF-IDF + KMeans
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.cluster import KMeans
            
            logger.info("Using TF-IDF & KMeans fallback...")
            vectorizer = TfidfVectorizer(stop_words='english', min_df=1, max_df=1.0)
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Determine number of clusters (typically 3 for smaller sets, up to 5)
            n_clusters = min(4, len(reviews))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            labels = kmeans.fit_predict(tfidf_matrix)
            
            # Dense representation for centroid calculation
            dense_matrix = tfidf_matrix.toarray()
            
            return self._group_by_labels_tfidf(reviews, dense_matrix, labels, kmeans.cluster_centers_)
        except Exception as e:
            logger.error(f"TF-IDF/KMeans clustering failed: {str(e)}. Using simple length/rating-based sorting fallback.")
            
        # Fallback 2: Simple rating/length-based grouping
        return self._fallback_simple_sorting(reviews)

    def _group_by_labels(self, reviews: List[Dict[str, Any]], embeddings: np.ndarray, labels: np.ndarray) -> Dict[str, Any]:
        """
        Groups reviews by UMAP/HDBSCAN labels and calculates centroids.
        """
        grouped = {}
        unique_labels = set(labels)
        
        for label in unique_labels:
            # -1 is the noise label in HDBSCAN. We group noise reviews together, but handle centroid differently
            is_noise = (label == -1)
            
            indices = [idx for idx, l in enumerate(labels) if l == label]
            cluster_reviews = [reviews[idx] for idx in indices]
            cluster_embeddings = embeddings[indices]
            
            # Compute centroid (mean vector)
            centroid = np.mean(cluster_embeddings, axis=0)
            
            # Find the review closest to the centroid
            distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)
            closest_idx = indices[np.argmin(distances)]
            centroid_review = reviews[closest_idx]
            
            grouped[str(label)] = {
                "cluster_id": int(label),
                "is_noise": is_noise,
                "reviews": cluster_reviews,
                "centroid_review": centroid_review,
                "size": len(cluster_reviews)
            }
            
        return grouped

    def _group_by_labels_tfidf(self, reviews: List[Dict[str, Any]], dense_matrix: np.ndarray, labels: np.ndarray, centers: np.ndarray) -> Dict[str, Any]:
        """
        Groups reviews by KMeans labels and computes representative reviews.
        """
        grouped = {}
        unique_labels = set(labels)
        
        for label in unique_labels:
            indices = [idx for idx, l in enumerate(labels) if l == label]
            cluster_reviews = [reviews[idx] for idx in indices]
            cluster_matrix = dense_matrix[indices]
            
            # KMeans centers are provided
            center = centers[label]
            
            # Find the review closest to the cluster center
            distances = np.linalg.norm(cluster_matrix - center, axis=1)
            closest_idx = indices[np.argmin(distances)]
            centroid_review = reviews[closest_idx]
            
            grouped[str(label)] = {
                "cluster_id": int(label),
                "is_noise": False,
                "reviews": cluster_reviews,
                "centroid_review": centroid_review,
                "size": len(cluster_reviews)
            }
            
        return grouped

    def _fallback_simple_sorting(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sorts reviews into three primitive buckets (Negative, Neutral, Positive) when all ML modules fail.
        """
        logger.info("Using basic rating-based sorting fallback.")
        grouped = {
            "negative": {"cluster_id": "negative", "reviews": [], "centroid_review": None, "size": 0},
            "neutral": {"cluster_id": "neutral", "reviews": [], "centroid_review": None, "size": 0},
            "positive": {"cluster_id": "positive", "reviews": [], "centroid_review": None, "size": 0}
        }
        
        for r in reviews:
            rating = r.get("rating", 3)
            if rating <= 2:
                grouped["negative"]["reviews"].append(r)
            elif rating == 3:
                grouped["neutral"]["reviews"].append(r)
            else:
                grouped["positive"]["reviews"].append(r)
                
        # Calculate size and pick the longest review as representative "centroid"
        keys_to_delete = []
        for key, value in grouped.items():
            value["size"] = len(value["reviews"])
            if value["size"] > 0:
                # Pick the longest review as it contains the most context
                value["reviews"].sort(key=lambda x: len(x.get("text", "")), reverse=True)
                value["centroid_review"] = value["reviews"][0]
            else:
                keys_to_delete.append(key)
                
        for key in keys_to_delete:
            del grouped[key]
            
        return grouped
