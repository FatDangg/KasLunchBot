from flask import Flask, request
import pandas as pd
from datetime import datetime, timedelta
import requests
import json
import os

app = Flask(__name__)

# === LINE Bot Credentials ===
LINE_ACCESS_TOKEN = "PxA7x7ls4KnWrK5v75znz9SHjMiXYcu61eeIGy+BXY06VgPQV08wAUTewoXkoR9zFcmh9xDigRTWLlAVPLDowHR8S2ruSXLjCRO/raCMT5LpdumnEiCtA2Mrpdv5lEdnMRxryvtnSznAONDyy2XC6wdB04t89/1O/w1cDnyilFU="  # Replace with your real token
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"
LINE_MULTICAST_URL = "https://api.line.me/v2/bot/message/multicast"

# === Google Sheet ===
SHEET_ID = "1frI5c7VE_1Bp93Z82oGLRnUNdFAqRPYMQGvz7Jf_IwY"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# === User Database ===
USER_DB_FILE = "users.txt"

# === Get Lunch Menu ===
def get_today_lunch():
    df = pd.read_csv(CSV_URL)
    today = datetime.utcnow() + timedelta(hours=8)  # Taiwan time
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

# === Save New User ID ===
def save_user(user_id):
    if not os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, "w") as f:
            f.write(user_id + "\n")
    else:
        with open(USER_DB_FILE, "r+") as f:
            ids = f.read().splitlines()
            if user_id not in ids:
                f.write(user_id + "\n")

# === Webhook (Reply to "lunch" or "午餐") ===
@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_json()
    try:
        for event in body["events"]:
            if event["type"] == "message" and event["message"]["type"] == "text":
                user_id = event["source"]["userId"]
                user_message = event["message"]["text"].lower()
                reply_token = event["replyToken"]

                save_user(user_id)  # Save anyone who sends a message

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
        print("Webhook error:", e, flush=True)
    return "OK"

# === Push to All Users via Multicast ===
@app.route("/push", methods=["GET"])
def push_all_users():
    if not os.path.exists(USER_DB_FILE):
        return "No users found."

    with open(USER_DB_FILE, "r") as f:
        user_ids = f.read().splitlines()

    if not user_ids:
        return "No user IDs available."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }

    body = {
        "to": user_ids,
        "messages": [{
            "type": "text",
            "text": get_today_lunch()
        }]
    }

    response = requests.post(LINE_MULTICAST_URL, headers=headers, data=json.dumps(body))
    return f"Multicast response: {response.status_code}"

# === For testing individual push ===
@app.route("/push/<user_id>", methods=["GET"])
def push_to_one(user_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    body = {
        "to": user_id,
        "messages": [{"type": "text", "text": get_today_lunch()}]
    }
    response = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, data=json.dumps(body))
    return f"Message sent: {response.status_code}"
