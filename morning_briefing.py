import os
import json
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.oauth2 import service_account
from googleapiclient.discovery import build
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

        service = build('calendar', 'v3', credentials=credentials)

        jst = ZoneInfo('Asia/Tokyo')
        today = datetime.now(jst).date()

        if morning:
            time_min = datetime.combine(today, datetime.min.time()).replace(tzinfo=jst).isoformat()
        else:
            time_min = datetime.combine(today, datetime.min.time()).replace(hour=12, tzinfo=jst).isoformat()

        time_max = (datetime.combine(today, datetime.max.time()) + timedelta(seconds=1)).replace(tzinfo=jst).isoformat()

        all_events = []
        calendar_names = {}

        # Fetch events from all calendars
        for calendar_id in CALENDAR_IDS:
            try:
                # Get calendar display name
                calendar_info = service.calendarList().get(calendarId=calendar_id).execute()
                calendar_names[calendar_id] = calendar_info.get('summary', calendar_id)

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

            if calendar_name and calendar_name != CALENDAR_IDS[0]:
                event_text += f"• {start_time} - {summary} ({calendar_name})\n"
            else:
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
            'text': text,
            'parse_mode': 'plain'
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

def main():
    """Main function to compile and send the briefing"""
    jst = ZoneInfo('Asia/Tokyo')
    now = datetime.now(jst)
    hour = now.hour
    minute = now.minute
    briefing_type = os.getenv('BRIEFING_TYPE', 'auto')

    logger.info(f"=== Briefing Script Started ===")
    logger.info(f"Current time (JST): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Current hour: {hour}, minute: {minute}")
    logger.info(f"Briefing type: {briefing_type}")

    try:
        date_and_day = get_date_info()
        weather = get_weather()
        bitcoin = get_bitcoin_price()

        # Determine which briefing to send
        is_morning = (hour == 6) or (briefing_type == 'morning')
        is_afternoon = (hour == 12) or (briefing_type == 'afternoon')

        # Morning briefing: 6 AM (6:00-6:59)
        if is_morning:
            logger.info("Sending morning briefing...")
            events = get_morning_events()

            message = f"""☀️ おはようございます!

{date_and_day}

{weather}

{bitcoin}

スケジュール:
{events}"""

        # Afternoon briefing: 12 PM (12:00-12:59)
        elif is_afternoon:
            logger.info("Sending afternoon briefing...")
            events = get_afternoon_events()

            message = f"""🌤️ こんにちは!

{date_and_day}

{weather}

{bitcoin}

午後のスケジュール:
{events}"""

        else:
            logger.info(f"Out of briefing time (current hour: {hour})")
            return

        logger.info(f"Sending message at {now.strftime('%H:%M:%S')}")
        logger.info(f"Message length: {len(message)} characters")
        send_telegram_message(message)
        logger.info("=== Message sent successfully ===")

    except Exception as e:
        logger.error(f"=== Error in main: {e} ===", exc_info=True)
        raise

if __name__ == "__main__":
    main()
