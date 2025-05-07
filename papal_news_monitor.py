import requests
from bs4 import BeautifulSoup
import time
import json
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import random
import re
import unicodedata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Load environment variables
# Look for .env file in the current directory
load_dotenv(dotenv_path=".env")
logger.info("Loading environment variables from .env file")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS", "").split(",")

if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
    raise ValueError("TELEGRAM_BOT_TOKEN is required")

if not CHAT_IDS or CHAT_IDS[0] == "":
    logger.error("TELEGRAM_CHAT_IDS not found in environment variables")
    raise ValueError("TELEGRAM_CHAT_IDS is required")

# News source configuration
INTERVAL = int(os.getenv("SCAN_INTERVAL", "60"))  # Default: scan every 60 seconds
logger.info(f"Scan interval set to {INTERVAL} seconds")

KEYWORDS = [
    "nuovo papa",
    "eletto papa",
    "nuovo pontefice",
    "diventa papa",
    "nominato pontefice",
    "succede a francesco",
    "proclamato papa",
    "salirà al soglio pontificio",
    "fumata bianca",
]
SITES = [
    "https://www.repubblica.it/",
    "https://www.corriere.it/",
    "https://www.lastampa.it/",
    "https://www.ilgiornale.it/",
    "https://www.ilsole24ore.com/",
    "https://www.ilfattoquotidiano.it/",
    "https://tg24.sky.it/",
    "https://www.tgcom24.mediaset.it/",
    "https://www.rainews.it/",
    "https://www.adnkronos.com/",
    "https://www.ansa.it/",
    "https://www.vaticannews.va/it.html",
    "https://www.avvenire.it/",
    "https://www.reuters.com/",
    "https://apnews.com/",
]

# Load candidates
try:
    with open("candidati.json", "r", encoding="utf-8") as f:
        candidati = json.load(f)
    candidate_names = [f"{x['nome']} {x['cognome']}" for x in candidati]
    logger.info(f"Loaded {len(candidate_names)} candidates")
except Exception as e:
    logger.error(f"Failed to load candidates: {e}")
    candidati = []
    candidate_names = []

# Load token addresses
token_data = []
try:
    with open("token_addresses.json", "r", encoding="utf-8") as f:
        token_data = json.load(f)
    logger.info(f"Loaded {len(token_data)} token addresses")
except Exception as e:
    logger.error(f"Failed to load token addresses: {e}")

# Track articles we've already seen
seen_articles = set()
# Store matched articles with candidate names
matches_history = {}


def find_token_address(candidate_name):
    """Find token address for a candidate name"""
    for entry in token_data:
        if candidate_name == entry["name"] or candidate_name == entry["full_name"]:
            return entry["token_address"]
    return None


def fetch_site(url):
    """Fetch website content with proper headers"""
    try:
        # Use different user agents to avoid being blocked
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        ]

        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.text
        else:
            logger.warning(f"Status {res.status_code} from {url}")
    except Exception as e:
        logger.error(f"Failed to access {url}: {e}")
    return ""


def extract_articles(html, site_url):
    """Extract articles with their URLs and content"""
    soup = BeautifulSoup(html, "html.parser")
    articles = []

    # Look for article tags
    article_tags = soup.find_all(["article", "div", "section"])

    for article in article_tags:
        # Try to find headline/title
        headline_tag = article.find(["h1", "h2", "h3", "h4"])
        if not headline_tag:
            continue

        headline = headline_tag.get_text(strip=True)
        if not headline:
            continue

        # Find link if any
        link = None
        link_tag = headline_tag.find("a") or article.find("a")
        if link_tag and link_tag.get("href"):
            link = link_tag["href"]
            # Handle relative URLs
            if link.startswith("/"):
                # Extract domain from site_url
                if "://" in site_url:
                    domain = (
                        site_url.split("://", 1)[0]
                        + "://"
                        + site_url.split("://", 1)[1].split("/", 1)[0]
                    )
                    link = domain + link
                else:
                    link = site_url.rstrip("/") + link

        # Extract content
        content = article.get_text(strip=True)

        # Add to articles if we have at least headline and content
        article_id = f"{site_url}::{headline}"
        if article_id not in seen_articles:
            articles.append(
                {
                    "id": article_id,
                    "headline": headline,
                    "content": content,
                    "link": link,
                    "source": site_url,
                    "type": "article",
                }
            )
            seen_articles.add(article_id)

    return articles


def normalize_text(text):
    """Normalize text by removing accents and non-alphanumeric characters"""
    # Normalize Unicode characters
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    # Convert to lowercase and remove extra spaces
    text = " ".join(text.lower().split())
    return text


