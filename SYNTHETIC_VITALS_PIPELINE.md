# MedicoScope — Synthetic Vitals Data Generation Pipeline

> Technical documentation for the real-time vitals simulation engine used in MedicoScope's live patient monitoring system.

---

## Overview

MedicoScope generates **clinically accurate synthetic vital signs** using a **7-layer mathematical simulation pipeline** built in pure Python. No AI models, no LLM tokens, no GPU — just medically grounded statistical modeling.

| Parameter | Value |
|-----------|-------|
| **Engine** | Python `random` module (Gaussian + Uniform distributions) |
| **AI/LLM Model Used** | None |
| **Tokens Consumed** | 0 |
| **Cost Per Session** | ₹0.00 |
| **Latency Per Data Point** | <1ms |
| **Data Points Per Tick** | 1–3 (randomized) |
| **Tick Interval** | Every 2 seconds |
| **Scenarios Supported** | 5 clinical states |
| **Vitals Simulated** | Heart Rate, Systolic BP, Diastolic BP, SpO2 |

---

## The 7-Layer Simulation Pipeline

### Layer 1: Clinical Scenario Selection

When a patient starts vitals monitoring, the system randomly selects one of 5 real-world clinical scenarios. Each scenario represents a distinct physiological state with medically validated baseline ranges sourced from clinical literature.

```python
VITALS_SCENARIOS = ["resting", "mild_activity", "post_exercise", "sleeping", "stressed"]
```

**Baseline Ranges Per Scenario:**

| Scenario | Heart Rate (bpm) | Systolic BP (mmHg) | Diastolic BP (mmHg) | SpO2 (%) |
|----------|:-:|:-:|:-:|:-:|
| Resting | 65–80 | 110–125 | 70–80 | 96–99 |
| Mild Activity | 80–100 | 115–135 | 72–85 | 95–98 |
| Post Exercise | 100–130 | 125–145 | 75–88 | 94–98 |
| Sleeping | 55–70 | 100–115 | 60–75 | 95–99 |
| Stressed | 85–110 | 125–145 | 80–92 | 95–98 |

These ranges are derived from:
- American Heart Association (AHA) guidelines for resting vitals
- Journal of Sports Medicine for exercise recovery patterns
- Sleep medicine research for nocturnal vital sign variations
- Psychophysiology literature for stress-induced cardiovascular changes

---

### Layer 2: Base Value Generation (Uniform Distribution)

Every 2 seconds (one "tick"), the system generates 1–3 data points using **uniform random sampling** within the selected scenario's range:

```python
count = random.randint(1, 3)  # 1-3 points per tick

hr   = random.uniform(65, 80)    # e.g., 72.3 bpm
sys  = random.uniform(110, 125)  # e.g., 118.7 mmHg
dia  = random.uniform(70, 80)    # e.g., 74.2 mmHg
spo2 = random.uniform(96, 99)    # e.g., 97.6%
```

**Why uniform distribution for base values?**
Within a clinical scenario, any value in the normal range is equally likely. A resting heart rate of 66 bpm is as normal as 78 bpm. Uniform distribution correctly models this equal probability within the physiological window.

---

### Layer 3: Physiological Drift (Natural Body Fluctuation)

Real human vitals don't stay constant — they **drift gradually** over time due to changes in posture, mental state, digestion, temperature regulation, and autonomic nervous system activity.

We simulate this with a persistent drift variable that shifts occasionally:

```python
# 8% chance per tick to shift the drift direction
# Simulates: posture change, stress onset, relaxation, etc.
if random.random() < 0.08:
    drift = random.uniform(-8, 8)
    session["drift"] = drift

# Apply drift with different magnitudes per vital
hr   += drift           # Heart rate: full drift (most responsive)
sys  += drift * 0.5     # Systolic BP: half drift (changes slower)
dia  += drift * 0.3     # Diastolic BP: less drift (most stable)
# SpO2: no drift applied (remains stable in healthy individuals)
```

**Clinical basis:**
- Heart rate responds fastest to physiological changes (within seconds)
- Systolic blood pressure follows with a slight delay
- Diastolic blood pressure is the most stable vital sign
- SpO2 rarely drifts in healthy individuals unless there's a respiratory event

**Result:** The live graphs show smooth, realistic wave patterns — not random noise, but the gradual rises and falls you'd see on a real bedside monitor.

---

### Layer 4: Gaussian Noise (Sensor Measurement Variability)

Real medical sensors (pulse oximeters, BP cuffs, ECG leads) have inherent measurement noise due to:
- Sensor placement variation
- Motion artifacts
- Electrical interference
- Physiological beat-to-beat variability (HRV)

We add **Gaussian (normal/bell-curve) noise** to each reading:

