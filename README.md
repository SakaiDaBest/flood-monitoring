# 🌊 Smart Flood Monitoring & Automated Alert System

A real-time, automated flood early warning platform combining IoT sensing, cloud-based risk classification, and automated alert escalation.

---

## 📁 Project Structure

```
flood-monitor/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── database.py          # DB connection
│   ├── models/              # SQLAlchemy models
│   ├── routers/             # API routes
│   │   ├── auth.py          # JWT auth
│   │   ├── devices.py       # Device management
│   │   ├── readings.py      # Water level ingestion ← CORE
│   │   ├── incidents.py     # Incident tracking
│   │   └── dashboard.py     # HTML dashboard
│   └── services/
│       ├── risk.py          # Risk classification engine
│       └── alerts.py        # Telegram notifications
├── dashboard/templates/     # Jinja2 HTML dashboard
├── pi_client/
│   ├── sensor_client.py     # Pi/sensor script
│   └── simulate_devices.py  # Multi-device simulator
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🚀 Quick Start (Local with Docker)

### Step 1 — Clone & configure

```bash
cp .env.example .env
# Edit .env — set SECRET_KEY, optionally add Telegram credentials
```

### Step 2 — Start everything

```bash
docker compose up --build
```

This starts:
- PostgreSQL on port 5432
- FastAPI backend on port 8000

### Step 3 — Create an admin user

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Step 4 — Register a device

```bash
# First, get a token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -d "username=admin&password=admin123" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Register device
curl -X POST http://localhost:8000/devices/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "river_001", "name": "Klang River", "location": "Ampang, Selangor"}'
```

### Step 5 — View the dashboard

Open: http://localhost:8000

### Step 6 — Start the simulator

```bash
pip install requests
python pi_client/simulate_devices.py
```

---

## 🔌 Raspberry Pi Setup

### Hardware wiring (HC-SR04)

```
HC-SR04  →  Raspberry Pi
VCC      →  Pin 2  (5V)
GND      →  Pin 6  (GND)
TRIG     →  Pin 16 (GPIO 23)
ECHO     →  Pin 18 (GPIO 24) ← use voltage divider!
```

**Voltage divider for ECHO pin** (Pi GPIO is 3.3V max!):
```
ECHO → 1kΩ → GPIO24
              ↓
             2kΩ
              ↓
             GND
```

### Install on Pi

```bash
pip install requests RPi.GPIO

# Set environment variables
export BACKEND_URL=http://YOUR_SERVER_IP:8000
export DEVICE_ID=river_001
export SIMULATE=false
export INTERVAL_S=30

python pi_client/sensor_client.py
```

### Or run simulated on Pi (no sensor needed)

```bash
export SIMULATE=true
python pi_client/sensor_client.py
```

---

## 📡 API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | None | Health check |
| POST | `/auth/register` | None | Create admin |
| POST | `/auth/token` | None | Login → JWT |
| GET | `/devices/` | None | List devices |
| POST | `/devices/` | Admin | Add device |
| POST | `/readings/` | None | Submit reading ← Pi uses this |
| GET | `/readings/` | None | List readings |
| GET | `/readings/latest/{id}` | None | Latest for device |
| GET | `/incidents/` | Admin | List incidents |
| GET | `/docs` | None | Swagger UI |
| GET | `/` | None | Dashboard |

---

## 🚨 Risk Logic

| Water Level | Risk Level |
|-------------|-----------|
| < 30 cm | Safe ✅ |
| 30–60 cm | Warning ⚠️ |
| 60–90 cm | High Risk 🔴 |
| > 90 cm | Critical 🚨 |

**Rapid Rise Detection:** If water rises > 15cm in 10 minutes, risk escalates one level.

**Escalation:**
- Warning persisting 30+ mins → escalated incident
- High Risk persisting 10+ mins → escalated incident

---

## 🤖 Telegram Bot Setup

1. Message `@BotFather` on Telegram → `/newbot` → copy the **TOKEN**
2. Message `@userinfobot` → copy your **Chat ID**
3. Add to `.env`:
   ```
   TELEGRAM_TOKEN=your_token_here
   TELEGRAM_CHAT_ID=your_chat_id
   ```
4. Restart the server

You'll now receive alerts like:
```
🚨 FLOOD ALERT — CRITICAL

📍 Location: Ampang, Selangor
🔧 Device: Klang River (river_001)
💧 Water Level: 94.3 cm
⚡ RAPID RISE DETECTED
```

---

## ☁️ Deploy to AWS EC2

```bash
# On your EC2 instance (Ubuntu):
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git

git clone <your-repo>
cd flood-monitor
cp .env.example .env
nano .env  # set SECRET_KEY and Telegram credentials

docker compose up -d

# Open ports in EC2 Security Group: 8000 (or put Nginx in front)
```

---

## 🧪 Stress Testing

```bash
# Send 100 readings quickly
for i in $(seq 1 100); do
  LEVEL=$((RANDOM % 120))
  curl -s -X POST http://localhost:8000/readings/ \
    -H "Content-Type: application/json" \
    -d "{\"device_id\":\"river_001\",\"water_level_cm\":$LEVEL}" &
done
wait
echo "Done"
```

---

## 🎤 Pitch Line

> "A real-time, automated flood early warning platform designed for Malaysian communities, combining IoT sensing, cloud-based risk classification, and automated alert escalation — deployable nationwide with cloud-native scaling."
# flood-monitoring
