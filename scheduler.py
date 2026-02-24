# scheduler.py — Orchestrates bot runs based on Gamma API soccer schedules.
# Prevents quota waste by only scanning during the 75-90+ minute window.

import logging
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

import polymarket_client
import main
import telegram_client
from config import MIN_MINUTE, MAX_MINUTE

logger = logging.getLogger("scheduler")

# Kickoff + 95 minutes = target start of scanning (around Minute 75 match clock)
WAKEUP_DELAY_MINUTES = 95
# Duration of a scanning session (from Minute 75 to ~Minute 105 real-time)
SESSION_DURATION_MINUTES = 30 


def get_upcoming_runs() -> list[dict]:
    """
    Fetch today's soccer schedule and calculate wakeup times.
    Returns a list of dicts: {'title': str, 'wakeup_time': datetime, 'end_time': datetime}
    """
    logger.info("Fetching soccer schedule from Gamma...")
    matches = polymarket_client.get_soccer_schedule()
    upcoming = []
    
    now = datetime.now(timezone.utc)
    
    for match in matches:
        # Gamma startTime is ISO 8601, e.g., "2026-02-28T15:00:00Z"
        start_str = match.get("startTime")
        if not start_str:
            continue
            
        try:
            # Handle possible 'Z' or offset formats
            kickoff = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            wakeup = kickoff + timedelta(minutes=WAKEUP_DELAY_MINUTES)
            end = wakeup + timedelta(minutes=SESSION_DURATION_MINUTES)
            
            # Skip matches that already finished their target window
            if now > end:
                continue
                
            upcoming.append({
                "title": match.get("title"),
                "kickoff": kickoff,
                "wakeup_time": wakeup,
                "end_time": end
            })
        except ValueError as e:
            logger.error("Failed to parse timestamp for %s: %s", match.get("title"), e)
            
    # Sort by wakeup time
    upcoming.sort(key=lambda x: x["wakeup_time"])
    return upcoming


def run_scheduler_loop():
    """Main loop that sleeps and wakes up for match windows."""
    load_dotenv()
    logger.info("Starting Smart Scheduler Loop...")
    telegram_client.send_status_update("Smart Scheduler Started 🚀")
    
    while True:
        runs = get_upcoming_runs()
        
        if not runs:
            logger.info("No more matches scheduled for today. Sleeping 1 hour before re-discovery.")
            time.sleep(3600)
            continue
            
        now = datetime.now(timezone.utc)
        next_run = runs[0]
        
        # 1. Are we currently inside a window?
        if next_run["wakeup_time"] <= now <= next_run["end_time"]:
            logger.info("!!! WAKING UP for match: %s", next_run["title"])
            telegram_client.send_status_update(f"Waking up for: {next_run['title']} 🏟")
            logger.info("Target window: %s to %s", 
                        next_run["wakeup_time"].strftime("%H:%M UTC"),
                        next_run["end_time"].strftime("%H:%M UTC"))
            
            # Start frequent scanning session
            session_end = next_run["end_time"]
            while datetime.now(timezone.utc) < session_end:
                try:
                    main.run_single_scan()
                except Exception as e:
                    logger.error("Error during scan session: %s", e)
                
                # Scan every 15 seconds during active window
                time.sleep(15)
                
            logger.info("Session finished for %s. Moving to next match.", next_run["title"])
            continue

        # 2. If it's too early for the next match, sleep until it
        time_to_wait = (next_run["wakeup_time"] - now).total_seconds()
        
        if time_to_wait > 0:
            logger.info("Next match: %s", next_run["title"])
            logger.info("Kickoff: %s | Wakeup: %s", 
                        next_run["kickoff"].strftime("%H:%M UTC"),
                        next_run["wakeup_time"].strftime("%H:%M UTC"))
            
            # Log waiting time in hours/minutes
            hours, remainder = divmod(int(time_to_wait), 3600)
            minutes, _ = divmod(remainder, 60)
            logger.info("Sleeping for %dh %dm...", hours, minutes)
            
            # Sleep at most 1 hour to re-check discovery occasionally
            sleep_duration = min(time_to_wait, 3600)
            time.sleep(sleep_duration)


if __name__ == "__main__":
    # Setup logging for standalone execution
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    run_scheduler_loop()
