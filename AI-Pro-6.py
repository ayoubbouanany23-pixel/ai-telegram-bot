from flask import Flask, request
import requests
import math
import random

app = Flask(__name__)

# ================= CONFIG =================
BOT_TOKEN = "8784956309:AAEyz3Ms6QiSykjhTxiwcxdH_LbyOXvySdk"
TELEGRAM_SEND = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

FOOTBALL_API_KEY = "36ec15df1f0c41bfac9bcecd8eef4087"
FOOTBALL_URL = "https://v3.football.api-sports.io/fixtures?date=2026-02-27"

HEADERS = {
    "x-apisports-key": FOOTBALL_API_KEY
}
# ===========================================

# --------- POISSON ENGINE ----------
def poisson(lmbda, k):
    return (lmbda ** k * math.exp(-lmbda)) / math.factorial(k)

def monte_carlo(home_xg, away_xg, simulations=3000):
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

# --------- FETCH MATCHES ----------
def get_matches():
    response = requests.get(FOOTBALL_URL, headers=HEADERS)
    data = response.json()
    matches = []

    for game in data["response"]:
        if game["fixture"]["status"]["short"] == "NS":
            home = game["teams"]["home"]["name"]
            away = game["teams"]["away"]["name"]

            # قيم افتراضية للـ xG (يمكن تطويرها لاحقاً)
            home_xg = random.uniform(1.2, 2.0)
            away_xg = random.uniform(0.8, 1.6)

            home_p, draw_p, away_p, score = monte_carlo(home_xg, away_xg)

            matches.append({
                "home": home,
                "away": away,
                "home_p": round(home_p*100,1),
                "draw_p": round(draw_p*100,1),
                "away_p": round(away_p*100,1),
                "score": score
            })

    return matches

# --------- WEBHOOK ----------
@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    chat_id = data["message"]["chat"]["id"]
    text = data["message"]["text"]

    if text == "/today":
        matches = get_matches()

        if not matches:
            message = "لا توجد مباريات اليوم ⚽"
        else:
            message = "🔥 AI 6.0 Predictions 🔥\n\n"
            for m in matches[:5]:
                message += f"""
{m['home']} 🆚 {m['away']}
🏠 {m['home_p']}% | 🤝 {m['draw_p']}% | ✈ {m['away_p']}%
🎯 Best Score: {m['score']}

"""

    else:
        message = "اكتب /today لرؤية توقعات اليوم ⚽"

    requests.post(TELEGRAM_SEND, json={
        "chat_id": chat_id,
        "text": message
    })

    return "ok"

if __name__ == "__main__":
    app.run(port=5000)