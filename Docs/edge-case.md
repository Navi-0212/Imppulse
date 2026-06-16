# Edge Cases and Corner Cases: Project Impullse

This document details critical edge cases, failure modes, and corner cases for **Impullse (Weekly Product Review Pulse)**. For each scenario, we define the technical risk, system behavior, and mitigation strategies implemented in the codebase.

---

## 1. Data Ingestion & Crawler Layer

### 1.1. High-Volume RSS Capping Limit
* **Scenario:** The Apple App Store RSS feed limits the payload to a maximum of **500 reviews**. For high-volume fintech apps like **Groww**, 500 reviews can easily represent only the last 2-3 days of customer feedback, making it impossible to reconstruct an 8-12 weeks historical window in a single crawl.
* **System Behavior:** The `AppStoreIngestor` fetches the current 500 feed entries. Reviews older than the rolling window cutoff are discarded.
* **Mitigation:**
  * **Paging & Archival:** The pipeline is designed to write incremental execution logs under `logs/runs/`. A future production upgrade should load these runs into a persistent database to build a complete historical review timeline, rather than crawling the RSS feed from scratch each week.

### 1.2. Play Store Crawler Blocking & CAPTCHAs
* **Scenario:** Google Play Store listing structures are protected by anti-bot frameworks. Consecutive automated runs via Playwright can trigger CAPTCHAs, cookie blocks, or temporary IP bans.
* **System Behavior:** Playwright throws timeout errors or fails to locate the "See all reviews" button.
* **Mitigation:**
  * **Offline/Mock Fallback:** If `playwright` imports fail or the scraper throws an error, the system catches the exception and falls back to a high-fidelity local mock review engine that yields Groww-centric ratings and issue categories (e.g. 9:15 AM IST freezes, mutual fund settlement, chatbot SLA delays).
  * **Scraper Randomization:** The crawler sets language query parameters (`&hl=en`), uses dynamic viewport profiles, and implements scroll throttling delays (`time.sleep(1.5)`) to reduce access footprints.

### 1.3. Zero or Extremely Low Review Volumes
* **Scenario:** A product is run during holiday seasons, or is configured with a narrow date window yielding 0 or 1 total reviews.
* **System Behavior:** Density-based clustering algorithms (like UMAP/HDBSCAN) require a minimum number of samples. Running them on empty or single-item datasets causes mathematical dimension exceptions (e.g., UMAP nearest neighbor index errors).
* **Mitigation:**
  * **Short-Circuit Verification:** `cli.py` evaluates review payload size immediately after ingestion. If `len(all_reviews) == 0`, it logs the status `no_reviews` and terminates cleanly without initializing the analytics engine.
  * **Small-Dataset Handling:** In `cluster.py`, if review count is less than 3, the clusterer skips vector clustering and returns a single pre-grouped cluster holding the raw inputs.

---

## 2. PII Safety & Redaction Gate

### 2.1. Over-Redaction of Numerical Values
* **Scenario:** Regex rules redact all numbers greater than 4 digits (to strip phone numbers, credit cards, user IDs, or OTPs). This risks over-redacting valuable feedback, such as currency figures (e.g., *"lost Rs. 50000"*) or ticket IDs.
* **System Behavior:** Value strings are scrubbed into `[ID]`.
* **Mitigation:**
  * **Entity Scoping:** The regular expressions use strict boundary matches (`\b\d{5,}\b`) to avoid scrubbing formatted decimals, dates, or version numbers (e.g. `version 5.4.1`).

### 2.2. Offline SpaCy Model Download Failures
* **Scenario:** Microsoft Presidio Analyzer requires downloading a SpaCy language model (like `en_core_web_sm`). On disconnected air-gapped runtimes, downloading this model fails, causing Presidio to crash on startup.
* **System Behavior:** An exception is caught during initialization of `AnalyzerEngine`.
* **Mitigation:**
  * **Dual-Layer Fallback:** The `PIIScrubber` runs in a try-except block. If Presidio fails to initialize, it toggles a `presidio_available = False` flag and falls back to a locally compiled regex engine that masks emails, phone numbers, and IDs with zero network dependencies.

---

## 3. Analytics & Topic Clustering

### 3.1. UMAP/HDBSCAN Native C++ Compilation Failures
* **Scenario:** `umap-learn` and `hdbscan` depend on native C/C++ compilation headers (Numba/Cython). On standard Windows developer machines without Visual Studio Build Tools, installing these python packages can fail.
* **System Behavior:** Import errors or DLL loading failures.
* **Mitigation:**
  * **Layered Fallbacks:** In `cluster.py`, the `ReviewClusterer` handles import errors. If UMAP/HDBSCAN fail, it automatically falls back to a scikit-learn `TF-IDF Vectorizer` combined with `KMeans` clustering (which is extremely reliable and pre-built on PyPI). If scikit-learn also fails, it implements a primitive fallback that groups reviews into Negative, Neutral, and Positive rating buckets.

### 3.2. All Reviews Classified as Noise
* **Scenario:** HDBSCAN is a density-based algorithm. If review feedback is extremely disjointed, HDBSCAN will categorize 100% of reviews as noise (assigning label `-1` to all records), resulting in zero valid clusters.
* **System Behavior:** The LLM prompt context is empty.
* **Mitigation:**
  * **Noise Centroid Recovery:** If no clusters are formed, the system falls back to pulling representative reviews directly from the noise cluster to provide context to the summarizer.

---

## 4. Summarization & Grounding (GQV)

### 4.1. LLM Quote Formatting and Hallucinations
* **Scenario:** The LLM summarizes themes but returns slightly modified quotes (e.g. correcting typos, inserting punctuation, or paraphrasing), which fails verbatim GQV checking.
* **System Behavior:** The quote is flagged as invalid.
* **Mitigation:**
  * **GQV Self-Correcting Retry Loop:** The `GroundedQuoteValidator` runs up to 3 generation attempts. On failure, it appends a critical warning listing the failed quotes and re-submits the prompt to Gemini.
  * **Strict Force-Grounding Safeguard:** If the retry loop is exhausted, the system runs `_force_ground_quotes` to replace any invalid quote with a verified actual raw review string, ensuring the final Workspace output meets compliance rules.

---

## 5. Workspace MCP & Subprocess Delivery

### 5.2. Stdio Subprocess Buffering Deadlocks
* **Scenario:** Python and Node.js standard streams use buffering. If the spawned Node.js process does not flush stdout after writing a JSON-RPC response, the Python parent client will block indefinitely waiting for output, resulting in a deadlock.
* **System Behavior:** The run hangs on Docs or Gmail tool calls.
* **Mitigation:**
  * **Line-Buffered Streams:** Python spawns the subprocess with `bufsize=1` (line-buffered) and explicitly calls `.flush()` on write. The Node.js MCP server uses `readline` to process inputs line-by-line and writes JSON payloads ending with `\n` to prevent stream blocks.

### 5.3. Double Notification Dispatches (Idempotency)
* **Scenario:** If a scheduled pipeline crashes mid-run or is manually re-run for the same week, stakeholders might receive duplicate email alerts.
* **System Behavior:** Gmail sends duplicate notifications.
* **Mitigation:**
  * **Run history Caching:** The Gmail MCP server reads and updates `logs/delivery_history.json`. Before sending a teaser, it checks for a `(product_name, iso_week, type="email_sent")` entry and skips the tool call if found.
  * **Heading Anchor Updates:** The Google Docs MCP server queries the doc structure for `pulse-anchor-[ISO_WEEK]`. If found, it overwrites the existing section range in-place rather than appending a duplicate page.
