import os
import json
import requests
import subprocess
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.oauth2 import service_account
from googleapiclient.discovery import build
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GitHub Actions環境検出
GITHUB_RUN_ID = os.getenv('GITHUB_RUN_ID')
GITHUB_WORKFLOW = os.getenv('GITHUB_WORKFLOW', 'manual')

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_USER_ID = os.getenv('TELEGRAM_USER_ID')
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS')

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Multiple calendar IDs
CALENDAR_IDS = [
    'styletech.jp@gmail.com',  # スタイルテック
    # マイカレンダー・ToDoリスト・MAE・WB × Argo・オーシャン・ヨナッックスデザイン・社団WCRI・與那覇 航
    # are configured via ADDITIONAL_CALENDAR_IDS environment variable if needed
]

# Add additional calendars from environment if configured
ADDITIONAL_CALENDARS = os.getenv('ADDITIONAL_CALENDAR_IDS', '')
if ADDITIONAL_CALENDARS:
    CALENDAR_IDS.extend([cal.strip() for cal in ADDITIONAL_CALENDARS.split(',')])

# Japanese holidays for 2024-2026
JAPANESE_HOLIDAYS = {
    '01-01': '元日',
    '01-09': '成人の日',  # 2nd Monday of January
    '02-11': '建国記念の日',
    '02-12': '休日（建国記念の日のため）',  # 2024
    '03-20': '春分の日',
    '04-29': '昭和の日',
    '05-03': '憲法記念日',
    '05-04': 'みどりの日',
    '05-05': 'こどもの日',
    '05-06': '振替休日',  # May 6 may be a substitute holiday
    '07-15': '海の日',  # 3rd Monday of July
    '08-11': '山の日',
    '09-16': '敬老の日',  # 3rd Monday of September
    '09-22': '秋分の日',
    '09-23': '秋分の日（2024）',
    '10-14': 'スポーツの日',  # 2nd Monday of October
    '11-03': '文化の日',
    '11-04': '振替休日',  # if Nov 3 is Sunday
    '11-23': '勤労感謝の日',
}

# Special dates/memorial days
SPECIAL_DATES = {
    '03-11': '東日本大震災の日',
    '06-04': '天皇誕生日（現上皇）',
    '09-01': '防災の日',
    '12-25': 'クリスマス',
}

def get_date_info():
    """Get date with holiday/memorial day information"""
    jst = ZoneInfo('Asia/Tokyo')
    now = datetime.now(jst)
    date_str = now.strftime("%Y年%m月%d日")
    days = ["月", "火", "水", "木", "金", "土", "日"]
    day_of_week = days[now.weekday()]

    date_key = now.strftime("%m-%d")

    # Check for holidays
    date_info = f"{date_str}（{day_of_week}曜日）"

    if date_key in JAPANESE_HOLIDAYS:
        holiday = JAPANESE_HOLIDAYS[date_key]
        date_info += f"\n㊗️祝日：{holiday}"
    elif date_key in SPECIAL_DATES:
        special = SPECIAL_DATES[date_key]
        date_info += f"\n📅{special}"

    return date_info

