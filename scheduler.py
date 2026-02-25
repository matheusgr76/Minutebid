# scheduler.py — Orchestrates bot runs based on Gamma API soccer schedules.
# Prevents quota waste by only scanning during the 75-90+ minute window.

import logging
import time
import ctypes
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

import polymarket_client
import main
import telegram_client
from config import MIN_MINUTE, MAX_MINUTE, MAX_SCHEDULE_HOURS, SCAN_INTERVAL_SLOW

logger = logging.getLogger("scheduler")

# Kickoff + 80 minutes = target start of scanning (around Minute 65+ match clock)
WAKEUP_DELAY_MINUTES = 80
# Duration of a scanning session (from Minute 65 to ~Minute 100 real-time)
SESSION_DURATION_MINUTES = 35 

# Windows Power Management Constants
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001

def set_windows_sleep_inhibition(prevent: bool):
    """
    Tells Windows to prevent (or allow) system sleep. 
    Does NOT prevent the display from turning off.
    """
    try:
        if prevent:
            # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
            logger.info("Windows sleep inhibition enabled (System stays awake, screen can sleep).")
        else:
            # Restore default behavior
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            logger.info("Windows sleep inhibition disabled (Standard power settings restored).")
    except Exception as e:
        logger.warning("Could not set Windows execution state: %s", e)

def get_br_time(utc_dt: datetime) -> datetime:
    """Convert UTC datetime to Brasilia Time (UTC-3)."""
    return utc_dt.astimezone(timezone(timedelta(hours=-3)))


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
                
            # Skip matches scheduled too far in the future (Time Horizon Filter)
            if kickoff > now + timedelta(hours=MAX_SCHEDULE_HOURS):
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
    
    # Prevent system sleep while the bot is active
    set_windows_sleep_inhibition(True)

    try:
        last_discovery_time = 0
        last_dashboard_update = 0
        last_dashboard_repost = 0
        discovery_interval = 3600  # 1 hour
        dashboard_interval = 600   # 10 minutes — Reduce noise as requested
        repost_interval = 7200     # 2 hours — Post a fresh message to avoid scrolling
        runs = []

        def _check_dashboard(runs_list: list):
            """Helper to update the Telegram dashboard if interval passed."""
            nonlocal last_dashboard_update, last_dashboard_repost
            now_ts = time.time()
            
            # Check for 2-hour RE-POST (Fresh Message)
            if now_ts - last_dashboard_repost > repost_interval:
                try:
                    telegram_client.update_scheduler_dashboard(runs_list, force_new=True)
                    last_dashboard_repost = now_ts
                    last_dashboard_update = now_ts # Also resets update timer
                    return
                except Exception as e:
                    logger.error("Dashboard re-post failed: %s", e)

            # Check for regular EDIT (Update same message)
            if now_ts - last_dashboard_update > dashboard_interval:
                try:
                    telegram_client.update_scheduler_dashboard(runs_list, force_new=False)
                except Exception as e:
                    logger.error("Dashboard update failed: %s", e)
                last_dashboard_update = now_ts

        while True:
            now_ts = time.time()

            # 1. Periodically fetch soccer schedule (Discovery)
            if now_ts - last_discovery_time > discovery_interval:
                runs = get_upcoming_runs()
                last_discovery_time = now_ts
                logger.info("Discovery cycle complete. %d matches found.", len(runs))
                if runs:
                    next_m = runs[0]
                    br_kickoff = get_br_time(next_m['kickoff'])
                    br_wakeup = get_br_time(next_m['wakeup_time'])
                    logger.info("Next Match: %s | Kickoff: %s (BR) | Wakeup: %s (BR)", 
                                next_m['title'], br_kickoff.strftime('%H:%M'), br_wakeup.strftime('%H:%M'))

            # 2. Update Telegram dashboard periodically
            _check_dashboard(runs)
            
            if not runs:
                logger.info("No more matches scheduled. Sleeping before re-discovery.")
                time.sleep(60)
                continue

            now = datetime.now(timezone.utc)
            active_run = None
            for run in runs:
                if run["wakeup_time"] <= now <= run["end_time"]:
                    active_run = run
                    break
            
            if active_run:
                logger.info("!!! WAKING UP for match: %s", active_run["title"])
                telegram_client.send_status_update(f"Waking up for: {active_run['title']} 🏟")
                
                # Start frequent scanning session
                session_end = active_run["end_time"]
                while datetime.now(timezone.utc) < session_end:
                    try:
                        main.run_single_scan()
                    except Exception as e:
                        logger.error("Error during scan session: %s", e)
                    
                    # Check for dashboard update even during active session
                    _check_dashboard(runs)
                    
                    # Scan on a slow pulse (e.g. 120s) during active window
                    time.sleep(SCAN_INTERVAL_SLOW)
                    
                logger.info("Session finished for %s. Re-running discovery.", active_run["title"])
                last_discovery_time = 0 # Force discovery after a session
                continue

            # 3. If no match is active, sleep (60s check for dashboard/active runs)
            time.sleep(60)
    finally:
        # Restore normal sleep settings on exit
        set_windows_sleep_inhibition(False)


if __name__ == "__main__":
    # Setup unified logging (console + file)
    main.setup_logging()
    run_scheduler_loop()
