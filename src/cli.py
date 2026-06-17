import click
import json
import datetime
import os
import logging
from typing import Dict, Any
from src.ingestion.app_store import AppStoreIngestor
from src.ingestion.play_store import PlayStoreScraper
from src.ingestion.scrub import PIIScrubber
from src.analytics.cluster import ReviewClusterer
from src.analytics.summarize import GeminiSummarizer
from src.analytics.validate import GroundedQuoteValidator
from src.client import MCPClient
from src.ingestion.filter import ReviewFilter
from src.ingestion.normalize import normalize_reviews

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("impullse")

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()


class FileLockError(Exception):
    pass

class FileLock:
    def __init__(self, lock_file: str):
        self.lock_file = lock_file
        self.is_acquired = False
        
    def acquire(self):
        os.makedirs(os.path.dirname(self.lock_file), exist_ok=True)
        
        # Try to atomically create the file
        try:
            fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                with os.fdopen(fd, 'w') as f:
                    f.write(str(os.getpid()))
                self.is_acquired = True
                return
            except Exception:
                try:
                    os.remove(self.lock_file)
                except OSError:
                    pass
                raise
        except FileExistsError:
            # File already exists, check if PID inside is active
            pass

        try:
            with open(self.lock_file, "r") as f:
                pid = int(f.read().strip())
            
            # If the PID inside is our own PID, it means this is a stale lock from a previous
            # container run (since our current running instance hasn't acquired it yet).
            if pid == os.getpid():
                try:
                    os.remove(self.lock_file)
                except OSError:
                    pass
                # Re-acquire
                fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, 'w') as f:
                    f.write(str(os.getpid()))
                self.is_acquired = True
                return

            # Check if process is still running
            os.kill(pid, 0)
            raise FileLockError(f"Another pipeline execution is already running (PID: {pid}).")
        except (ValueError, OSError):
            # Process is dead or PID is invalid, reclaim the lock
            try:
                os.remove(self.lock_file)
            except OSError:
                pass
                
            # Attempt to acquire one more time
            try:
                fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, 'w') as f:
                    f.write(str(os.getpid()))
                self.is_acquired = True
            except FileExistsError:
                # Another process acquired it in the split second between remove and open
                try:
                    with open(self.lock_file, "r") as f:
                        pid = int(f.read().strip())
                    raise FileLockError(f"Another pipeline execution is already running (PID: {pid}).")
                except Exception:
                    raise FileLockError("Another pipeline execution is already running.")
            
    def release(self):
        if self.is_acquired:
            try:
                if os.path.exists(self.lock_file):
                    os.remove(self.lock_file)
                self.is_acquired = False
            except Exception:
                pass

@click.group()
def cli():
    """Impullse: Weekly Product Review Pulse CLI."""
    pass