def search_candidate_mentions(items):
    """Search for candidate mentions in articles or tweets with improved accuracy"""
    results = {}

    # Define more specific election indicator patterns
    ELECTION_PATTERNS = [
        r"(nuovo|eletto|proclamato) papa [^.!?]*\b{}\b",  # "nuovo papa [text] Name"
        r"\b{}\b[^.!?]* (eletto|scelto|diventa|è il nuovo|nominato) papa",  # "Name [text] eletto papa"
        r"fumata bianca[^.!?]*\b{}\b",  # "fumata bianca [text] Name"
        r"\b{}\b[^.!?]*fumata bianca",  # "Name [text] fumata bianca"
        r"(conclave|cardinali) [^.!?]*\b{}\b[^.!?]*(eletto|scelto|nominato)",  # "conclave [text] Name [text] eletto"
        r"successore di (papa |francesco)[^.!?]*\b{}\b",  # "successore di francesco [text] Name"
        r"\b{}\b[^.!?]*successore di (papa |francesco)",  # "Name [text] successore di francesco"
    ]

    # Keywords that strongly indicate an actual election (not just a mention)
    STRONG_INDICATORS = [
        "fumata bianca",
        "habemus papam",
        "è il nuovo papa",
        "nuovo pontefice",
        "eletto papa",
        "sarà il prossimo papa",
        "è stato eletto",
        "succederà a francesco",
    ]

    # Normalize candidate names for comparison
    normalized_candidate_names = [
        (name, normalize_text(name)) for name in candidate_names
    ]

    for item in items:
        # Normalize headline and content
        headline_norm = normalize_text(item["headline"])
        content_norm = normalize_text(item["content"])
        item_content_norm = headline_norm + " " + content_norm

        # First check for strong indicators to reduce processing
        if not any(
            indicator.lower() in item_content_norm
            for indicator in map(normalize_text, STRONG_INDICATORS)
        ):
            continue

        # For each candidate, check for specific election patterns
        for original_name, name_norm in normalized_candidate_names:
            # Check for proximity patterns with candidate name
            has_election_pattern = False
            for pattern in ELECTION_PATTERNS:
                # Insert name into pattern and check
                formatted_pattern = pattern.format(name_norm)
                if re.search(formatted_pattern, item_content_norm):
                    has_election_pattern = True
                    break

            # Add to results if specific pattern found
            if has_election_pattern:
                # Calculate confidence score based on headline (higher weight) and content
                score = 0

                # Check headline separately (higher importance)
                if name_norm in headline_norm and any(
                    normalize_text(indicator) in headline_norm
                    for indicator in STRONG_INDICATORS
                ):
                    score += 5  # Higher score for headline matches

                # Count strong indicators in the content
                for indicator in STRONG_INDICATORS:
                    if normalize_text(indicator) in item_content_norm:
                        score += 1

                # Only include if score is high enough (threshold can be adjusted)
                if score >= 2:
                    if original_name not in results:
                        results[original_name] = []

                    # Add the confidence score to the item
                    item_with_score = item.copy()
                    item_with_score["confidence_score"] = score
                    results[original_name].append(item_with_score)

    return results


def send_telegram_notification(message):
    """Send notification to Telegram"""
    for chat_id in CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
            response = requests.post(url, data=payload)
            if response.status_code != 200:
                logger.error(f"Failed to send Telegram message: {response.text}")
            else:
                logger.info(f"Notification sent to {chat_id}")
        except Exception as e:
            logger.error(f"Error sending Telegram message to {chat_id}: {e}")


