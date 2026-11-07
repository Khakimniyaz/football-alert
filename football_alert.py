import os, json, time, subprocess, requests
from datetime import datetime, timezone

API_KEY = os.environ["API_KEY"]
TG_TOKEN = os.environ["TG_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]   # один или несколько id через запятую
STATE = "sent.json"

START_HOUR, END_HOUR = 8, 22   # окно работы по UTC (13:00-03:00 по Ташкенту)
RUN_SECONDS = 5.5 * 3600       # сколько работает один запуск
PAUSE = 600                    # проверка раз в 10 минут

sent = set(json.load(open(STATE))) if os.path.exists(STATE) else set()

def notify(text):
    for chat in CHAT_ID.split(","):
        r = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": chat.strip(), "text": text},
        )
        if not r.ok:
            print("Ошибка Telegram:", chat, r.text)

def save_state():
    json.dump(sorted(sent), open(STATE, "w"))
    cmds = [
        ["git", "config", "user.name", "bot"],
        ["git", "config", "user.email", "bot@users.noreply.github.com"],
        ["git", "add", STATE],
        ["git", "commit", "-m", "state"],
        ["git", "pull", "--rebase"],
        ["git", "push"],
    ]
    for c in cmds:
        subprocess.run(c, check=False)

def check():
    resp = requests.get(
        "https://v3.football.api-sports.io/fixtures",
        headers={"x-apisports-key": API_KEY},
        params={"live": "all"},
        timeout=30,
    )
    data = resp.json()
    print(datetime.now(timezone.utc).strftime("%H:%M"), "UTC | live:",
          len(data.get("response", [])),
          "| осталось запросов:", resp.headers.get("x-ratelimit-requests-remaining"))
    if data.get("errors"):
        print("Ошибка API:", data["errors"])
    changed = False
    for m in data.get("response", []):
        fid = m["fixture"]["id"]
        if m["fixture"]["status"]["short"] != "HT" or fid in sent:
            continue
        h, a = m["goals"]["home"], m["goals"]["away"]
        if (h, a) in [(1, 0), (0, 1)]:
            sent.add(fid)
            changed = True
            notify(
                f'Перерыв, счёт {h}:{a}\n'
                f'{m["teams"]["home"]["name"]} - {m["teams"]["away"]["name"]}\n'
                f'{m["league"]["country"]}, {m["league"]["name"]}'
            )
    if changed:
        save_state()

end = time.time() + RUN_SECONDS
while time.time() < end:
    hour = datetime.now(timezone.utc).hour
    if START_HOUR <= hour < END_HOUR:
        try:
            check()
        except Exception as e:
            print("Ошибка:", e)
    time.sleep(PAUSE)
