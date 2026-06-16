# Problem Statement: Impullse (Weekly Product Review Pulse)

> [!IMPORTANT]
> **Project Context:** Tracking public user sentiment across mobile platforms is crucial for fintech products, but doing so manually is highly inefficient. This project, code-named **Impullse**, builds an automated weekly "pulse" system that scrapes, processes, and aggregates Apple App Store and Google Play Store reviews for the **Groww** application. It converts unstructured customer feedback into actionable insights and delivers them to stakeholders via Google Workspace. Crucially, the system includes custom Google Docs and Gmail MCP servers built directly within this project repository to handle Workspace interactions, bypassing ad-hoc REST API integrations inside the core agent.

---

## 1. Project Vision & Business Drivers

Product, support, and leadership teams in fintech firms must continuously monitor user feedback to catch bugs, prioritize feature roadmaps, and assess overall customer health. However, manually scraping, compiling, and analyzing app store reviews is time-consuming, fragmented, and prone to copy-paste errors.

## 1. The Core Challenges
1. **Multi-Platform Fragmentation:** Customer reviews are split between the Apple App Store (RSS-based feed) and Google Play Store (HTML/API-based scraping).
2. **Noise vs. Signal:** Raw reviews are flooded with uninformative comments (e.g., *"Good app"*, *"Okay"*), making it hard to extract recurring themes.
3. **API Integration Overhead:** Embedding OAuth credentials, managing tokens, and writing direct REST integrations for Google Docs and Gmail inside the agent leads to brittle codebase coupling.
4. **Data Hallucinations:** When summarizing reviews, Large Language Models (LLMs) can invent representative quotes that were never actually written by users.
5. **PII and Safety Risks:** App reviews sometimes contain Personally Identifiable Information (PII) like phone numbers or email addresses, which must be scrubbed before sending to public LLMs or publishing.

---

## 2. Core Objectives

Design and implement a highly secure, modular, and automated system that:
* **Ingests reviews** from the last 8–12 weeks for the **Groww** application.
* **Clusters and summarizes** feedback using embedding models and density-based clustering to extract major themes, verbatim representative quotes, and action items.
* **Validates LLM summaries** by ensuring all generated user quotes are verified, exact substrings of the raw review text.
* **Integrates with Google Workspace via custom MCP servers** created in this project to append reports to a running Google Doc and send teaser emails with heading links to stakeholders.
* **Ensures idempotent execution**, preventing duplicate document sections and duplicate emails on re-runs of the same week.

---

## 3. Supported Fintech Product

The project focuses exclusively on the following consumer fintech application:

| # | Product Name | Platforms | Core Focus |
| :--- | :--- | :--- | :--- |
| 1 | **Groww** | App Store + Google Play | Mutual funds, stock trading, SIPs |

---

## 4. End-to-End System Architecture

The following flowchart illustrates how review data is ingested, structured, processed, and ultimately delivered using Google Docs MCP and Gmail MCP servers.

```mermaid
flowchart TD
    subgraph Data Ingestion Tier
        A1[Apple App Store RSS Feed] --> B[Ingestion Engine]
        A2[Google Play Store Scraper] --> B
        B --> C[PII Scrubbing & Normalization]
    end

    subgraph Analytics & Clustering Tier
        C --> D[Embedding Model]
        D --> E[UMAP Dimensionality Reduction]
        E --> F[HDBSCAN Density Clustering]
        F --> G[Theme Aggregator]
    end

    subgraph LLM Summarization & Validation
        G --> H[LLM Reasoning Prompt]
        H --> I[LLM Theme Namer & Quote Extractor]
        I --> J[Grounded Quote Validator]
        J -- Fail --> I
        J -- Pass --> K[Render Structured Report & Email HTML]
    end

    subgraph Delivery Tier (MCP Host)
        K --> L[MCP Client Interface]
        L --> M[Google Docs MCP Server]
        L --> N[Gmail MCP Server]
        M --> O[Append Dated Section to Running Google Doc]
        N --> P[Send Stakeholder Teaser with Heading Link]
    end

    style M fill:#4285F4,stroke:#333,stroke-width:2px,color:#fff
    style N fill:#EA4335,stroke:#333,stroke-width:2px,color:#fff
    style O fill:#0F9D58,stroke:#333,stroke-width:2px,color:#fff
    style P fill:#F4B400,stroke:#333,stroke-width:2px,color:#fff
```

