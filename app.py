from flask import Flask, request, jsonify
import requests
import datetime

app = Flask(__name__)

# Вставьте ваш API-ключ Solscan
SOLSCAN_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkQXQiOjE3MzMxNjc0OTIwNTcsImVtYWlsIjoiYmxvZ2djaGV6QGdtYWlsLmNvbSIsImFjdGlvbiI6InRva2VuLWFwaSIsImFwaVZlcnNpb24iOiJ2MiIsImlhdCI6MTczMzE2NzQ5Mn0.bJH1x8C2hQPZ9SfSWkEO9k5JZ1UUZ5GqAPjeNhW34OY"
BASE_URL = "https://pro-api.solscan.io/v2.0/token/meta"

def analyze_token(token_address, entry_mcap):
    headers = {"accept": "application/json", "token": SOLSCAN_API_KEY}
    response = requests.get(f"{BASE_URL}?tokenAddress={token_address}", headers=headers)
    
    if response.status_code != 200:
        return {"error": f"Ошибка API для {token_address}"}

    data = response.json()
    if not data or "data" not in data:
        return {"error": f"Нет данных для {token_address}"}
    
    token_data = data["data"]
    ath_mcap = token_data.get("marketCap", {}).get("allTimeHigh")
    current_mcap = token_data.get("marketCap", {}).get("current")
    ath_date = token_data.get("marketCap", {}).get("allTimeHighDate")

    if not ath_mcap or not ath_date:
        return {"error": f"Недостаточно данных для {token_address}"}

    # Расчет роста или потерь
    growth_or_loss = (ath_mcap / entry_mcap) if current_mcap >= entry_mcap else -((entry_mcap - current_mcap) / entry_mcap * 100)
    ath_datetime = datetime.datetime.fromtimestamp(int(ath_date) // 1000)
    time_to_ath = (ath_datetime - datetime.datetime.now()).days

    return {
        "contract": token_address,
        "ath_mcap": ath_mcap,
        "growth": f"{growth_or_loss:.2f}x" if growth_or_loss > 0 else f"{growth_or_loss:.2f}%",
        "time_to_ath": f"{time_to_ath} дней" if time_to_ath > 0 else "ATH еще не достигнут"
    }

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json.get("data", "")
    if not data:
        return jsonify({"error": "Нет данных для анализа"}), 400
    
    results = []
    for line in data.splitlines():
        parts = line.strip().split()
        if len(parts) != 2:
            results.append({"error": f"Неверный формат данных: {line}"})
            continue

        token_address, entry_mcap = parts[0], float(parts[1])
        result = analyze_token(token_address, entry_mcap)
        results.append(result)

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)