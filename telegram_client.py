# telegram_client.py — Sends alerts and status updates to a Telegram Bot.

import os
import logging
import requests
from typing import Optional

logger = logging.getLogger("telegram")

def send_message(text: str) -> bool:
    """
    Sends a generic text message to the configured Telegram chat.
    Returns True if successful, False otherwise.
    """
    token = os.getenv("TELEGRAM_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    
    if not token or not chat_id:
        logger.warning("Telegram credentials missing in .env. Skipping notification.")
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            logger.error("Telegram API Error (%s): %s", response.status_code, response.text)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error("Failed to send Telegram message: %s", e)
        return False

def send_opportunity_alert(opp: dict) -> None:
    """
    Formats and sends a high-priority opportunity alert.
    """
    # Header
    msg = f"⚽ *MINUTEBID OPPORTUNITY FOUND!*\n\n"
    
    # Match Info
    msg += f"🏟 *Match:* {opp.get('event_title', 'Unknown')}\n"
    msg += f"⏱ *Minute:* {opp.get('minute', '?')}\n"
    msg += f"📊 *Outcome:* {opp.get('outcome_name', 'Yes')}\n\n"
    
    # Price Info
    poly_prob = opp.get('implied_prob', 0) * 100
    ref_prob = opp.get('ref_implied_prob', 0) * 100
    edge = opp.get('edge', 0) * 100
    
    msg += f"📍 *Polymarket:* {poly_prob:.1f}% (${opp.get('price', 0):.2f})\n"
    msg += f"📈 *Reference:* {ref_prob:.1f}%\n"
    msg += f"🔥 *EDGE:* {edge:.1f}%\n\n"
    
    # Link
    event_id = opp.get('event_id')
    if event_id:
        # Note: This is an example Gamma URL structure, adjust if needed
        link = f"https://polymarket.com/event/{event_id}"
        msg += f"[View on Polymarket]({link})"
        
    send_message(msg)

def send_status_update(status: str) -> None:
    """
    Sends a simple status heartbeat to Telegram.
    """
    msg = f"🤖 *Status Update:* {status}"
    send_message(msg)
