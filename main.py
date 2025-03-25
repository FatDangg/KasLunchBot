from flask import Flask, request
import pandas as pd
from datetime import datetime, timedelta
import requests
import json

app = Flask(__name__)

# Your LINE access token
LINE_ACCESS_TOKEN = "c9e901efa691f5070fa59c89a8f75e53"
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"
LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"

# Google Sheet (public)
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

# Webhook to auto-reply when someone types "lunch" or "午餐"
@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_json()
    try:
        for event in body["events"]:
            if event["type"] == "message" and event["message"]["type"] == "text":
                user_message = event["message"]["text"].lower()
                reply_token = event["replyToken"]
                if "lunch" in user_message or "午餐" in user_message:
                    reply_text = get_today_lunch()
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
                    }
                    payload = {
                        "replyToken": reply_token,
                        "messages": [{"type": "text", "text": reply_text}]
                    }
                    requests.post(LINE_REPLY_URL, headers=headers, json=payload)
    except Exception as e:
        print("Webhook error:", e)
    return "OK"

# Push route for cron job
@app.route("/push", methods=["GET"])
def push():
    # You can replace this with a list of users or group broadcast if needed
    # But by default, this won’t do anything unless you manually provide a userId
    return "Push endpoint is active. But you need to call /push/{userId} to push."

# Optional: Push to any user by ID (used for manual testing)
@app.route("/push/<user_id>", methods=["GET"])
def push_to_user(user_id):
    text = get_today_lunch()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    body = {
        "to": user_id,
        "messages": [{"type": "text", "text": text}]
    }
    response = requests.post(LINE_PUSH_URL, headers=headers, data=json.dumps(body))
    return f"Message sent: {response.status_code}"
