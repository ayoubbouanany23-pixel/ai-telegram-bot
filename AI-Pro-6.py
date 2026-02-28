from flask import Flask, request
import requests
import math
import random
import os
from datetime import datetime

app = Flask(__name__)

# ================= CONFIG =================

BOT_TOKEN = os.environ.get("8784956309:AAEyz3Ms6QiSykjhTxiwcxdH_LbyOXvySdk")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in environment variables")

if not FOOTBALL_API_KEY:
    raise ValueError("FOOTBALL_API_KEY not set in environment variables")

TELEGRAM_SEND = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

today_date = datetime.utcnow().strftime("%Y-%m-%d")
FOOTBALL_URL = f"https://v3.football.api-sports.io/fixtures?date={today_date}"

HEADERS = {
    "x-apisports-key": FOOTBALL_API_KEY
}

# ================= AI ENGINE =================

def poisson(lmbda, k):
    return (lmbda ** k * math.exp(-lmbda)) / math.factorial(k)

def analyze_match(home_xg, away_xg):
    home_win = 0
    draw = 0
    away_win = 0
    best_score = ""
    max_prob = 0

    for i in range(6):
        for j in range(6):
            p = poisson(home_xg, i) * poisson(away_xg, j)

            if p > max_prob:
                max_prob = p
                best_score = f"{i}-{j}"

            if i > j:
                home_win += p
            elif i == j:
                draw += p
            else:
                away_win += p

    return home_win, draw, away_win, best_score

# ================= FETCH MATCHES =================

def get_matches():
    try:
        response = requests.get(FOOTBALL_URL, headers=HEADERS, timeout=10)
        data = response.json()
    except Exception:
        return []

    matches = []

    if "response" not in data:
        return []

    for game in data["response"]:
        if game["fixture"]["status"]["short"] == "NS":

            home = game["teams"]["home"]["name"]
            away = game["teams"]["away"]["name"]

            # تقدير xG عشوائي (يمكن تطويره لاحقاً)
            home_xg = random.uniform(1.2, 2.0)
            away_xg = random.uniform(0.8, 1.6)

            home_p, draw_p, away_p, score = analyze_match(home_xg, away_xg)

            matches.append({
                "home": home,
                "away": away,
                "home_p": round(home_p * 100, 1),
                "draw_p": round(draw_p * 100, 1),
                "away_p": round(away_p * 100, 1),
                "score": score
            })

    return matches

# ================= TELEGRAM WEBHOOK =================

@app.route("/", methods=["GET"])
def home():
    return "AI 6.0 Telegram Engine is Running 🚀"

@app.route("/", methods=["POST"])
def webhook():
    try:
        data = request.json
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]
    except:
        return "Invalid request", 400

    if text == "/today":
        matches = get_matches()

        if not matches:
            message = "لا توجد مباريات اليوم ⚽"
        else:
            message = "🔥 AI 6.0 Predictions 🔥\n\n"

            for m in matches[:5]:
                message += (
                    f"{m['home']} 🆚 {m['away']}\n"
                    f"🏠 {m['home_p']}% | 🤝 {m['draw_p']}% | ✈ {m['away_p']}%\n"
                    f"🎯 Best Score: {m['score']}\n\n"
                )
    else:
        message = "اكتب /today لرؤية توقعات اليوم ⚽"

    requests.post(TELEGRAM_SEND, json={
        "chat_id": chat_id,
        "text": message
    })

    return "ok"

# ================= RUN =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