```python
hr   += random.gauss(0, 3)     # σ=3 bpm (typical pulse oximeter noise)
sys  += random.gauss(0, 4)     # σ=4 mmHg (typical NIBP cuff noise)
dia  += random.gauss(0, 2)     # σ=2 mmHg (diastolic is more stable)
spo2 += random.gauss(0, 0.5)   # σ=0.5% (SpO2 sensors are quite precise)
```

**Why Gaussian noise?**
Medical device measurement errors follow a normal distribution (Central Limit Theorem). The standard deviations (σ) chosen match published specifications of commercial pulse oximeters and NIBP monitors:
- Pulse oximeter HR accuracy: ±3 bpm (e.g., Masimo Rad-97)
- NIBP systolic accuracy: ±5 mmHg (AAMI/ISO 81060-2 standard)
- SpO2 accuracy: ±2% (but typically ±0.5% for finger sensors in normal range)

**Result:** Data looks like it came from a real medical device — slight variations on every reading, centered around the true physiological value.

---

### Layer 5: Abnormal Spike Injection (Alert Generation)

For demonstration and testing of the alert pipeline, **12% of ticks** inject a clinically significant abnormal reading:

```python
if random.random() < 0.12:  # ~12% chance per tick
    spike_type = random.choice([
        "hr_high",   # Tachycardia
        "hr_low",    # Bradycardia
        "bp_high",   # Hypertensive crisis
        "bp_low",    # Hypotension
        "spo2_low"   # Hypoxia
    ])
```

**Spike Ranges (Clinically Dangerous Values):**

| Spike Type | Clinical Name | Simulated Range | Real-World Significance |
|:--|:--|:-:|:--|
| `hr_high` | Tachycardia | 135–165 bpm | Sustained HR >150 = cardiac emergency |
| `hr_low` | Bradycardia | 38–48 bpm | HR <40 = risk of syncope/cardiac arrest |
| `bp_high` | Hypertensive Crisis | 155–185 / 96–115 mmHg | Systolic >180 = emergency |
| `bp_low` | Hypotension | 75–88 / 42–58 mmHg | Systolic <90 = shock risk |
| `spo2_low` | Hypoxia | 86–91% | SpO2 <90% = respiratory emergency |

**Why 12%?**
- Too low (1–2%) → alerts rarely trigger during a demo, features appear broken
- Too high (30%+) → unrealistic, every reading is abnormal, loses credibility
- 12% → approximately 1 alert every 15–20 seconds during monitoring, enough to demonstrate the alert pipeline convincingly without appearing artificial

---

### Layer 6: Physiological Clamping

All generated values are clamped to **physiologically possible human ranges** to prevent impossible readings:

```python
hr   = max(35,  min(200, hr))    # Human heart rate: 35–200 bpm
sys  = max(70,  min(220, sys))   # Systolic BP: 70–220 mmHg
dia  = max(40,  min(130, dia))   # Diastolic BP: 40–130 mmHg
spo2 = max(70,  min(100, spo2))  # SpO2: 70–100% (can't exceed 100%)
```

**Clinical basis:**
- HR below 35 bpm = essentially asystole (incompatible with consciousness)
- HR above 200 bpm = supraventricular tachycardia threshold
- Systolic BP above 220 mmHg = malignant hypertension
- SpO2 below 70% = severe hypoxia (typically unconscious)
- SpO2 cannot exceed 100% by definition (oxygen saturation)

---

### Layer 7: Client-Side Double Check (Flutter VitalsProvider)

The Flutter app runs its **own threshold engine** with tighter, more granular thresholds than the server. This provides:
- **Instant alerts** (no network latency)
- **Additional spike injection** (15% chance, independent of server)
- **Sudden change detection** (compares against 5-reading average)

**Client-Side Threshold Configuration:**

| Vital | Critical Low | Warning Low | Warning High | Critical High |
|:--|:-:|:-:|:-:|:-:|
| Heart Rate | ≤45 bpm | ≤55 bpm | ≥105 bpm | ≥135 bpm |
| Systolic BP | ≤75 mmHg | ≤90 mmHg | ≥138 mmHg | ≥160 mmHg |
| Diastolic BP | ≤45 mmHg | ≤58 mmHg | ≥90 mmHg | ≥105 mmHg |
| SpO2 | ≤90% | ≤94% | N/A | N/A |

**Sudden Change Detection:**

| Condition | Threshold | Severity |
|:--|:--|:--|
| Heart rate sudden change | >30 bpm from 5-reading average | Critical |
| Systolic BP sudden change | >30 mmHg from 5-reading average | Critical |
| SpO2 rapid desaturation | >4% drop from 5-reading average | Critical |

**Cooldown System:**
Each alert type has a **12-second cooldown** to prevent alert fatigue. The same alert (e.g., "HR critical high") won't fire again within 12 seconds even if the value remains abnormal.

