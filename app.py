"""
Umnico Auto Voice Greeting Bot
================================
Автоматически отправляет голосовое приветствие всем новым чатам
в интеграции GoodZhan (telebot, ID 108954) со статусом "Первичный".

Запуск:
    pip install requests python-dotenv
    python app.py
"""

import logging
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
#  НАСТРОЙКИ
# ─────────────────────────────────────────
UMNICO_TOKEN     = os.getenv("UMNICO_TOKEN", "ВАШ_API_ТОКЕН")  # Umnico → Настройки → API Public
VOICE_FILE_PATH  = os.getenv("VOICE_FILE", "Салем_1.ogg")
POLL_INTERVAL    = int(os.getenv("POLL_INTERVAL", "10"))        # секунд между проверками
BASE_URL         = "https://api.umnico.com/v1.3"
TARGET_SA_ID     = 108954  # ID интеграции (GoodZhan telebot)
TARGET_STATUS_ID = 958299  # ID статуса "Первичный"
# ─────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_seen_leads: set = set()
_initialized = False


def hdrs():
    return {
        "Authorization": f"bearer {UMNICO_TOKEN}",
        "Host": "api.umnico.com",
        "Content-Type": "application/json",
    }

def hdrs_base():
    return {
        "Authorization": f"bearer {UMNICO_TOKEN}",
        "Host": "api.umnico.com",
    }


def get_active_leads() -> list:
    r = requests.get(f"{BASE_URL}/leads/active", headers=hdrs(), timeout=10)
    if r.status_code == 200:
        data = r.json()
        return data if isinstance(data, list) else (data.get("data") or [])
    logger.error(f"❌ Ошибка получения лидов {r.status_code}: {r.text[:200]}")
    return []


def get_source_real_id(lead_id: int) -> str | None:
    r = requests.get(f"{BASE_URL}/messaging/{lead_id}/sources", headers=hdrs(), timeout=10)
    if r.status_code == 200:
        sources = r.json()
        if sources:
            return str(sources[0].get("realId") or sources[0].get("id", ""))
    logger.warning(f"⚠️ Не удалось получить source для лида {lead_id}: {r.status_code}")
    return None


def upload_file(source_real_id: str) -> dict | None:
    with open(VOICE_FILE_PATH, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/messaging/upload",
            headers=hdrs_base(),
            data={"source": source_real_id},
            files={"media": (os.path.basename(VOICE_FILE_PATH), f, "audio/ogg")},
            timeout=30,
        )
    if r.status_code == 200:
        return r.json()
    logger.error(f"❌ Ошибка загрузки файла {r.status_code}: {r.text[:300]}")
    return None


def send_voice(lead: dict) -> bool:
    lead_id = lead["id"]
    user_id = lead["userId"]

    source_real_id = get_source_real_id(lead_id)
    if not source_real_id:
        return False

    attachment = upload_file(source_real_id)
    if not attachment:
        return False

    payload = {
        "message": {"text": "", "attachment": attachment},
        "source": source_real_id,
        "userId": user_id,
    }
    r = requests.post(
        f"{BASE_URL}/messaging/{lead_id}/send",
        headers=hdrs(),
        json=payload,
        timeout=15,
    )
    if r.status_code in (200, 201):
        name = lead.get("customer", {}).get("name", "")
        logger.info(f"✅ Голосовое отправлено → {name} (чат {lead_id})")
        return True
    logger.error(f"❌ Ошибка отправки {r.status_code} в чат {lead_id}: {r.text[:300]}")
    return False


def polling_loop():
    global _initialized, _seen_leads
    logger.info(f"🔄 Polling запущен (каждые {POLL_INTERVAL} сек)")

    while True:
        leads = get_active_leads()

        if not _initialized:
            _seen_leads = {str(l["id"]) for l in leads}
            _initialized = True
            logger.info(f"📋 Существующих чатов: {len(_seen_leads)} — пропускаем")
        else:
            for lead in leads:
                lead_id = str(lead["id"])
                if lead_id in _seen_leads:
                    continue

                sa_id     = (lead.get("socialAccount") or {}).get("id")
                status_id = lead.get("statusId")

                # Только новые чаты из нужной интеграции с нужным статусом
                if sa_id != TARGET_SA_ID or status_id != TARGET_STATUS_ID:
                    _seen_leads.add(lead_id)
                    continue

                name = lead.get("customer", {}).get("name", "")
                logger.info(f"🆕 Новый чат: {name} (id={lead_id})")
                send_voice(lead)
                _seen_leads.add(lead_id)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    if "ВАШ_API_ТОКЕН" in UMNICO_TOKEN:
        logger.error("❌ Укажите UMNICO_TOKEN в файле .env!")
        exit(1)
    if not os.path.exists(VOICE_FILE_PATH):
        logger.error(f"❌ Файл не найден: {VOICE_FILE_PATH}")
        exit(1)
    logger.info("🚀 Бот запущен")
    polling_loop()
