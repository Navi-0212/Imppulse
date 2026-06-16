import json
import random
import datetime
import os
import re
from typing import Dict, Any, List
from src.ingestion.normalize import normalize_review
from src.ingestion.filter import ReviewFilter
from src.ingestion.scrub import PIIScrubber

# List of common Indian names for authors
AUTHORS = [
    "Aarav", "Priya", "Amit", "Rahul", "Neha", "Rohan", "Siddharth", "Ananya", "Vikram", "Sneha",
    "Rajesh", "Suresh", "Lakshmi", "Vijay", "Ramesh", "Kavita", "Aditi", "Manish", "Divya", "Sanjay",
    "Deepak", "Sunita", "Harish", "Pooja", "Arjun", "Kiran", "Nikhil", "Shalini", "Alok", "Ritu",
    "Manoj", "Jyoti", "Pradeep", "Aarti", "Ashok", "Geeta", "Vinay", "Meera", "Sandeep", "Swati",
    "Anil", "Rekha", "Abhishek", "Preeti", "Kartik", "Shruti", "Varun", "Komal", "Dev", "Payal"
]

# Themes & Phrases mapping to ratings
THEMES = {
    "trading": {
        "starts": [
            "The charting features on Groww are",
            "Stock trading execution is",
            "Using the technical analysis tools is",
            "Buying intraday options during peak hours is",
            "The candlestick charts are",
            "Placing orders in the F&O segment is",
            "The live stock price feed is",
            "Reviewing my stock portfolio dashboard is"
        ],
        "middles_bad": [
            "very slow and lagged. I couldn't buy at my desired price",
            "freezing constantly, causing heavy losses in my active positions",
            "not updating fast enough compared to other discount brokers",
            "crashing during volatile market movements, which is unacceptable",
            "showing wrong charts and delayed candles that misleads traders"
        ],
        "middles_good": [
            "responsive and easy to customize with multiple technical indicators",
            "really helpful for analyzing market trends in real time",
            "the best and cleanest interface I have seen on any trading app",
            "extremely fast, orders get executed in milliseconds",
            "very intuitive, making stock purchasing super straightforward"
        ],
        "ends_bad": [
            "Please fix this chart latency issue as soon as possible.",
            "I lost money because the order took two minutes to place.",
            "The platform is completely useless for active intraday traders.",
            "They must optimize their servers for 9:15 AM market opening peak hours.",
            "Extremely disappointed with the constant connection drops."
        ],
        "ends_good": [
            "Highly recommended for people who want to trade stocks.",
            "The UI is clean and makes stock market analysis simple.",
            "The charts need more indicators like supertrend and VWAP but it is good.",
            "Excellent dashboard that lists all active holdings nicely.",
            "Really happy with the low brokerage charges and fast execution."
        ]
    },
    "sip_mf": {
        "starts": [
            "My monthly mutual fund SIP transaction",
            "Setting up the auto-pay bank mandate was",
            "Investing in direct mutual funds through this app is",
            "Redeeming my mutual fund units from the dashboard",
            "The SIP payment option via Google Pay",
            "Setting up a new automated SIP was",
            "Tracking mutual fund returns on the dashboard is",
            "The unit allocation process for mutual funds is"
        ],
        "middles_bad": [
            "failed multiple times but money was debited from my bank account",
            "stuck in progress for the last four working days with no update",
            "showing a wrong dashboard value which is highly confusing and risky",
            "rejected by the payment gateway but the amount is not yet refunded",
            "not reflecting in my portfolio even after 5 days of debit"
        ],
        "middles_good": [
            "incredibly smooth and completed in just a few clicks",
            "very straightforward and simple compared to older platforms",
            "seamless, with units credited exactly on time",
            "extremely easy to pause or modify whenever needed",
            "very clear with no hidden charges, completely transparent"
        ],
        "ends_bad": [
            "Please refund my amount immediately to my bank account.",
            "I am still waiting for the units to be allocated to my portfolio.",
            "Support team needs to resolve this pending transaction issue.",
            "This delay is unacceptable for financial apps handling public money.",
            "I am worried about my hard-earned money being stuck in limbo."
        ],
        "ends_good": [
            "This is the best app for automated monthly investing.",
            "Love the dashboard representation of total returns and gains.",
            "Kudos for offering completely free direct mutual fund investment options.",
            "Everything is organized perfectly, making SIP tracking a breeze.",
            "Highly recommend this to anyone starting their savings journey."
        ]
    },
    "support": {
        "starts": [
            "The customer service support on this platform is",
            "Trying to resolve my pending issue with help desk is",
            "The automated chat bot in the help center is",
            "Raising a support ticket for my KYC issue is",
            "Customer care representatives are",
            "The ticketing system for resolving app issues is",
            "Reaching out to customer support on Groww is",
            "Their email support responsiveness is"
        ],
        "middles_bad": [
            "extremely slow and unresponsive. No one replies to tickets for days",
            "repeating generic automated answers without understanding the actual problem",
            "taking days to reply and closing tickets without proper resolution",
            "not helpful at all. I have been waiting for weeks to hear back",
            "absolutely useless. There is no call support option to talk to human agents"
        ],
        "middles_good": [
            "surprisingly fast and resolved my query within an hour",
            "helpful and guided me step-by-step through the process",
            "decent, though it takes some clicks to reach a real representative",
            "polite and quickly updated my bank account details",
            "responsive enough to solve my login issues on the same day"
        ],
        "ends_bad": [
            "My support ticket reference is pending for a week. Pathetic experience!",
            "I will close my account and move to another platform if this continues.",
            "They need to hire human agents instead of relying on broken bots.",
            "Still waiting for a response on my registered email address.",
            "Extremely frustrated with the lack of direct communication channels."
        ],
        "ends_good": [
            "Kudos to the team for resolving issues quickly.",
            "Happy with the resolution provided by customer support team.",
            "Though it took some time, they finally fixed my bank account link.",
            "Good support overall, keep up the helpful attitude.",
            "The help center contains answers to almost all common questions."
        ]
    },
    "kyc": {
        "starts": [
            "My KYC verification process is",
            "Account opening on this app was",
            "Linking my savings bank account was",
            "Uploading documents for options activation is",
            "The onboarding journey on Groww is",
            "Submitting PAN card details for verification is",
            "Re-verifying my address details through Digilocker is",
            "My account activation status is"
        ],
        "middles_bad": [
            "stuck for the last one week with error code 504 on the portal",
            "rejected repeatedly without giving any clear reasons or comments",
            "failing during the Digilocker authentication step every single time",
            "taking forever to verify even though all documents are perfectly correct",
            "throwing random errors while uploading my bank account statement"
        ],
        "middles_good": [
            "completed within 10 minutes, super fast and paperless",
            "very user-friendly, especially for first-time retail investors",
            "highly appreciate the clean interface for uploading Aadhaar details",
            "approved in a single day, extremely hassle-free setup",
            "straightforward and guided very well by the in-app tooltips"
        ],
        "ends_bad": [
            "Please approve my account so I can start investing soon.",
            "The support team is not helping with document verification at all.",
            "Why is KYC verification so complicated on this app compared to others?",
            "Extremely annoying to see failed status repeatedly without explanation.",
            "I am unable to start my investment journey due to this delay."
        ],
        "ends_good": [
            "Kudos to the team for making onboarding so seamless!",
            "I will recommend this app to all my friends starting SIPs.",
            "Perfect onboarding flow, was active and ready to trade in no time.",
            "Great experience, paperless account opening is the future.",
            "Simple interface makes filling out profile details very quick."
        ]
    },
    "general": {
        "starts": [
            "Groww is the best investment application because of its",
            "I have been using this app for two years and the",
            "The overall user interface and layout of the app are",
            "Managing both stocks and mutual funds together is",
            "My experience with the application has been",
            "The app design and navigation options are",
            "Using this app daily for stock tracking is",
            "The dashboard presentation of all assets is"
        ],
        "middles_bad": [
            "getting worse with every new update. The design is too cluttered now",
            "showing occasional lags and random glitches during evening hours",
            "too slow to load my portfolio details on poor network connections",
            "confusing to navigate since they changed the bottom tab bar structure",
            "unstable on my phone, crash reports are sent frequently"
        ],
        "middles_good": [
            "sleek design, low brokerage fees, and clean, intuitive dashboard",
            "incredibly reliable and works perfectly fine on mobile data",
            "very easy to understand for beginners starting their finance journey",
            "highly convenient and saves a lot of tracking and transaction time",
            "exceptional and I have not faced any major bugs or issues so far"
        ],
        "ends_bad": [
            "Please revert to the older UI design which was much simpler.",
            "They need to fix these minor bugs to keep the app rating high.",
            "I hope they optimize the performance on older devices soon.",
            "The recent update ruined a perfectly good application.",
            "Needs improvement in stability and general performance speed."
        ],
        "ends_good": [
            "Keep up the excellent work, team Groww!",
            "Highly recommended for anyone looking to invest in India.",
            "It makes tracking returns extremely visual and clean.",
            "Five stars for the simplicity and transparency of charges.",
            "Looking forward to more features in future updates."
        ]
    }
}