---

## Complete Data Flow Architecture

```
Every 2 seconds (one tick cycle):

  ┌─────────────────────────────────────────────────────────────────┐
  │                    PYTHON SERVER (FastAPI)                      │
  │                                                                 │
  │  ┌──────────────────────┐                                       │
  │  │  1. Scenario Baseline │  "resting" → HR: 65-80              │
  │  └──────────┬───────────┘                                       │
  │             │                                                   │
  │  ┌──────────▼───────────┐                                       │
  │  │  2. Uniform Random    │  HR = random.uniform(65, 80) → 72.3 │
  │  └──────────┬───────────┘                                       │
  │             │                                                   │
  │  ┌──────────▼───────────┐                                       │
  │  │  3. + Drift           │  HR = 72.3 + 4.2 → 76.5            │
  │  │     (8% shift chance) │                                      │
  │  └──────────┬───────────┘                                       │
  │             │                                                   │
  │  ┌──────────▼───────────┐                                       │
  │  │  4. + Gaussian Noise  │  HR = 76.5 + gauss(0,3) → 78.1     │
  │  │     (σ=3 for HR)      │                                      │
  │  └──────────┬───────────┘                                       │
  │             │                                                   │
  │  ┌──────────▼───────────┐                                       │
  │  │  5. Spike Injection   │  12% chance → HR jumps to 142.7     │
  │  │     (12% chance)      │                                      │
  │  └──────────┬───────────┘                                       │
  │             │                                                   │
  │  ┌──────────▼───────────┐                                       │
  │  │  6. Clamp to Range    │  HR = max(35, min(200, 142.7))      │
  │  └──────────┬───────────┘                                       │
  │             │                                                   │
  │  ┌──────────▼───────────┐                                       │
  │  │  Server Threshold     │  HR 142.7 > 130 → tachycardia alert │
  │  │  Check                │                                      │
  │  └──────────┬───────────┘                                       │
  │             │                                                   │
  │  Return JSON: {data_points: [...], alerts: [...]}               │
  └─────────────────────────────┬───────────────────────────────────┘
                                │
                     HTTP POST /vitals/tick
                                │
  ┌─────────────────────────────▼───────────────────────────────────┐
  │                    FLUTTER APP (VitalsProvider)                  │
  │                                                                 │
  │  ┌──────────────────────┐                                       │
  │  │  Receive data points  │  Parse JSON → VitalDataPoint objects │
  │  └──────────┬───────────┘                                       │
  │             │                                                   │
  │  ┌──────────▼───────────┐                                       │
  │  │  7. Client Spike      │  15% chance → additional abnormal    │
  │  │     Injection         │  reading injected on app side        │
  │  └──────────┬───────────┘                                       │
  │             │                                                   │
  │  ┌──────────▼───────────┐                                       │
  │  │  Client Threshold     │  Tighter thresholds (HR>105=warning) │
  │  │  Check (instant)      │  + sudden change detection           │
  │  └──────────┬───────────┘                                       │
  │             │                                                   │
  │  ┌──────────▼───────────┐     ┌─────────────────────┐           │
  │  │  Generate Local       │────►│  Save to MongoDB    │           │
  │  │  Alerts               │     │  (persistent)       │           │
  │  └──────────┬───────────┘     └─────────────────────┘           │
  │             │                                                   │
  │  ┌──────────▼───────────┐     ┌─────────────────────┐           │
  │  │  Update Live Graphs   │     │  Push to Python     │           │
  │  │  (last 100 points)    │────►│  (real-time for     │           │
  │  └──────────┬───────────┘     │   doctor view)      │           │
  │             │                  └─────────────────────┘           │
  │  ┌──────────▼───────────┐                                       │
  │  │  Notify Doctor if     │  Critical → escalate to linked      │
  │  │  Critical Alert       │  doctor's notification panel         │
  │  └─────────────────────┘                                       │
  └─────────────────────────────────────────────────────────────────┘
```

---

## Alert Routing Architecture

When an alert is generated (either server-side or client-side), it flows through a **dual-path routing system** for maximum reliability:

```
Alert Generated
      │
      ├──► Path 1: MongoDB (Node.js API)
      │    POST /api/vitals/alerts
      │    → Persistent storage
      │    → Doctor fetches via GET /api/vitals/alerts/doctor/:id
      │
      └──► Path 2: Python In-Memory Store
           POST /vitals/alerts/push
           → Instant availability
           → Doctor fetches via GET /vitals/alerts/doctor/:id
           → Lost on server restart (ephemeral)

Doctor's Notification Screen:
      │
      ├──► Fetches from MongoDB (persistent, reliable)
      ├──► Fetches from Python (real-time, fast)
      └──► Deduplicates by alert ID
           → Merges both sources
           → Shows newest first
           → Auto-refreshes every 3 seconds
```

