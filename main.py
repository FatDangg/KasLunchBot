from flask import Flask, request, abort
import pandas as pd
from datetime import datetime, timedelta
import requests
import json

app = Flask(__name__)

# LINE API credentials
LINE_ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"
LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
USER_ID = "YOUR_USER_ID"  # This is for push messages only

# School lunch sheet
SHEET_ID = "1frI5c7VE_1Bp93Z82oGLRnUNdFAqRPYMQGvz7Jf_IwY"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

def get_today_lunch():
    df = pd.read_csv(CSV_URL)
    today = datetime.utcnow() + timedelta(hours=8)
    today_str = today.strftime('%Y/%-m/%-d')

    row = df[df['Date'] == today_str]
    if not row.empty:
        row = row.iloc[0]
        return f"""🍱 Today's Lunch ({today_str}):

🍛 Set A: {row['SetA_English']} / {row['SetA_Chinese']}
🍛 Set B: {row['SetB_English']} / {row['SetB_Chinese']}
🥦 Vegetarian: {row['Vegetarian_English']} / {row['Vegetarian_Chinese']}
🥗 Side Dish: {row['SideDish_English']} / {row['SideDish_Chinese']}"""
    else:
        return f"No lunch info found for {today_str}."

def send_push_message():
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    body = {
        "to": USER_ID,
        "messages": [{
            "type": "text",
            "text": get_today_lunch()
        }]
    }
    requests.post(LINE_PUSH_URL, headers=headers, data=json.dumps(body))

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_json()
    try:
        event = body["events"][0]
        reply_token = event["replyToken"]
        user_text = event["message"]["text"].lower()
        if user_text in ["lunch", "午餐"]:
            reply_text = get_today_lunch()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
            }
            reply_body = {
                "replyToken": reply_token,
                "messages": [{"type": "text", "text": reply_text}]
            }
            requests.post(LINE_REPLY_URL, headers=headers, data=json.dumps(reply_body))
    except Exception as e:
        print("Webhook error:", e)
    return "OK"