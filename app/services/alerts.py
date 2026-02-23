import httpx
import os
import logging
from app.models import RiskLevel

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

RISK_EMOJI = {
    RiskLevel.SAFE: "✅",
    RiskLevel.WARNING: "⚠️",
    RiskLevel.HIGH_RISK: "🔴",
    RiskLevel.CRITICAL: "🚨",
}

async def send_telegram_alert(device_id: str, device_name: str, location: str,
                               water_level: float, risk: RiskLevel, rapid_rise: bool = False):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.info("Telegram not configured, skipping alert")
        return

    emoji = RISK_EMOJI.get(risk, "❓")
    rapid_tag = "\n⚡ *RAPID RISE DETECTED*" if rapid_rise else ""

    message = (
        f"{emoji} *FLOOD ALERT — {risk.value.upper().replace('_', ' ')}*\n\n"
        f"📍 *Location:* {location}\n"
        f"🔧 *Device:* {device_name} ({device_id})\n"
        f"💧 *Water Level:* {water_level:.1f} cm"
        f"{rapid_tag}\n\n"
        f"⏰ Please take immediate action if required."
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                logger.info(f"Telegram alert sent for {device_id} [{risk.value}]")
            else:
                logger.error(f"Telegram error: {resp.text}")
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