# PII injection templates
PII_EMAILS = [
    "user123@gmail.com", "groww-user@yahoo.co.in", "investor.help@outlook.com", 
    "test_trader@hotmail.com", "client.support@groww-analytics.internal"
]
PII_PHONES = [
    "9876543210", "+91-9988776655", "022-24328847", 
    "+91 88776 65544", "7766554433"
]
PII_IDS = [
    "8847291", "109283", "55443322", 
    "987654", "1234567"
]

def generate_random_review_text(rating: int, inject_pii: bool = False) -> str:
    """
    Generates a realistic review text of at least 8 words, matching the rating sentiment.
    """
    # Pick a random category
    category = random.choice(["trading", "sip_mf", "support", "kyc", "general"])
    cat_data = THEMES[category]
    
    start = random.choice(cat_data["starts"])
    
    # Determine sentiment based on rating
    if rating <= 2:
        middle = random.choice(cat_data["middles_bad"])
        end = random.choice(cat_data["ends_bad"])
    elif rating == 3:
        # Mix good/bad or select neutral
        if random.random() < 0.5:
            middle = random.choice(cat_data["middles_bad"])
            end = random.choice(cat_data["ends_good"])
        else:
            middle = random.choice(cat_data["middles_good"])
            end = random.choice(cat_data["ends_bad"])
    else:
        middle = random.choice(cat_data["middles_good"])
        end = random.choice(cat_data["ends_good"])
        
    text = f"{start} {middle} {end}"
    
    # Inject PII if requested
    if inject_pii:
        pii_type = random.choice(["email", "phone", "id", "all"])
        if pii_type == "email":
            text += f" Contact me at {random.choice(PII_EMAILS)}."
        elif pii_type == "phone":
            text += f" Contact me on {random.choice(PII_PHONES)}."
        elif pii_type == "id":
            text += f" My support ticket ID is {random.choice(PII_IDS)}."
        else:
            text += f" Support ticket is {random.choice(PII_IDS)}, email is {random.choice(PII_EMAILS)}, phone is {random.choice(PII_PHONES)}."
            
    return text