@cli.command()
@click.option("--product", default="groww", help="Name of product to run (default: groww)")
@click.option("--start-date", default=None, help="Start date in YYYY-MM-DD format (defaults to start of previous week)")
@click.option("--end-date", default=None, help="End date in YYYY-MM-DD format (defaults to end of previous week)")
@click.option("--dry-run", is_flag=True, help="Run ingestion and analytics without Workspace delivery")
@click.option("--recipients", default="stakeholders@groww-analytics.internal", envvar="STAKEHOLDER_EMAILS", help="Comma-separated recipient emails")
def run(product, start_date, end_date, dry_run, recipients):
    """Executes the weekly product review aggregation, clustering, AI summarization, GQV validation, and Workspace delivery."""
    click.echo(f"Starting Impullse weekly run for {product.upper()}...")
    
    lock_file = os.path.join("logs", "impullse.lock")
    lock = FileLock(lock_file)
    try:
        lock.acquire()
    except FileLockError as e:
        raise click.ClickException(f"Run aborted: {str(e)}")

    
    # Calculate previous calendar week defaults if not specified
    if not start_date and not end_date:
        today_date = datetime.date.today()
        # Previous calendar week: Monday to Sunday
        last_monday = today_date - datetime.timedelta(days=today_date.weekday() + 7)
        last_sunday = last_monday + datetime.timedelta(days=6)
        start_date = last_monday.strftime("%Y-%m-%d")
        end_date = last_sunday.strftime("%Y-%m-%d")
        click.echo(f"No date range specified. Defaulting to previous calendar week: {start_date} to {end_date}")
    elif not start_date:
        start_date = "1970-01-01"
    elif not end_date:
        end_date = datetime.date.today().strftime("%Y-%m-%d")
        
    # Calculate ISO week from start_date
    try:
        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        year, week, _ = start_dt.isocalendar()
        iso_week = f"{year}-W{week:02d}"
    except Exception:
        today_date = datetime.date.today()
        year, week, _ = today_date.isocalendar()
        iso_week = f"{year}-W{week:02d}"
        
    click.echo(f"ISO Week Target: {iso_week} (Date range: {start_date} to {end_date})")
    
    # Setup run log path
    runs_dir = os.path.join("logs", "runs")
    os.makedirs(runs_dir, exist_ok=True)
    run_log_path = os.path.join(runs_dir, f"run_{product}_{iso_week}.json")
    
    # Init run log payload
    run_payload = {
        "metadata": {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "product": product,
            "iso_week": iso_week,
            "start_date": start_date,
            "end_date": end_date,
        },
        "stats": {},
        "delivery": {},
        "errors": []
    }
    
    try:
        # 1. Ingestion Phase
        click.echo("\n--- Phase 1: Ingestion & PII Scrubbing ---")
        click.echo("Fetching iOS reviews from App Store...")
        ios_ingestor = AppStoreIngestor()
        ios_reviews = ios_ingestor.fetch_reviews(start_date=start_date, end_date=end_date)
        click.echo(f"Fetched {len(ios_reviews)} reviews from iOS App Store.")
        
        click.echo("Fetching Android reviews from Google Play Store...")
        android_scraper = PlayStoreScraper()
        android_reviews = android_scraper.scrape_reviews(start_date=start_date, end_date=end_date)
        click.echo(f"Fetched {len(android_reviews)} reviews from Google Play Store.")
        
        all_reviews = ios_reviews + android_reviews
        click.echo(f"Total reviews ingested: {len(all_reviews)}")
        run_payload["stats"]["reviews_ingested"] = len(all_reviews)
        
        if not all_reviews:
            click.echo("No reviews found in the specified window. Exiting.")
            run_payload["stats"]["status"] = "no_reviews"
            save_run_log(run_log_path, run_payload)
            return
            
        # Normalization Phase
        click.echo("Normalizing reviews (HTML unescaping, whitespace cleanup)...")
        normalized_reviews = normalize_reviews(all_reviews)

        # Filtering Phase (Length >= 8 words, No Emojis, English Only)
        click.echo("Filtering reviews (length >= 8 words, no emojis, English only)...")
        review_filter = ReviewFilter(min_word_count=8)
        filtered_reviews = review_filter.filter_reviews(normalized_reviews)
        click.echo(f"Reviews remaining after filtering: {len(filtered_reviews)}")
        run_payload["stats"]["reviews_after_filtering"] = len(filtered_reviews)
        
        if not filtered_reviews:
            click.echo("No reviews remaining after filtering. Exiting.")
            run_payload["stats"]["status"] = "no_reviews_after_filtering"
            save_run_log(run_log_path, run_payload)
            return

        # PII Scrubbing
        click.echo("Scrubbing PII from filtered reviews...")
        scrubber = PIIScrubber()
        scrubbed_reviews = scrubber.scrub_reviews(filtered_reviews)
        click.echo("PII scrubbing complete.")
        run_payload["reviews"] = scrubbed_reviews

        # Save to a single file under Docs for persistent normalized reviews
        docs_reviews_path = os.path.join("Docs", "reviews.json")
        with open(docs_reviews_path, "w", encoding="utf-8") as f:
            json.dump(scrubbed_reviews, f, indent=2, ensure_ascii=False)
        click.echo(f"Normalized reviews successfully written to: {docs_reviews_path}")
        
        # 2. Clustering Phase
        click.echo("\n--- Phase 2: Semantic Clustering ---")
        click.echo("Running density-based review clustering...")
        clusterer = ReviewClusterer()
        clusters = clusterer.cluster_reviews(scrubbed_reviews, min_cluster_size=2)
        
        # Extract metadata
        noise_size = 0
        total_clusters = 0
        for cid, details in clusters.items():
            if details.get("is_noise", False):
                noise_size = details.get("size", 0)
            else:
                total_clusters += 1
                
        click.echo(f"Clustering complete. Identified {total_clusters} semantic clusters. Discarded {noise_size} noise reviews.")
        run_payload["stats"]["total_clusters"] = total_clusters
        run_payload["stats"]["noise_reviews_discarded"] = noise_size
        
        # 3. Summarization & GQV Phase
        click.echo("\n--- Phase 3: AI Summarization & Quote Grounding ---")
        click.echo("Generating report and validating quotes (GQV)...")
        summarizer = GeminiSummarizer()
        validator = GroundedQuoteValidator()
        
        report = validator.get_validated_report(summarizer, clusters, scrubbed_reviews, max_retries=3)
        click.echo("Quote grounding completed successfully. 100% compliance met.")
        run_payload["report"] = report
        run_payload["stats"]["gqv_attempts"] = validator.last_run_attempts
        
        # Format markdown for Google Doc upload
        report_markdown = format_report_markdown(report, product.upper(), iso_week)
        
        # 4. Workspace Delivery Phase
        click.echo("\n--- Phase 4: Google Workspace Delivery ---")
        if dry_run:
            click.echo("Dry-run enabled. Skipping Workspace delivery. Local markdown output:")
            click.echo(report_markdown[:500] + "\n... [truncated] ...")
            run_payload["stats"]["status"] = "dry_run_success"
        else:
            # Load target doc ID and MCP server base URL from environment
            doc_id = os.environ.get("GOOGLE_DOC_ID")
            if not doc_id:
                raise ValueError("GOOGLE_DOC_ID environment variable is missing!")
                
            mcp_server_url = os.environ.get("GOOGLE_MCP_SERVER_URL", "https://my-mcp-server-production-1f3f.up.railway.app").strip().rstrip("/")
            recipient_list = [r.strip() for r in recipients.split(",") if r.strip()]
            
            # 4.1. Call Docs Tool via Deployed Python MCP Server
            click.echo(f"Calling Google Docs Tool at {mcp_server_url}/append_to_doc...")
            doc_api_url = f"{mcp_server_url}/append_to_doc"
            
            import urllib.request
            
            doc_payload = {
                "doc_id": doc_id,
                "content": report_markdown
            }
            
            req_doc = urllib.request.Request(
                doc_api_url,
                data=json.dumps(doc_payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req_doc) as response:
                doc_response = json.loads(response.read().decode('utf-8'))
            
            click.echo("Google Doc updated successfully with formatting.")
            run_payload["delivery"]["google_doc"] = doc_response
            
            # 4.2. Call Gmail Tool via Deployed Python MCP Server
            click.echo(f"Calling Gmail Tool at {mcp_server_url}/create_email_draft...")
            gmail_api_url = f"{mcp_server_url}/create_email_draft"
            
            subject = f"[{product.upper()}] Weekly Review Pulse — {iso_week}"
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            
            # Generate email body with top themes
            top_themes = ", ".join([theme.get("theme_name", "") for theme in report.get("themes", [])][:3])
            email_body = (
                f"Hello Team,\n\n"
                f"Here is the Weekly Review Pulse for {product.upper()} (ISO Week: {iso_week}).\n\n"
                f"Top Themes Identified: {top_themes}\n\n"
                f"You can view the full formatted report directly in Google Docs here:\n"
                f"{doc_url}\n\n"
                f"Best regards,\n"
                f"Impullse Analytics System"
            )
            
            delivered_recipients = []
            skipped_recipients = []
            for recipient in recipient_list:
                # Task 5.1: Idempotency check before calling Gmail tool
                if check_already_delivered(product, iso_week, recipient):
                    click.echo(f"Skipping teaser email for {recipient} (already delivered for week {iso_week}).")
                    skipped_recipients.append(recipient)
                    continue
                    
                gmail_payload = {
                    "to": recipient,
                    "subject": subject,
                    "body": email_body
                }
                
                req_gmail = urllib.request.Request(
                    gmail_api_url,
                    data=json.dumps(gmail_payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                
                with urllib.request.urlopen(req_gmail) as response:
                    gmail_response = json.loads(response.read().decode('utf-8'))
                    
                click.echo(f"Gmail draft created successfully for {recipient}.")
                # Record delivery to log
                record_delivery(product, iso_week, recipient)
                delivered_recipients.append(recipient)
                
            run_payload["delivery"]["gmail"] = {
                "status": "success",
                "delivered": delivered_recipients,
                "skipped": skipped_recipients
            }
            run_payload["stats"]["status"] = "completed_success"

            
    except Exception as e:
        click.echo(f"Run encountered a fatal error: {str(e)}", err=True)
        run_payload["stats"]["status"] = "failed"
        run_payload["errors"].append(str(e))
        
    finally:
        # Write audit log
        save_run_log(run_log_path, run_payload)
        click.echo(f"Run log audit successfully written to: {run_log_path}")
        lock.release()

def check_already_delivered(product: str, iso_week: str, recipient: str, history_path: str = None) -> bool:
    if history_path is None:
        history_path = os.path.join("logs", "delivery_history.json")
    if not os.path.exists(history_path):
        return False
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
            if not isinstance(history, list):
                return False
            for record in history:
                if (record.get("product") == product and 
                    record.get("iso_week") == iso_week and 
                    record.get("recipient") == recipient and 
                    record.get("action") == "email_sent"):
                    return True
    except Exception as e:
        logger.warning(f"Error reading delivery history: {str(e)}")
    return False

def record_delivery(product: str, iso_week: str, recipient: str, history_path: str = None):
    if history_path is None:
        history_path = os.path.join("logs", "delivery_history.json")
    history = []
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []
        except Exception as e:
            logger.warning(f"Error reading delivery history for write: {str(e)}")
            history = []
    
    history.append({
        "product": product,
        "iso_week": iso_week,
        "recipient": recipient,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "action": "email_sent"
    })
    
    try:
        os.makedirs(os.path.dirname(history_path), exist_ok=True)
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error writing delivery history: {str(e)}")

def format_report_markdown(report: Dict[str, Any], product: str, iso_week: str) -> str:
    """
    Helper function to render a clean, standard markdown representation of the LLM report.
    """
    lines = []
    lines.append(f"### **Weekly Review Pulse — {product}**")
    lines.append(f"* **Period:** Rolling 8-12 weeks (Target Week: {iso_week})")
    lines.append(f"* **Report Date:** {datetime.date.today().strftime('%B %d, %Y')}")
    lines.append("")
    lines.append("#### **Top Semantic Themes & Insights**")
    lines.append("")
    
    for idx, theme in enumerate(report.get("themes", [])):
        lines.append(f"{idx + 1}. **{theme.get('theme_name', '')}**")
        lines.append(f"   * *Summary:* {theme.get('summary', '')}")
        
        # Render verbatim quotes
        lines.append("   * *Verbatim User Quotes:*")
        for quote in theme.get("quotes", []):
            lines.append(f"     - *\"{quote}\"*")
            
        # Render action ideas
        lines.append("   * *Actionable Product/Support Recommendations:*")
        for idea in theme.get("action_ideas", []):
            lines.append(f"     - {idea}")
        lines.append("")
        
    return "\n".join(lines)

def save_run_log(path: str, payload: Dict[str, Any]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    cli()