def get_events_from_calendars(morning=True):
    """Get events from multiple calendars"""
    try:
        credentials_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=SCOPES
        )

        service = build('calendar', 'v3', credentials=credentials, cache_discovery=False)

        jst = ZoneInfo('Asia/Tokyo')
        today = datetime.now(jst).date()

        if morning:
            time_min = datetime.combine(today, datetime.min.time()).replace(tzinfo=jst).isoformat()
        else:
            time_min = datetime.combine(today, datetime.min.time()).replace(hour=12, tzinfo=jst).isoformat()

        time_max = (datetime.combine(today, datetime.max.time()) + timedelta(seconds=1)).replace(tzinfo=jst).isoformat()

        all_events = []
        calendar_names = {}

        # Get all calendars for this user
        try:
            calendar_list = service.calendarList().list().execute()
            all_calendar_ids = [cal['id'] for cal in calendar_list.get('items', [])]
            # If API returns empty list, fall back to configured CALENDAR_IDS
            if not all_calendar_ids:
                all_calendar_ids = CALENDAR_IDS
            logger.info(f"Found {len(all_calendar_ids)} calendars: {all_calendar_ids}")
        except Exception as e:
            logger.error(f"Error fetching calendar list: {e}")
            all_calendar_ids = CALENDAR_IDS

        # Fetch events from all calendars
        for calendar_id in all_calendar_ids:
            try:
                # Try to get calendar display name from calendarList
                try:
                    calendar_info = service.calendarList().get(calendarId=calendar_id).execute()
                    calendar_names[calendar_id] = calendar_info.get('summary', calendar_id)
                except Exception:
                    # If not in calendarList, just use the calendar_id as name
                    # The events() API works even if calendar isn't in CalendarList
                    calendar_names[calendar_id] = calendar_id
                    logger.info(f"Calendar {calendar_id} using ID as display name")

                # Fetch events from this calendar
                events_result = service.events().list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=20,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()

                events = events_result.get('items', [])

                for event in events:
                    # Add calendar name to event
                    event['calendar_name'] = calendar_names[calendar_id]
                    all_events.append(event)

                if events:
                    logger.info(f"Found {len(events)} events from {calendar_id}")

            except Exception as e:
                logger.error(f"Error fetching from {calendar_id}: {e}")
                continue

        if not all_events:
            return "今日のスケジュール: なし" if morning else "午後のスケジュール: なし"

        # Sort by start time
        all_events.sort(key=lambda x: x['start'].get('dateTime', x['start'].get('date', '9999')))

        event_text = ""
        for event in all_events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event['summary']
            calendar_name = event.get('calendar_name', '')

            if 'T' in start:
                dt = datetime.fromisoformat(start)
                start_time = dt.strftime("%H:%M")
            else:
                start_time = "終日"

            # Display only event time and summary without calendar name
            event_text += f"• {start_time} - {summary}\n"

        return event_text.strip()

    except Exception as e:
        logger.error(f"Error getting events: {e}")
        return "スケジュール取得エラー"

def get_morning_events():
    """Get today's all events for morning briefing"""
    return get_events_from_calendars(morning=True)

def get_afternoon_events():
    """Get afternoon events (12:00 onwards) for noon briefing"""
    return get_events_from_calendars(morning=False)