def main():
    print("Generating ~2000 high-fidelity normalized, filtered, and scrubbed reviews...")
    
    # Setup instances
    filter_engine = ReviewFilter(min_word_count=8)
    scrubber_engine = PIIScrubber()
    
    target_count = 2000
    generated_reviews = []
    
    # Dates spanning the last 12 weeks
    now = datetime.datetime.now(datetime.timezone.utc)
    start_date = now - datetime.timedelta(weeks=12)
    delta_seconds = int((now - start_date).total_seconds())
    
    # Loop until we have enough reviews that PASS the filter
    attempt = 0
    last_print = 0
    while len(generated_reviews) < target_count:
        attempt += 1
        # Distribute ratings: 50% positive (4-5), 35% negative (1-2), 15% neutral (3)
        rand_val = random.random()
        if rand_val < 0.35:
            rating = random.choice([1, 2])
        elif rand_val < 0.50:
            rating = 3
        else:
            rating = random.choice([4, 5])
            
        # Inject PII in roughly 3% of the reviews
        inject_pii = random.random() < 0.03
        
        raw_text = generate_random_review_text(rating, inject_pii=inject_pii)
        
        # Pick a random date in the last 12 weeks
        random_seconds = random.randint(0, delta_seconds)
        review_date = start_date + datetime.timedelta(seconds=random_seconds)
        
        platform = "android" if random.random() < 0.8 else "ios"
        author = random.choice(AUTHORS)
        review_id = f"gp_gen_{attempt}_{review_date.strftime('%Y%m%d%H%M%S')}"
        
        # Construct raw dict
        raw_review = {
            "id": review_id,
            "author": author,
            "title": "",
            "text": raw_text,
            "rating": rating,
            "date": review_date.isoformat(),
            "platform": platform
        }
        
        # 1. Normalize
        normalized = normalize_review(raw_review)
        
        # 2. Filter
        if not filter_engine.should_keep(normalized["text"]):
            continue
            
        # 3. Scrub PII
        normalized["text"] = scrubber_engine.scrub_text(normalized["text"])
        
        generated_reviews.append(normalized)
        
        # Print progress
        current_count = len(generated_reviews)
        if current_count % 500 == 0 and current_count != last_print:
            print(f"Generated {current_count}/{target_count} reviews...")
            last_print = current_count
        
    print(f"Generation successful. Generated {len(generated_reviews)} reviews (filtered and scrubbed).")
    
    # Sort reviews by date descending (most recent first)
    generated_reviews.sort(key=lambda x: x["date"], reverse=True)
    
    # Write to Docs/reviews.json
    docs_reviews_path = os.path.join("Docs", "reviews.json")
    os.makedirs(os.path.dirname(docs_reviews_path), exist_ok=True)
    
    with open(docs_reviews_path, "w", encoding="utf-8") as f:
        json.dump(generated_reviews, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully wrote {len(generated_reviews)} reviews to {docs_reviews_path}")

if __name__ == "__main__":
    main()