def format_item_message(candidate_name, items, token_address=None):
    """Format a nice message with article details"""
    rome_tz = pytz.timezone("Europe/Rome")
    current_time = datetime.now(rome_tz).strftime("%d/%m/%Y %H:%M:%S")

    # Calculate average confidence score
    avg_confidence = (
        sum(item.get("confidence_score", 0) for item in items) / len(items)
        if items
        else 0
    )
    confidence_emoji = (
        "🟢" if avg_confidence >= 5 else "🟡" if avg_confidence >= 3 else "🔴"
    )

    message = f"{confidence_emoji} <b>POSSIBILE ELEZIONE:</b> Menzioni di <b>{candidate_name}</b> trovate!\n"
    message += f"⏰ Data e ora: {current_time}\n"
    message += f"🔍 <b>Affidabilità:</b> {confidence_emoji} {avg_confidence:.1f}/10\n\n"

    # Add a disclaimer for low confidence scores
    if avg_confidence < 3:
        message += "⚠️ <b>ATTENZIONE:</b> Bassa affidabilità della notizia. Potrebbero essere solo menzioni casuali.\n\n"

    articles = [item for item in items if item["type"] == "article"]

    # Format articles
    if articles:
        message += f"📰 <b>ARTICOLI ({len(articles)}):</b>\n\n"
        for i, article in enumerate(articles, 1):
            score = article.get("confidence_score", 0)
            score_emoji = "🟢" if score >= 5 else "🟡" if score >= 3 else "🔴"

            message += f"<b>Articolo {i}:</b> {score_emoji} {score}/10\n"
            message += f"📝 <b>Titolo:</b> {article['headline']}\n"

            # Add excerpt of content (first 150 chars)
            excerpt = (
                article["content"][:150] + "..."
                if len(article["content"]) > 150
                else article["content"]
            )
            message += f"💬 <b>Estratto:</b> {excerpt}\n"

            # Add source and link
            message += f"🌐 <b>Fonte:</b> {article['source']}\n"
            if article["link"]:
                message += f"🔗 <b>Link:</b> {article['link']}\n"

            message += "\n"

    # Add token info if available (only for high confidence)
    if token_address and avg_confidence >= 3:
        message += f"🪙 <b>TOKEN ADDRESS:</b> <code>{token_address}</code>\n\n"
        message += f"🔄 <b>PER ACQUISTARE:</b> /buy {token_address} [amount]\n\n"

    message += "⚠️ Verificare immediatamente queste informazioni!"
    return message


def main_loop():
    """Main monitoring loop"""
    logger.info("Starting Papal News Monitor")

    while True:
        try:
            logger.info(f"Scanning {len(SITES)} news sources...")
            all_items = []

            # Fetch and process each site
            for site in SITES:
                try:
                    logger.info(f"Checking website: {site}")
                    html = fetch_site(site)
                    if html:
                        site_articles = extract_articles(html, site)
                        logger.info(f"Found {len(site_articles)} articles on {site}")
                        all_items.extend(site_articles)
                    else:
                        logger.warning(f"No content retrieved from {site}")
                    # Be nice to servers - add small delay between requests
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"Error processing {site}: {e}")

            # Search for candidate mentions
            logger.info(
                f"Searching for candidates in {len(all_items)} items (articles)"
            )
            matches = search_candidate_mentions(all_items)

            # Handle matches
            if matches:
                logger.info(f"Found mentions for {len(matches)} candidates")

                for candidate, items in matches.items():
                    # Skip if no items
                    if not items:
                        continue

                    # Calculate average confidence score for this candidate
                    avg_confidence = sum(
                        item.get("confidence_score", 0) for item in items
                    ) / len(items)
                    logger.info(
                        f"Candidate {candidate} has average confidence score: {avg_confidence:.1f}"
                    )

                    # Check if this is a new match or has new items
                    is_new_match = candidate not in matches_history

                    if is_new_match:
                        matches_history[candidate] = set()

                    # Find only new items
                    new_items = []
                    for item in items:
                        if item["id"] not in matches_history[candidate]:
                            matches_history[candidate].add(item["id"])
                            new_items.append(item)

                    # Skip if no new items
                    if not new_items:
                        continue

                    # Recalculate confidence with only new items
                    if new_items:
                        new_avg_confidence = sum(
                            item.get("confidence_score", 0) for item in new_items
                        ) / len(new_items)
                        logger.info(
                            f"New items for {candidate} have confidence: {new_avg_confidence:.1f}"
                        )
                    else:
                        new_avg_confidence = 0

                    # Check if there's a token address for this candidate
                    token_address = find_token_address(candidate)

                    # Send notification with token info if available
                    message = format_item_message(candidate, new_items, token_address)

                    # Only send notification if confidence is above minimum threshold
                    min_notification_threshold = (
                        2  # Minimum threshold to send any notification
                    )
                    if new_avg_confidence >= min_notification_threshold:
                        send_telegram_notification(message)
                        logger.info(
                            f"Sent notification for {candidate} with {len(new_items)} new items (confidence: {new_avg_confidence:.1f})"
                        )
                    else:
                        logger.info(
                            f"Skipping notification for {candidate} due to very low confidence ({new_avg_confidence:.1f})"
                        )
            else:
                logger.info("No candidate mentions found in this scan")

            # Wait for next scan
            logger.info(f"Waiting {INTERVAL} seconds before next scan")
            time.sleep(INTERVAL)

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            # Don't crash on errors, wait a bit and continue
            time.sleep(60)


if __name__ == "__main__":
    main_loop()
