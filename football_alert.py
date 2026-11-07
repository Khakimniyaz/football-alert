import os, json, requests

API_KEY = os.environ["47b5f5b947f21142a0af9f1ac680e324"]
TG_TOKEN = os.environ["9135148835:AAGehZK8csmvBV-o2WnRB0y2Y020i26fXSE"]
CHAT_ID = os.environ["985944227"]
STATE = "sent.json"

sent = set(json.load(open(STATE))) if os.path.exists(STATE) else set()

def notify(text):
    r = requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text},
    )
    if not r.ok:
        print("Ошибка Telegram:", r.text)

resp = requests.get(
    "https://v3.football.api-sports.io/fixtures",
    headers={"x-apisports-key": API_KEY},
    params={"live": "all"},
    timeout=30,
)
data = resp.json()
print("матчей live:", len(data.get("response", [])),
      "| осталось запросов:", resp.headers.get("x-ratelimit-requests-remaining"))
if data.get("errors"):
    print("Ошибка API:", data["errors"])

for m in data.get("response", []):
    fid = m["fixture"]["id"]
    if m["fixture"]["status"]["short"] != "HT" or fid in sent:
        continue
    h, a = m["goals"]["home"], m["goals"]["away"]
    if (h, a) in [(1, 0), (0, 1)]:
        sent.add(fid)
        notify(
            f'Перерыв, счёт {h}:{a}\n'
            f'{m["teams"]["home"]["name"]} - {m["teams"]["away"]["name"]}\n'
            f'{m["league"]["country"]}, {m["league"]["name"]}'
        )

json.dump(sorted(sent), open(STATE, "w"))
