import re
import logging

logger = logging.getLogger(__name__)

# Compile regex fallbacks for standard PII patterns
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_REGEX = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
# Matches any sequence of digits greater than or equal to 5 digits (potential account/user IDs, ticket numbers)
ID_REGEX = re.compile(r'\b\d{5,}\b')

class PIIScrubber:
    def __init__(self):
        self.presidio_available = False
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            self.presidio_available = True
            logger.info("Microsoft Presidio initialized successfully.")
        except Exception as e:
            logger.warning(
                f"Could not load Microsoft Presidio: {str(e)}. "
                "Presidio requires SpaCy models. Falling back to robust regex-based PII scrubbing."
            )

    def scrub_text(self, text: str) -> str:
        """
        Scrubs PII (Emails, Phone Numbers, and numerical IDs > 4 digits) from the input text.
        Uses Microsoft Presidio if available, otherwise falls back to compiled regex engines.
        """
        if not text:
            return ""

        if self.presidio_available:
            try:
                # Analyze text for standard entities
                analysis_results = self.analyzer.analyze(
                    text=text,
                    language="en",
                    entities=["EMAIL_ADDRESS", "PHONE_NUMBER"]
                )
                
                # Anonymize using custom placeholders
                from presidio_anonymizer.entities import OperatorConfig
                operators = {
                    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
                    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PHONE]"})
                }
                
                anonymized_result = self.anonymizer.anonymize(
                    text=text,
                    analyzer_results=analysis_results,
                    operators=operators
                )
                
                text = anonymized_result.text
            except Exception as e:
                logger.error(f"Presidio anonymization failed: {str(e)}. Falling back to regex.")

        # Post-process or fallback with Regex (always scrub > 4 digits as IDs, and fallback check emails/phones)
        text = EMAIL_REGEX.sub("[EMAIL]", text)
        text = PHONE_REGEX.sub("[PHONE]", text)
        text = ID_REGEX.sub("[ID]", text)
        
        return text

    def scrub_reviews(self, reviews: list) -> list:
        """
        Processes a list of reviews and scrubs PII from their text fields in-place.
        """
        for review in reviews:
            review["text"] = self.scrub_text(review.get("text", ""))
            review["title"] = self.scrub_text(review.get("title", ""))
        return reviews
