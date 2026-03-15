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

def get_morning_events():
    """Get today's all events for morning briefing"""
    try:
        credentials_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=SCOPES
        )

        service = build('calendar', 'v3', credentials=credentials)

        jst = ZoneInfo('Asia/Tokyo')
        today = datetime.now(jst).date()

        time_min = datetime.combine(today, datetime.min.time()).replace(tzinfo=jst).isoformat()
        time_max = (datetime.combine(today, datetime.max.time()) + timedelta(seconds=1)).replace(tzinfo=jst).isoformat()

        events_result = service.events().list(
            calendarId='styletech.jp@gmail.com',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            return "今日のスケジュール: なし"

        event_text = "スケジュール:\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event['summary']

            if 'T' in start:
                dt = datetime.fromisoformat(start)
                start_time = dt.strftime("%H:%M")
            else:
                start_time = "終日"

            event_text += f"• {start_time} - {summary}\n"

        return event_text
    except Exception as e:
        logger.error(f"Error getting morning events: {e}")
        return "スケジュール取得エラー"

def get_afternoon_events():
    """Get afternoon events (12:00 onwards) for noon briefing"""
    try:
        credentials_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=SCOPES
        )

        service = build('calendar', 'v3', credentials=credentials)

        jst = ZoneInfo('Asia/Tokyo')
        today = datetime.now(jst).date()

        time_min = datetime.combine(today, datetime.min.time()).replace(hour=12, tzinfo=jst).isoformat()
        time_max = (datetime.combine(today, datetime.max.time()) + timedelta(seconds=1)).replace(tzinfo=jst).isoformat()

        events_result = service.events().list(
            calendarId='styletech.jp@gmail.com',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            return "午後のスケジュール: なし"

        event_text = "午後のスケジュール:\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event['summary']

            if 'T' in start:
                dt = datetime.fromisoformat(start)
                start_time = dt.strftime("%H:%M")
            else:
                start_time = "終日"

            event_text += f"• {start_time} - {summary}\n"

        return event_text
    except Exception as e:
        logger.error(f"Error getting afternoon events: {e}")
        return "午後のスケジュール取得エラー"

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
    """Get Tokyo weather from Open-Meteo API"""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': 35.6762,
            'longitude': 139.6503,
            'current': 'temperature_2m,weather_code'
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        current = data['current']
        temp = current['temperature_2m']

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

        return f"🌡️ {weather} {temp}°C"
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        return "天気取得エラー"

def send_telegram_message(text):
    """Send message via Telegram Bot"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_USER_ID,
            'text': text,
            'parse_mode': 'plain'
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Message sent successfully to Telegram")
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")

def get_date_and_day():
    """Get formatted date and day of week"""
    jst = ZoneInfo('Asia/Tokyo')
    now = datetime.now(jst)
    date_str = now.strftime("%Y年%m月%d日")
    days = ["月", "火", "水", "木", "金", "土", "日"]
    day_of_week = days[now.weekday()]
    return f"{date_str}（{day_of_week}曜日）"

def main():
    """Main function to compile and send the briefing"""
    jst = ZoneInfo('Asia/Tokyo')
    now = datetime.now(jst)
    hour = now.hour

    date_and_day = get_date_and_day()
    weather = get_weather()
    bitcoin = get_bitcoin_price()

    if 6 <= hour < 12:
        logger.info("Sending morning briefing...")
        events = get_morning_events()

        message = f"""☀️ おはようございます!

{date_and_day}
{weather}
{bitcoin}

{events}"""

    elif 12 <= hour < 18:
        logger.info("Sending afternoon briefing...")
        events = get_afternoon_events()

        message = f"""🌤️ こんにちは!

{date_and_day}
{weather}
{bitcoin}

{events}"""

    else:
        logger.info("Out of briefing time")
        return

    logger.info(f"Message:\n{message}")
    send_telegram_message(message)

if __name__ == "__main__":
    main()