---

## 5. Technical Stack Recommendation

To ensure scalability, security, and low maintenance overhead, the following technologies are recommended:

| Module | Recommended Technology | Selection Rationale |
| :--- | :--- | :--- |
| **Ingestion Engine** | Python, `Playwright`, `feedparser` | `feedparser` quickly extracts RSS xml data from iTunes; `Playwright` drives dynamic Google Play web crawls. |
| **Clustering & Embeddings** | `SentenceTransformers`, `umap-learn`, `hdbscan` | Provides localized, high-performance semantic representation and noise-resilient clustering of short texts. |
| **PII Scrubbing** | `presidio-analyzer`, `re` | Microsoft Presidio provides enterprise-grade scanning and masking of phone numbers, emails, and names. |
| **LLM & Grounding** | `Gemini 1.5 Flash` or `Pro` | Fast inference, strong reasoning capabilities, and excellent structured JSON output capabilities. |
| **Workspace Integration** | **Model Context Protocol (MCP)** | Decouples Google credentials from the core logic, utilizing custom Gmail and Google Docs MCP servers created directly inside this project repository. |
| **CLI & Execution** | Python `click` or `argparse` | Enables easy backfilling of specific ISO weeks and configuration of review rolling windows. |

---

## 6. Functional Requirements & Core Modules

### 6.1. Ingestion & Preprocessing
* **Scraping Boundary:** Fetch reviews spanning the last 8–12 weeks.
* **PII Redaction:** Automatically scan and scrub private credentials (emails, phone numbers, addresses, account IDs) using rule-based and NER (Named Entity Recognition) engines.
* **Reviews as Data:** Enforce prompt structures that treat reviews strictly as data payloads rather than executable instructions (preventing prompt injection).

### 6.2. Semantic Clustering & Reasoning
* **Vectorization:** Convert scrubbed review text into dense vector representations.
* **Density-Based Clustering:** Filter out uninformative comments (categorized as noise by HDBSCAN) and cluster reviews into high-density topic nodes.
* **Grounded Quote Validation:** The system must inspect the LLM-selected quotes and verify they are present character-for-character in the source review text.

### 6.3. Idempotent Delivery Layer
* **Docs Append:** Add the generated summary as a new section to the product's running Doc (e.g. *Weekly Review Pulse — Groww*). If a run is re-executed for the same week/product, the system must search for the week's anchor ID and replace the existing section instead of creating a duplicate.
* **Gmail Notification:** Send a teaser email to stakeholders containing key bullet points and a deep link to the heading inside the running Google Doc.
* **Delivery Logging:** Log the document ID, message ID, and run parameters for compliance auditing.

---

## 7. Sample Output Structure (Illustrative)

### **Groww — Weekly Review Pulse**
* **Period:** Last 8–12 weeks (Rolling Window: ISO Week 24, 2026)
* **Top Themes:**
  1. **App performance & bugs:** Lag and application freezes during market open (9:15 AM IST); session timeouts.
  2. **Customer support friction:** Long response delays; automated chat answers not resolving tickets.
  3. **UX & feature gaps:** Confusing navigation inside portfolio analytics; missing advanced charts.
* **Verbatim User Quotes:**
  * *"The app freezes exactly when the market opens, very frustrating."*
  * *"Support takes days to reply and doesn't solve the issue."*
* **Actionable Recommendations:**
  * **Stabilize peak-time performance:** Scale infrastructure during 9:15 AM market hours.
  * **Improve support SLA visibility:** Add expected wait times directly in the in-app chat drawer.

---

## 8. Explicit Non-Goals

* Building a generic Google Workspace integration client beyond Docs append and Gmail drafting.
* Creating a dynamic frontend BI dashboard or real-time streaming charts (the shared, running Google Doc serves as the primary system of record).
* Scraping social channels (Twitter, Reddit, Discord) in the initial phase.
* Hardcoding credentials, refresh tokens, or secrets inside the codebase (secrets belong strictly in configuration files or environment variables loaded by the custom MCP servers).