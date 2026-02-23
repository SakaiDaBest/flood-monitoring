#!/usr/bin/env python3
"""
Simulate multiple devices posting readings to the backend.
Run this to demo/stress-test without physical hardware.

Usage:
  pip install requests
  python simulate_devices.py
"""

import requests
import time
import math
import random
from datetime import datetime, timezone

BACKEND_URL = "http://localhost:8000"

DEVICES = [
    {"id": "river_001", "name": "Klang River — Ampang", "location": "Ampang, Selangor"},
    {"id": "river_002", "name": "Gombak River — Sentul", "location": "Sentul, KL"},
    {"id": "drain_001", "name": "Pandan Drain — Cheras", "location": "Cheras, KL"},
]

def register_devices():
    """Register devices (requires admin token)."""
    # Get token
    try:
        r = requests.post(f"{BACKEND_URL}/auth/token",
                          data={"username": "admin", "password": "admin123"})
        if r.status_code != 200:
            print("⚠️  Could not get admin token. Register devices manually.")
            return
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        for d in DEVICES:
            r = requests.post(f"{BACKEND_URL}/devices/", json=d, headers=headers)
            if r.status_code == 200:
                print(f"✅ Registered: {d['id']}")
            else:
                print(f"ℹ️  {d['id']}: {r.json().get('detail', 'already exists?')}")
    except Exception as e:
        print(f"Registration error: {e}")

def water_level(device_idx: int, t: float) -> float:
    """Generate realistic water levels that vary per device."""
    phase = device_idx * 1.2
    base = 35 + 25 * math.sin(t / 120 + phase)
    spike = 0
    # Simulate occasional flood spike for device 0
    if device_idx == 0 and int(t) % 300 < 60:
        spike = 40 * (int(t) % 300) / 60
    noise = random.uniform(-1.5, 1.5)
    return round(max(0, base + spike + noise), 1)

def main():
    print("🌊 Flood Simulator Starting...")
    register_devices()
    print(f"📡 Sending readings every 10s to {BACKEND_URL}\n")

    t = 0
    try:
        while True:
            for idx, device in enumerate(DEVICES):
                level = water_level(idx, t)
                payload = {
                    "device_id": device["id"],
                    "water_level_cm": level,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                try:
                    r = requests.post(f"{BACKEND_URL}/readings/", json=payload, timeout=5)
                    if r.status_code == 200:
                        data = r.json()
                        risk = data["risk_level"].upper()
                        print(f"[{device['id']}] {level}cm → {risk}")
                    else:
                        print(f"[{device['id']}] Error: {r.status_code}")
                except Exception as e:
                    print(f"[{device['id']}] Failed: {e}")

            print("---")
            time.sleep(10)
            t += 10
    except KeyboardInterrupt:
        print("\nStopped simulator.")

if __name__ == "__main__":
    main()
