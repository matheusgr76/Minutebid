# telegram_client.py — Sends alerts and status updates to a Telegram Bot.

import os
import logging
import requests
from typing import Optional

logger = logging.getLogger("telegram")

def send_message(text: str) -> Optional[int]:
    """
    Sends a generic text message to the configured Telegram chat.
    Returns the message_id if successful, None otherwise.
    """
    token = os.getenv("TELEGRAM_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    
    if not token or not chat_id:
        logger.warning("Telegram credentials missing in .env. Skipping notification.")
        return None
        
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
        return response.json().get("result", {}).get("message_id")
    except Exception as e:
        logger.error("Failed to send Telegram message: %s", e)
        return None

def edit_message(text: str, message_id: int) -> bool:
    """
    Edits an existing Telegram message.
    """
    token = os.getenv("TELEGRAM_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    
    if not token or not chat_id:
        return False
        
    url = f"https://api.telegram.org/bot{token}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            # If the content is the same, Telegram returns 400 "message is not modified"
            if "message is not modified" in response.text:
                return True
            logger.error("Telegram API Error (%s): %s", response.status_code, response.text)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error("Failed to edit Telegram message: %s", e)
        return False

def send_opportunity_alert(opp: dict) -> None:
    """
    Formats and sends a bet signal alert based on Polymarket price threshold.
    """
    poly_prob = opp.get('poly_prob', 0) * 100
    msg = f"⚽ *BET SIGNAL*\n\n"
    msg += f"🏟 *Match:* {opp.get('match', 'Unknown')}\n"
    msg += f"⏱ *Minute:* ~{opp.get('minute', '?')}\n\n"
    msg += f"🔥 *Outcome:* {opp.get('outcome', '?')}\n"
    msg += f"📍 *Polymarket:* {poly_prob:.1f}¢\n"
    msg += f"\n[View on Polymarket]({opp.get('market_url', 'https://polymarket.com')})"
    send_message(msg)

def send_status_update(status: str) -> None:
    """
    Sends a simple status heartbeat to Telegram.
    """
    msg = f"🤖 *Status Update:* {status}"
    send_message(msg)

def send_order_confirmation(opp: dict, order_resp: dict, stake_usdc: float) -> None:
    """
    Sends a bet confirmation after a CLOB order is successfully placed.
    """
    poly_prob = opp.get("poly_prob", 0) * 100
    order_id = order_resp.get("orderID", "unknown") if isinstance(order_resp, dict) else str(order_resp)
    msg = f"✅ *BET PLACED*\n\n"
    msg += f"🏟 *Match:* {opp.get('match', 'Unknown')}\n"
    msg += f"⏱ *Minute:* ~{opp.get('minute', '?')}\n\n"
    msg += f"🎯 *Outcome:* {opp.get('outcome', '?')}\n"
    msg += f"💰 *Stake:* ${stake_usdc:.2f} @ {poly_prob:.1f}¢\n"
    msg += f"🔑 *Order ID:* `{order_id}`\n"
    msg += f"\n[View on Polymarket]({opp.get('market_url', 'https://polymarket.com')})"
    send_message(msg)

def send_order_failure(opp: dict, reason: str) -> None:
    """
    Sends an alert when a CLOB order fails so the operator can investigate.
    """
    msg = f"❌ *ORDER FAILED*\n\n"
    msg += f"🏟 *Match:* {opp.get('match', 'Unknown')}\n"
    msg += f"🎯 *Outcome:* {opp.get('outcome', '?')}\n"
    msg += f"⚠️ *Reason:* `{reason}`"
    send_message(msg)

DASHBOARD_FILE = ".dashboard_msg_id"

def _get_last_dashboard_id() -> Optional[int]:
    if os.path.exists(DASHBOARD_FILE):
        try:
            with open(DASHBOARD_FILE, "r") as f:
                return int(f.read().strip())
        except:
            pass
    return None

def _save_dashboard_id(msg_id: int):
    with open(DASHBOARD_FILE, "w") as f:
        f.write(str(msg_id))

def update_scheduler_dashboard(runs: list, force_new: bool = False) -> None:
    """
    Sends or updates a single dashboard message with the current schedule and countdowns.
    Limits to the next 15 games to avoid Telegram's 4096 character limit.
    If force_new is True, skips editing the previous message and sends a fresh one.
    """
    from datetime import datetime, timezone, timedelta
    
    now = datetime.now(timezone.utc)
    MAX_GAMES_DISPLAYED = 15
    
    msg = "📅 *MONITORED GAMES DASHBOARD*\n"
    # Convert to Brasilia Time (UTC-3)
    br_now = now.astimezone(timezone(timedelta(hours=-3)))
    msg += f"Last updated: {br_now.strftime('%H:%M:%S')} (UTC-3)\n"
    msg += f"Total games monitored today: {len(runs)}\n\n"
    
    if not runs:
        msg += "No games currently being monitored. 😴"
    else:
        # Show only the next N games
        display_runs = runs[:MAX_GAMES_DISPLAYED]
        
        for run in display_runs:
            wakeup = run['wakeup_time']
            diff = wakeup - now
            
            # Format countdown
            if diff.total_seconds() <= 0:
                t_minus = "ACTIVE 🔴"
            else:
                hours, remainder = divmod(int(diff.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                if hours > 0:
                    t_minus = f"T-{hours}h {minutes}m"
                else:
                    t_minus = f"T-{minutes}m {seconds}s"
            
            br_wakeup = wakeup.astimezone(timezone(timedelta(hours=-3)))
            msg += f"🏟 *{run['title']}*\n"
            msg += f"⏰ Wakeup: {br_wakeup.strftime('%H:%M')} (UTC-3) | ⏳ *{t_minus}*\n\n"
        
        if len(runs) > MAX_GAMES_DISPLAYED:
            msg += f"_...and {len(runs) - MAX_GAMES_DISPLAYED} more games scheduled._"

    last_id = None if force_new else _get_last_dashboard_id()
    
    if last_id:
        success = edit_message(msg, last_id)
        if not success:
            # If edit fails (e.g. message deleted), send a new one
            new_id = send_message(msg)
            if new_id:
                _save_dashboard_id(new_id)
    else:
        # Either No ID exists, or we are forcing a fresh post
        new_id = send_message(msg)
        if new_id:
            _save_dashboard_id(new_id)
