# Stitch UI Generation Prompt: Impullse Sentiment Dashboard

Below is the complete, copy-pasteable prompt optimized for Stitch (or other LLM frontend generation tools like v0 or Lovable).

```text
Create a modern, highly polished, lowkey, and professional single-page web application dashboard for "Impullse" — a weekly customer sentiment intelligence engine for consumer fintech applications. 

### Core Design Philosophy & Aesthetics:
- **Style**: Ultra-minimalist, sophisticated, and clean. It must NOT look like a generic, heavy enterprise portal (no blocky multi-colored card grids, nested borders, or crowded dashboard layout). Use generous whitespace, sleek thin borders, and subtle typographic contrast.
- **Color Palette (Mild, Lowkey, Professional)**:
  - Background: Very dark, premium slate/graphite steel (`#080b11` to `#0d1117`).
  - Card Surfaces: Semi-translucent dark slate (`rgba(22, 28, 45, 0.4)`) with very fine sub-pixel borders (`rgba(255, 255, 255, 0.05)`).
  - Primary Accent: A mild, professional mint/teal (`#00c090`) for active nav items, progress highlights, and success states, matching the brand of fintech apps like Groww but keeping it muted.
  - Secondary Text: Mild slate/gray (`#94a3b8` for subtitles, `#cbd5e1` for headers).
  - Warnings & Indicators: Very soft amber/orange (`#f59e0b`) and muted crimson (`#ef4444`).
- **Typography**: Clean, premium sans-serif (e.g., 'Outfit' for titles/headers, 'Inter' for text/data grids). Use monospaced font family for configuration items and timestamps.
- **Micro-interactions**: Soft hover scaling, thin glowing borders on cards when active, and smooth tab fade transitions.

### Layout & Page Structure:
1. **Sidebar Navigation (Sleek & Lowkey)**:
   - Modern, high-contrast title: "Impullse" with a smaller subtitle: "Sentiment Engine".
   - Minimalist vertical tab buttons: Dashboard, Sentiment Clusters, Review Explorer, Audit Logs.
   - Sidebar Footer: A small, low-opacity "Config Overview" card showing the targets (e.g., Google Doc ID and Google Workspace MCP server status) as truncated monospace texts.
2. **Main Header (Compact)**:
   - Current tab title (e.g., "Dashboard Overview") and a light, muted caption.
   - Status badge in the top right: A glowing green/orange pulse dot (e.g., "🟢 System Idle" or "🟡 Running").
   - Action Button: A clean, primary button with a rocket icon: "Trigger Ingestion Run".
3. **Primary Viewports (Tab Switched)**:
   - **Dashboard View**:
     - Key Metrics Lineup: 4 lightweight cards showing "Reviews Ingested", "Semantic Clusters", "Outlier Noise Discarded", and "GQV Grounding Compliance (100%)". Use clean numeric text and small icons.
     - Operational health summary explaining the scrubbing gates, GQV (Grounded Quote Validator) self-correction retry count, and daily token budget tracker (represented by a sleek thin progress bar showing token limits like "12,500 / 70,000").
   - **Sentiment Clusters View**:
     - Interactive accordions displaying semantic categories (e.g., "App Stability at Market Open", "Support Ticket Response Friction").
     - Inside each accordion: A "Summary Analysis" text, a "Verbatim Feedback Quotes" block (shown inside a clean, blockquoted left-border style), and "Actionable Product/Support Recommendations" formatted as bullet items.
   - **Review Explorer View**:
     - Search input and dropdown filters (Platform: iOS/Android, Rating: 1-5 Stars).
     - Clean list table displaying the processed and PII-scrubbed reviews (emails, phone numbers, and transactional reference IDs should be styled as highlight-red inline tags like "[EMAIL]").
   - **Audit Logs View**:
     - Chronological list of historical execution runs showing: Run Timestamp, ISO Week, Ingestion Volume, Total Clusters, Delivery Status, and a "View Details" button.

### Popups & Control Triggers:
- **Run Pipeline Modal**: A clean overlay card containing:
  - Input field for "Product Name" (default: "groww").
  - Numerical input for "Rolling Window (Weeks)" (default: 12).
  - Checkbox for "Dry-run Mode" (runs analytics and validation locally without pushing to Google Docs/Gmail).
  - Input field for "Recipients" (comma-separated stakeholder emails).
- **Run Progress Console Drawer**: A slide-up status console showing live steps of the pipeline: Ingestion, Clustering, Quote Grounding Validation, and Workspace Delivery, with small rotating spinner highlights.
- **JSON Detail Modal**: Displays the raw run JSON audit logs in a pretty-printed code block.
```