def get_bitcoin_price():
    """Get Bitcoin price from CoinGecko API"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': 'bitcoin',
            'vs_currencies': 'jpy,usd'
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        btc_jpy = data['bitcoin']['jpy']
        btc_usd = data['bitcoin']['usd']

        return f"₿ Bitcoin: ¥{btc_jpy:,.0f} / ${btc_usd:,.2f}"
    except Exception as e:
        logger.error(f"Error getting Bitcoin price: {e}")
        return "Bitcoin価格取得エラー"

def get_weather():
    """Get Tokyo weather with detailed temperature information"""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': 35.6762,
            'longitude': 139.6503,
            'current': 'temperature_2m,weather_code',
            'daily': 'temperature_2m_max,temperature_2m_min',
            'hourly': 'temperature_2m',
            'timezone': 'Asia/Tokyo'
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        current = data['current']
        temp = current['temperature_2m']

        # Get daily min/max
        daily = data['daily']
        temp_max = daily['temperature_2m_max'][0]
        temp_min = daily['temperature_2m_min'][0]

        # Calculate average temperature for business hours (9:00-17:00)
        hourly_temps = data['hourly']['temperature_2m']
        # Hours 9-17 (indices 9-17)
        business_hours_temps = hourly_temps[9:18]
        temp_avg = sum(business_hours_temps) / len(business_hours_temps)

        weather_codes = {
            0: '晴れ', 1: '晴れ', 2: '曇り', 3: '曇り',
            45: '霧', 48: '霧',
            51: '小雨', 53: '小雨', 55: '小雨',
            61: '雨', 63: '雨', 65: '豪雨',
            71: '小雪', 73: '雪', 75: '豪雪',
            77: 'あられ',
            80: '所々小雨', 81: '所々雨', 82: '所々豪雨',
            85: 'あられ', 86: 'あられ',
            95: '雷雨', 96: '雷雨', 99: '雷雨'
        }

        weather = weather_codes.get(current['weather_code'], '不明')

        return f"🌡️ {weather} / 気温 {temp}°C（最低 {temp_min}°C、最高 {temp_max}°C、日中平均 {temp_avg:.1f}°C）"
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        return "天気取得エラー"

def get_daily_message():
    """Get a random motivational/informational message for the day"""
    import random

    messages = [
        "小さな工夫が大きな成果を生む。今日も一歩ずつ前に進もう！",
        "今日の成功は昨日の準備から生まれる。準備万端で挑もう！",
        "チャレンジなくして成長なし。新しいことにチャレンジしよう！",
        "完璧を目指さず、進歩を重ねることが大切。今日も前へ！",
        "周囲への感謝の気持ちを忘れずに。今日も全力を尽くそう！",
        "時間は最大の資源。今この瞬間を大切にしよう。",
        "失敗は学びの機会。恐れずにチャレンジしよう！",
        "一日一日の積み重ねが人生を作る。今日も大事に過ごそう！",
        "良い習慣が良い結果を生む。今日も一つ良い習慣を！",
        "目標を忘れずに、今日のタスクに集中しよう！",
        "仕事も人生も、バランスが大切。今日も心と体のケアを！",
        "周りの人の笑顔を増やすことが、自分の幸福につながる。",
        "今日の小さな決定が、明日の大きな変化を生む。",
        "ストレスは敵ではなく、成長のチャンス。前向きに！",
    ]

    return random.choice(messages)

def send_telegram_message(text):
    """Send message via Telegram Bot"""
    try:
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set")
        if not TELEGRAM_USER_ID:
            raise ValueError("TELEGRAM_USER_ID is not set")

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_USER_ID,
            'text': text
        }

        logger.info(f"Sending Telegram message to chat_id: {TELEGRAM_USER_ID}")
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        result = response.json()
        if result.get('ok'):
            logger.info(f"Message sent successfully to Telegram (message_id: {result.get('result', {}).get('message_id')})")
        else:
            logger.error(f"Telegram API returned error: {result}")

    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}", exc_info=True)
        raise


def check_if_already_executed_today():
    """
    Check if this briefing type was already executed today in GitHub Actions.

    Uses GITHUB_RUN_ID to detect the current execution context.
    Compares against .github/run-log.json to prevent duplicate sends within same day.
    """
    if not GITHUB_RUN_ID:
        # Not running in GitHub Actions, allow execution
        logger.info("Not running in GitHub Actions (no GITHUB_RUN_ID). Proceeding.")
        return False

    jst = ZoneInfo('Asia/Tokyo')
    today = datetime.now(jst).date()
    briefing_type = os.getenv('BRIEFING_TYPE', 'auto')

    try:
        # Check git history for run-log.json
        result = subprocess.run(
            ['git', 'show', 'HEAD:.github/run-log.json'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            logger.info("No previous run log found. This is the first execution today.")
            return False

        run_log = json.loads(result.stdout)
        last_run_date = run_log.get(f'last_{briefing_type}_run_date')

        if last_run_date == str(today):
            logger.info(f"{briefing_type.capitalize()} briefing already executed today ({today}). Skipping.")
            return True
        else:
            logger.info(f"Last {briefing_type} run was on {last_run_date}. Running today's briefing.")
            return False

    except Exception as e:
        logger.warning(f"Could not check run log: {e}. Proceeding with execution.")
        return False


def save_execution_log():
    """Save execution log to git to prevent duplicate sends."""
    if not GITHUB_RUN_ID:
        return

    jst = ZoneInfo('Asia/Tokyo')
    today = datetime.now(jst).date()
    briefing_type = os.getenv('BRIEFING_TYPE', 'auto')

    try:
        log_file = '.github/run-log.json'

        # Try to read existing log
        try:
            with open(log_file, 'r') as f:
                run_log = json.load(f)
        except FileNotFoundError:
            run_log = {}

        # Update log
        run_log[f'last_{briefing_type}_run_date'] = str(today)
        run_log[f'last_{briefing_type}_run_id'] = GITHUB_RUN_ID
        run_log[f'last_{briefing_type}_run_time'] = datetime.now(jst).isoformat()

        # Write log
        with open(log_file, 'w') as f:
            json.dump(run_log, f, indent=2)

        # Commit and push
        subprocess.run(['git', 'add', log_file], check=True)
        subprocess.run([
            'git', 'commit', '-m',
            f'chore: Update execution log for {briefing_type} briefing'
        ], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)

        logger.info(f"Execution log saved and pushed to GitHub.")

    except Exception as e:
        logger.warning(f"Could not save execution log: {e}. Continuing anyway.")


def main():
    """Main function to compile and send the briefing"""
    jst = ZoneInfo('Asia/Tokyo')
    now = datetime.now(jst)
    hour = now.hour
    minute = now.minute
    briefing_type = os.getenv('BRIEFING_TYPE', 'auto')

    logger.info(f"=== Briefing Script Started ===")
    logger.info(f"Current time (JST): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"GitHub Run ID: {GITHUB_RUN_ID}")
    logger.info(f"Current hour: {hour}, minute: {minute}")
    logger.info(f"Briefing type: {briefing_type}")

    # Check if already executed today (daily execution lock)
    if check_if_already_executed_today():
        logger.info("This briefing was already executed today. Exiting to prevent duplicate sends.")
        return

    try:
        date_and_day = get_date_info()
        weather = get_weather()
        bitcoin = get_bitcoin_price()
        daily_message = get_daily_message()

        # Determine which briefing to send based on BRIEFING_TYPE environment variable
        # Critical: Add strict time checking to prevent duplicate sends at wrong hours
        if briefing_type == 'morning':
            # Morning briefing ONLY runs during 6:00-6:59 JST
            if hour != 6:
                logger.info(f"Morning briefing scheduled but current hour is {hour}. Skipping to prevent out-of-time execution.")
                return
            is_morning = True
            is_afternoon = False
        elif briefing_type == 'afternoon':
            # Afternoon briefing ONLY runs during 12:00-12:59 JST
            if hour != 12:
                logger.info(f"Afternoon briefing scheduled but current hour is {hour}. Skipping to prevent out-of-time execution.")
                return
            is_morning = False
            is_afternoon = True
        else:
            # Fallback: use current hour (for manual/test runs without BRIEFING_TYPE)
            is_morning = (hour == 6)
            is_afternoon = (hour == 12)

        # Morning briefing: 6 AM (6:00-6:59)
        if is_morning:
            logger.info("Sending morning briefing...")
            events = get_morning_events()

            message = f"""🌅 朝の総合ブリーフィング

📅 {date_and_day}

{weather}

💰 {bitcoin}

📋 本日のスケジュール:
{events}

💪 本日のメッセージ:
「{daily_message}」

Have a productive day! 🚀"""

        # Afternoon briefing: 12 PM (12:00-12:59)
        elif is_afternoon:
            logger.info("Sending afternoon briefing...")
            events = get_afternoon_events()

            message = f"""☀️ 午後のブリーフィング

📅 {date_and_day}

{weather}

💰 {bitcoin}

📋 午後のスケジュール:
{events}

💪 本日のメッセージ:
「{daily_message}」

Have a great afternoon! 🎯"""

        else:
            logger.info(f"Out of briefing time (current hour: {hour})")
            return

        logger.info(f"Sending message at {now.strftime('%H:%M:%S')}")
        logger.info(f"Message length: {len(message)} characters")
        send_telegram_message(message)
        logger.info("=== Message sent successfully ===")

        # Save execution log to prevent duplicate sends in future runs
        save_execution_log()

    except Exception as e:
        logger.error(f"=== Error in main: {e} ===", exc_info=True)
        raise

if __name__ == "__main__":
    main()
