#!/usr/bin/env python3
"""
Raspberry Pi Flood Sensor Client
Reads from HC-SR04 ultrasonic sensor (or simulates) and posts to backend.

Wiring:
  VCC  → 5V (Pin 2)
  GND  → GND (Pin 6)
  TRIG → GPIO 23 (Pin 16)
  ECHO → GPIO 24 (Pin 18)  [use voltage divider: 1kΩ + 2kΩ]
"""

import time
import requests
from datetime import datetime, timezone
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("pi-client")

# ─── CONFIG ────────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DEVICE_ID   = os.getenv("DEVICE_ID",   "river_001")
INTERVAL_S  = int(os.getenv("INTERVAL_S", "30"))  # send every 30 seconds
SIMULATE    = os.getenv("SIMULATE", "true").lower() == "true"

# Ultrasonic GPIO pins (only used if SIMULATE=false)
TRIG_PIN = 23
ECHO_PIN = 24

# Physical setup: sensor height above empty riverbed (cm)
SENSOR_HEIGHT_CM = 150  # adjust to your installation

# ─── SENSOR SETUP ──────────────────────────────────────────────────────────────
if not SIMULATE:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG_PIN, GPIO.OUT)
    GPIO.setup(ECHO_PIN, GPIO.IN)
    GPIO.output(TRIG_PIN, False)
    time.sleep(2)  # settle

# ─── FUNCTIONS ─────────────────────────────────────────────────────────────────
def measure_distance_cm() -> float:
    """Measure distance using HC-SR04."""
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    start = time.time()
    while GPIO.input(ECHO_PIN) == 0:
        start = time.time()
    while GPIO.input(ECHO_PIN) == 1:
        end = time.time()

    elapsed = end - start
    distance_cm = (elapsed * 34300) / 2
    return round(distance_cm, 1)

def get_water_level_cm() -> float:
    if SIMULATE:
        # Simulate a realistic rising/falling water level
        import math, random
        t = time.time() / 300  # slow cycle
        base = 40 + 30 * math.sin(t)
        noise = random.uniform(-2, 2)
        return round(max(0, base + noise), 1)
    else:
        distance = measure_distance_cm()
        water_level = SENSOR_HEIGHT_CM - distance
        return round(max(0, water_level), 1)

def send_reading(water_level: float):
    payload = {
        "device_id": DEVICE_ID,
        "water_level_cm": water_level,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        resp = requests.post(f"{BACKEND_URL}/readings/", json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            logger.info(f"Sent: {water_level}cm → risk={data['risk_level']}")
        else:
            logger.error(f"Backend error {resp.status_code}: {resp.text}")
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot reach backend at {BACKEND_URL}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

# ─── MAIN LOOP ─────────────────────────────────────────────────────────────────
def main():
    logger.info(f"Starting Pi client | device={DEVICE_ID} | simulate={SIMULATE} | interval={INTERVAL_S}s")
    try:
        while True:
            level = get_water_level_cm()
            send_reading(level)
            time.sleep(INTERVAL_S)
    except KeyboardInterrupt:
        logger.info("Stopped.")
    finally:
        if not SIMULATE:
            GPIO.cleanup()

if __name__ == "__main__":
    main()