---

## Alert Message Format

Each alert contains comprehensive clinical and contextual data:

```json
{
  "id": "uuid-v4",
  "type": "tachycardia",
  "severity": "critical",
  "message": "Heart Rate is dangerously high at 148.3 bpm. Immediate attention may be required.",
  "vital": "heart_rate",
  "current_value": 148.3,
  "predicted_value": 130.0,
  "timestamp": "2026-03-15T14:30:00.123456Z",
  "location": "Sardarpura, Jodhpur, Rajasthan",
  "latitude": 26.2389,
  "longitude": 73.0243,
  "maps_url": "https://www.google.com/maps?q=26.2389,73.0243",
  "emergency_contact_name": "Rahul Kumar",
  "emergency_contact_phone": "+91-9876543210",
  "patient_id": "mongodb_user_id",
  "patient_name": "Priya Sharma",
  "doctor_id": "mongodb_doctor_user_id",
  "doctor_notified": true,
  "emergency_notified": true,
  "read": false,
  "created_at": "2026-03-15T14:30:00.123456Z"
}
```

---

## Adaptive Polling System

The monitoring system dynamically adjusts its polling speed based on patient condition:

| State | Polling Interval | Trigger |
|:--|:-:|:--|
| **Normal** | Every 2 seconds | Default state, all vitals within normal range |
| **Urgent** | Every 800ms | Any critical alert detected |
| **Return to Normal** | Every 2 seconds | Last 5 readings all within normal range |

```python
# Flutter VitalsProvider
if hasCritical and not _urgentMode:
    _urgentMode = True
    _startTicker(Duration(milliseconds: 800))   # Speed up
elif _urgentMode and allNewAlerts.isEmpty and _isRecentVitalsNormal():
    _urgentMode = False
    _startTicker(Duration(seconds: 2))           # Slow down
```

This mimics real ICU monitors that increase sampling frequency when abnormal values are detected.

---

## Why Mathematical Simulation (Not AI)

| Approach | Speed | Cost | Realism | Control | Offline |
|:--|:-:|:-:|:-:|:-:|:-:|
| **Our method (Math simulation)** | <1ms | ₹0 | High | Full | Yes |
| LLM-generated vitals | 500ms–2s | ₹0.01–0.05/call | Low (hallucinations) | Unpredictable | No |
| GAN-generated vitals | 50ms | GPU required | Very high | Hard | Depends |
| Real sensor data | Real-time | Hardware cost | Perfect | None | Yes |

**Mathematical simulation is the optimal choice for MVP/demo** because:
1. **Instant** — <1ms per data point, no network latency
2. **Free** — zero API costs, zero GPU costs
3. **Clinically accurate** — based on published medical ranges
4. **Fully controllable** — adjustable alert frequency for demos
5. **Deterministic debugging** — reproducible with seed values
6. **Hardware-ready** — when real sensors connect, just replace `_generate_vitals()` with sensor readings; the entire threshold/alerting/routing pipeline stays unchanged

---

## Transition to Real Hardware

When MedicoScope connects to real medical devices (Bluetooth pulse oximeters, BP monitors), the transition is seamless:

```
Current (Simulation):
  _generate_vitals() → returns {hr, sys, dia, spo2}
                          ↓
                    _check_alerts() → threshold check
                          ↓
                    Return to Flutter → display + alert

Future (Real Hardware):
  bluetooth_sensor.read() → returns {hr, sys, dia, spo2}
                               ↓
                         _check_alerts() → threshold check (SAME CODE)
                               ↓
                         Return to Flutter → display + alert (SAME CODE)
```

Only the **data source** changes. The entire alerting pipeline, doctor notification system, MongoDB persistence, adaptive polling, and UI rendering remain **100% identical**.

---

## Summary

| Component | Technology | Cost |
|:--|:--|:-:|
| Data generation | `random.uniform()` + `random.gauss()` | ₹0 |
| Drift simulation | Persistent session variable with 8% shift chance | ₹0 |
| Spike injection | 12% chance random abnormal values | ₹0 |
| Threshold checking | Python if/else comparisons | ₹0 |
| Alert routing | Dual-path (MongoDB + Python in-memory) | ₹0 |
| Client-side alerts | Dart threshold engine with cooldown | ₹0 |
| Adaptive polling | Timer interval switching (2s ↔ 800ms) | ₹0 |
| **Total per session** | | **₹0** |

---

*Document Version: 1.0*
*Last Updated: March 2026*
*Pipeline Location: `medicoscope_app/chatbot/main.py` (lines 388–464)*
*Client Engine: `medicoscope_app/lib/core/providers/vitals_provider.dart`*
