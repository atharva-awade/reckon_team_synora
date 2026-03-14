import os
import re
import json
import uuid
import random
import asyncio
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_groq import ChatGroq

load_dotenv()

app = FastAPI(title="HearMe Chatbot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Clients ──────────────────────────────────────────────────────────────────
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7,
    max_tokens=1024,
)

llm_streaming = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7,
    max_tokens=1024,
    streaming=True,
)

# ── Config ─────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "https://medicoscope-server.onrender.com/api")

# ── In-memory stores ────────────────────────────────────────────────────────
session_histories: dict[str, list] = {}

# ── Vitals in-memory stores ─────────────────────────────────────────────────
vitals_sessions: dict[str, dict] = {}   # session_id -> session data
vitals_alerts: dict[str, list] = {}     # doctor_id / patient_id -> [alerts]

# ── Medical Knowledge Base ──────────────────────────────────────────────────
MEDICAL_DATA = {
    "skin_diseases": {
        "eczema": {"symptoms": ["itchy skin", "red patches", "dry skin", "inflammation"], "severity": "moderate", "advice": "Use moisturizers, avoid triggers, consider topical corticosteroids"},
        "psoriasis": {"symptoms": ["scaly patches", "red skin", "itching", "thick silvery scales"], "severity": "moderate", "advice": "Phototherapy, topical treatments, systemic medications for severe cases"},
        "acne": {"symptoms": ["pimples", "blackheads", "whiteheads", "oily skin"], "severity": "mild", "advice": "Gentle cleansing, benzoyl peroxide, retinoids, consult dermatologist if severe"},
        "dermatitis": {"symptoms": ["skin rash", "blisters", "itching", "swelling"], "severity": "mild-moderate", "advice": "Identify and avoid allergens, use antihistamines and topical steroids"},
    },
    "chest_diseases": {
        "asthma": {"symptoms": ["wheezing", "shortness of breath", "chest tightness", "coughing"], "severity": "moderate-severe", "advice": "Use inhaler, avoid triggers, seek emergency care for severe attacks"},
        "pneumonia": {"symptoms": ["fever", "cough with phlegm", "chest pain", "difficulty breathing"], "severity": "severe", "advice": "Seek immediate medical care, antibiotics may be needed, rest and fluids"},
        "bronchitis": {"symptoms": ["persistent cough", "mucus production", "fatigue", "chest discomfort"], "severity": "moderate", "advice": "Rest, fluids, humidifier, see doctor if symptoms last >3 weeks"},
        "copd": {"symptoms": ["chronic cough", "shortness of breath", "wheezing", "frequent respiratory infections"], "severity": "severe", "advice": "Quit smoking, bronchodilators, pulmonary rehabilitation, see pulmonologist"},
    },
    "brain_diseases": {
        "migraine": {"symptoms": ["severe headache", "nausea", "sensitivity to light", "visual disturbances"], "severity": "moderate", "advice": "Rest in dark room, OTC pain relievers, preventive medications for frequent migraines"},
        "tension_headache": {"symptoms": ["dull aching head pain", "tightness around forehead", "tenderness in scalp"], "severity": "mild", "advice": "Stress management, OTC pain relievers, adequate sleep, regular exercise"},
        "concussion": {"symptoms": ["headache", "confusion", "dizziness", "nausea", "memory problems"], "severity": "severe", "advice": "Seek immediate medical attention, rest, avoid screens, gradual return to activities"},
        "meningitis": {"symptoms": ["severe headache", "stiff neck", "high fever", "sensitivity to light", "nausea"], "severity": "critical", "advice": "EMERGENCY: Seek immediate medical care. This is potentially life-threatening."},
    },
}

# ── Language Instructions ───────────────────────────────────────────────────
LANGUAGE_INSTRUCTIONS = {
    "en": "Respond in English.",
    "hi": "Respond in Hindi (हिंदी में उत्तर दें).",
    "ta": "Respond in Tamil (தமிழில் பதிலளிக்கவும்).",
    "te": "Respond in Telugu (తెలుగులో సమాధానం ఇవ్వండి).",
    "mr": "Respond in Marathi (मराठीत उत्तर द्या).",
    "bn": "Respond in Bengali (বাংলায় উত্তর দিন).",
    "kn": "Respond in Kannada (ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ).",
}

# ── Pydantic Models ─────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    language: str = "en"
    medical_context: Optional[str] = None
    patient_profile: Optional[str] = None

class RewardRedeemRequest(BaseModel):
    reward_type: str
    language: str = "en"


# ── Helper Functions ────────────────────────────────────────────────────────

def get_session_history(session_id: str) -> list:
    if session_id not in session_histories:
        session_histories[session_id] = []
    return session_histories[session_id]


def _build_system_prompt(
    lang_instruction: str,
    medical_json: str,
    medical_context: Optional[str],
    patient_profile: Optional[str],
) -> str:
    """Build the full system prompt with all available patient context."""
    system_template = f"""You are a highly capable, conversational medical assistant for MedicoScope.
Your role is to help users understand their symptoms, provide general health guidance, and advise when to see a doctor.
You have FULL access to all the patient's data from the MedicoScope app, including their vitals readings (BP, heart rate, SpO2),
AI detection scan results (skin, chest X-ray, brain MRI), MindSpace mental health check-in transcripts,
medical conditions, medications, and health history.

IMPORTANT RULES:
1. Always be empathetic and supportive.
2. Never diagnose — only provide general information.
3. For severe symptoms, always advise seeking immediate medical attention.
4. When the patient asks about their health data (BP, vitals, scans, MindSpace sessions), refer to the PATIENT DATA below.
5. You can correlate data across different sources — e.g., if vitals show high BP and MindSpace shows stress, mention the connection.
6. If the patient mentions something they told MindSpace, you should know about it from their MindSpace transcripts.
7. {lang_instruction}

MEDICAL KNOWLEDGE BASE:
{medical_json}
"""
    if patient_profile:
        escaped_profile = patient_profile.replace("{", "{{").replace("}", "}}")
        system_template += f"\n\nPATIENT PROFILE:\n{escaped_profile}"

    if medical_context:
        escaped_context = medical_context.replace("{", "{{").replace("}", "}}")
        system_template += f"\n\nPATIENT DATA (from MedicoScope app — use this to answer patient questions):\n{escaped_context}"

    return system_template


# ── Routes ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "hearme-chatbot"}


# ── Chat (non-streaming) ───────────────────────────────────────────────────

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        history = get_session_history(req.session_id)
        lang_instruction = LANGUAGE_INSTRUCTIONS.get(req.language, LANGUAGE_INSTRUCTIONS["en"])

        # Escape curly braces in JSON so LangChain doesn't treat them as template vars
        medical_json = json.dumps(MEDICAL_DATA, indent=2).replace("{", "{{").replace("}", "}}")

        system_template = _build_system_prompt(lang_instruction, medical_json, req.medical_context, req.patient_profile)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ])

        chain = prompt | llm
        response = chain.invoke({"input": req.message, "history": history})

        history.append(HumanMessage(content=req.message))
        history.append(AIMessage(content=response.content))

        # Keep history manageable
        if len(history) > 20:
            session_histories[req.session_id] = history[-20:]

        return {"response": response.content, "session_id": req.session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Chat (streaming SSE) ───────────────────────────────────────────────────

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def event_generator():
        try:
            history = get_session_history(req.session_id)
            lang_instruction = LANGUAGE_INSTRUCTIONS.get(req.language, LANGUAGE_INSTRUCTIONS["en"])

            medical_json = json.dumps(MEDICAL_DATA, indent=2).replace("{", "{{").replace("}", "}}")

            system_template = _build_system_prompt(lang_instruction, medical_json, req.medical_context, req.patient_profile)

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_template),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ])

            chain = prompt | llm_streaming
            full_response = ""

            async for chunk in chain.astream({"input": req.message, "history": history}):
                token = chunk.content
                if token:
                    full_response += token
                    yield f"data: {json.dumps({'token': token})}\n\n"

            history.append(HumanMessage(content=req.message))
            history.append(AIMessage(content=full_response))

            if len(history) > 20:
                session_histories[req.session_id] = history[-20:]

            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── Mental Health Analysis ──────────────────────────────────────────────────

@app.post("/mental-health/analyze")
async def analyze_mental_health(
    audio: UploadFile = File(...),
    patient_id: str = Form(...),
    patient_name: str = Form(...),
    doctor_id: Optional[str] = Form(None),
    language: str = Form("en"),
):
    try:
        # Save audio temporarily
        audio_bytes = await audio.read()
        temp_path = f"/tmp/mental_health_{uuid.uuid4()}.m4a"
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)

        # Transcribe with Groq Whisper
        with open(temp_path, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=("audio.m4a", audio_file),
                model="whisper-large-v3-turbo",
                language=language if language != "en" else None,
            )

        transcript = transcription.text
        lang_instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["en"])

        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass

        # User-facing empathetic response
        user_prompt = f"""You are a compassionate mental health companion for MedicoScope MindSpace.
A user just shared their feelings through a voice check-in. Here's their transcription:

"{transcript}"

Provide a warm, empathetic, and detailed response that:
1. Acknowledges and validates their specific feelings with genuine empathy
2. Reflects back what they shared to show you truly listened
3. Offers 2-3 practical and personalized coping strategies relevant to what they described
4. Ends with an encouraging, hopeful note

Write 2-3 short paragraphs (8-12 sentences total). Be conversational and caring, like a supportive friend who also understands wellness. {lang_instruction}"""

        user_response = llm.invoke(user_prompt)

        # Doctor-facing clinical report
        doctor_report = None
        urgency = "low"
        if doctor_id:
            doctor_prompt = f"""You are a clinical mental health analyst for HearMe.
Analyze this patient's mental health check-in transcription and provide a clinical summary for their doctor.

Patient: {patient_name}
Transcription: "{transcript}"

Provide:
1. Brief clinical summary (2-3 sentences)
2. Key concerns identified
3. Recommended follow-up actions
4. Urgency level: low, moderate, or high

Format as a professional clinical note. Respond in English."""

            doctor_response = llm.invoke(doctor_prompt)
            doctor_report = doctor_response.content

            # Determine urgency from keywords
            report_lower = doctor_report.lower()
            if any(w in report_lower for w in ["high urgency", "urgent", "crisis", "suicidal", "self-harm", "emergency"]):
                urgency = "high"
            elif any(w in report_lower for w in ["moderate urgency", "moderate", "concerning", "anxiety", "depression"]):
                urgency = "moderate"

            # Save notification to Node.js backend (MongoDB)
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    await client.post(
                        f"{BACKEND_URL}/mental-health/notifications",
                        json={
                            "doctorId": doctor_id,
                            "patientId": patient_id,
                            "patientName": patient_name,
                            "clinicalReport": doctor_report,
                            "urgency": urgency,
                            "transcript": transcript,
                        },
                    )
            except Exception as notif_err:
                print(f"Warning: Failed to save notification to backend: {notif_err}")

        return {
            "user_message": user_response.content,
            "transcript": transcript,
            "doctor_report": doctor_report,
            "urgency": urgency,
            "coins_earned": 10,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Rewards ─────────────────────────────────────────────────────────────────

@app.post("/rewards/redeem")
async def redeem_reward(req: RewardRedeemRequest):
    lang_instruction = LANGUAGE_INSTRUCTIONS.get(req.language, LANGUAGE_INSTRUCTIONS["en"])

    # Map Flutter reward types to prompt keys
    type_map = {
        "meditation": "guided_meditation",
        "wellness_report": "weekly_wellness",
        "health_tips": "premium_health_tips",
        "guided_meditation": "guided_meditation",
        "weekly_wellness": "weekly_wellness",
        "premium_health_tips": "premium_health_tips",
    }

    prompts = {
        "guided_meditation": f"""Create a personalized guided meditation script (5-7 minutes).
Include breathing exercises, body scan, and visualization.
Make it calming and suitable for stress relief. {lang_instruction}""",
        "weekly_wellness": f"""Generate a comprehensive weekly wellness report with:
1. Mental health tips for the week
2. Nutrition recommendations
3. Exercise suggestions
4. Sleep hygiene tips
5. Mindfulness exercises
Make it actionable and motivating. {lang_instruction}""",
        "premium_health_tips": f"""Provide 10 premium health tips covering:
1. Physical health
2. Mental well-being
3. Nutrition
4. Sleep quality
5. Stress management
Make each tip detailed and evidence-based. {lang_instruction}""",
    }

    mapped_type = type_map.get(req.reward_type)
    prompt = prompts.get(mapped_type) if mapped_type else None
    if not prompt:
        raise HTTPException(status_code=400, detail="Invalid reward type")

    try:
        response = llm.invoke(prompt)
        return {"content": response.content, "reward_type": req.reward_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Vitals Monitoring ───────────────────────────────────────────────────────

VITALS_SCENARIOS = ["resting", "mild_activity", "post_exercise", "sleeping", "stressed"]

# Normal baseline ranges
VITALS_BASELINES = {
    "resting":       {"hr": (65, 80),  "sys": (110, 125), "dia": (70, 80),  "spo2": (96, 99)},
    "mild_activity": {"hr": (80, 100), "sys": (115, 135), "dia": (72, 85),  "spo2": (95, 98)},
    "post_exercise": {"hr": (100,130), "sys": (125, 145), "dia": (75, 88),  "spo2": (94, 98)},
    "sleeping":      {"hr": (55, 70),  "sys": (100, 115), "dia": (60, 75),  "spo2": (95, 99)},
    "stressed":      {"hr": (85, 110), "sys": (125, 145), "dia": (80, 92),  "spo2": (95, 98)},
}

ALERT_THRESHOLDS = {
    "heart_rate_high":  130,
    "heart_rate_low":   50,
    "systolic_high":    150,
    "systolic_low":     85,
    "spo2_low":         92,
}


def _generate_vitals(session: dict) -> list[dict]:
    """Generate 1-3 simulated data points for a tick."""
    scenario = session["scenario"]
    baseline = VITALS_BASELINES[scenario]
    tick = session["tick_counter"]
    points = []

    count = random.randint(1, 3)
    for i in range(count):
        tick += 1
        # Add some drift and noise
        drift = session.get("drift", 0)
        # Occasionally shift drift to simulate natural fluctuation
        if random.random() < 0.08:
            drift = random.uniform(-8, 8)
            session["drift"] = drift

        hr = random.uniform(*baseline["hr"]) + drift + random.gauss(0, 3)
        sys_ = random.uniform(*baseline["sys"]) + drift * 0.5 + random.gauss(0, 4)
        dia = random.uniform(*baseline["dia"]) + drift * 0.3 + random.gauss(0, 2)
        spo2 = random.uniform(*baseline["spo2"]) + random.gauss(0, 0.5)

        # ~12% chance of an abnormal spike/dip to generate alerts for demo
        if random.random() < 0.12:
            spike_type = random.choice(["hr_high", "hr_low", "bp_high", "bp_low", "spo2_low"])
            if spike_type == "hr_high":
                hr = random.uniform(135, 165)
            elif spike_type == "hr_low":
                hr = random.uniform(38, 48)
            elif spike_type == "bp_high":
                sys_ = random.uniform(155, 185)
                dia = random.uniform(96, 115)
            elif spike_type == "bp_low":
                sys_ = random.uniform(75, 88)
                dia = random.uniform(42, 58)
            elif spike_type == "spo2_low":
                spo2 = random.uniform(86, 91)

        # Clamp to physiologically possible values
        hr = max(35, min(200, hr))
        sys_ = max(70, min(220, sys_))
        dia = max(40, min(130, dia))
        spo2 = max(70, min(100, spo2))

        points.append({
            "tick": tick,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "heart_rate": round(hr, 1),
            "systolic": round(sys_, 1),
            "diastolic": round(dia, 1),
            "spo2": round(spo2, 1),
        })

    session["tick_counter"] = tick
    return points


def _check_alerts(session: dict, points: list[dict]) -> list[dict]:
    """Check data points against thresholds and generate alerts."""
    alerts = []
    for pt in points:
        ts = pt["timestamp"]

        if pt["heart_rate"] > ALERT_THRESHOLDS["heart_rate_high"]:
            alerts.append(_make_alert(session, "tachycardia", "warning",
                f"Heart rate elevated: {pt['heart_rate']} bpm",
                "heart_rate", pt["heart_rate"], ALERT_THRESHOLDS["heart_rate_high"], ts))
        elif pt["heart_rate"] < ALERT_THRESHOLDS["heart_rate_low"]:
            alerts.append(_make_alert(session, "bradycardia", "critical",
                f"Heart rate dangerously low: {pt['heart_rate']} bpm",
                "heart_rate", pt["heart_rate"], ALERT_THRESHOLDS["heart_rate_low"], ts))

        if pt["systolic"] > ALERT_THRESHOLDS["systolic_high"]:
            alerts.append(_make_alert(session, "hypertension", "warning",
                f"Blood pressure high: {pt['systolic']}/{pt['diastolic']} mmHg",
                "systolic", pt["systolic"], ALERT_THRESHOLDS["systolic_high"], ts))
        elif pt["systolic"] < ALERT_THRESHOLDS["systolic_low"]:
            alerts.append(_make_alert(session, "hypotension", "warning",
                f"Blood pressure low: {pt['systolic']}/{pt['diastolic']} mmHg",
                "systolic", pt["systolic"], ALERT_THRESHOLDS["systolic_low"], ts))

        if pt["spo2"] < ALERT_THRESHOLDS["spo2_low"]:
            sev = "critical" if pt["spo2"] < 88 else "warning"
            alerts.append(_make_alert(session, "hypoxia", sev,
                f"SpO2 low: {pt['spo2']}%",
                "spo2", pt["spo2"], ALERT_THRESHOLDS["spo2_low"], ts))

    return alerts


def _make_alert(session: dict, alert_type: str, severity: str,
                message: str, vital: str, current: float, predicted: float,
                timestamp: str) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "type": alert_type,
        "severity": severity,
        "message": message,
        "vital": vital,
        "current_value": current,
        "predicted_value": predicted,
        "timestamp": timestamp,
        "location": session.get("location", ""),
        "latitude": session.get("latitude", 0),
        "longitude": session.get("longitude", 0),
        "maps_url": f"https://www.google.com/maps?q={session.get('latitude',0)},{session.get('longitude',0)}",
        "emergency_contact_name": session.get("emergency_contact_name", ""),
        "emergency_contact_phone": session.get("emergency_contact_phone", ""),
        "patient_id": session.get("patient_id", ""),
        "patient_name": session.get("patient_name", ""),
        "doctor_id": session.get("doctor_id", ""),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "read": False,
    }


class VitalsStartRequest(BaseModel):
    patient_id: str
    patient_name: str
    doctor_id: str = ""
    emergency_contact_name: str = ""
    emergency_contact_phone: str = ""
    location: str = "Unknown"
    latitude: float = 0.0
    longitude: float = 0.0


class VitalsTickRequest(BaseModel):
    session_id: str


@app.post("/vitals/start")
async def vitals_start(req: VitalsStartRequest):
    session_id = str(uuid.uuid4())
    scenario = random.choice(VITALS_SCENARIOS)

    session = {
        "session_id": session_id,
        "scenario": scenario,
        "patient_id": req.patient_id,
        "patient_name": req.patient_name,
        "doctor_id": req.doctor_id,
        "emergency_contact_name": req.emergency_contact_name,
        "emergency_contact_phone": req.emergency_contact_phone,
        "location": req.location,
        "latitude": req.latitude,
        "longitude": req.longitude,
        "tick_counter": 0,
        "drift": 0,
        "created_at": datetime.utcnow().isoformat(),
    }

    vitals_sessions[session_id] = session
    return {"session_id": session_id, "scenario": scenario}


@app.post("/vitals/tick")
async def vitals_tick(req: VitalsTickRequest):
    session = vitals_sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    points = _generate_vitals(session)
    alerts = _check_alerts(session, points)

    # Store alerts per doctor and patient for later querying
    if alerts:
        doctor_id = session.get("doctor_id", "")
        patient_id = session.get("patient_id", "")
        if doctor_id:
            vitals_alerts.setdefault(f"doc_{doctor_id}", []).extend(alerts)
        if patient_id:
            vitals_alerts.setdefault(f"pat_{patient_id}", []).extend(alerts)

    return {"data_points": points, "alerts": alerts}


@app.delete("/vitals/session/{session_id}")
async def vitals_stop(session_id: str):
    vitals_sessions.pop(session_id, None)
    return {"status": "stopped"}


@app.get("/vitals/alerts/doctor/{doctor_id}")
async def vitals_doctor_alerts(doctor_id: str):
    alerts = vitals_alerts.get(f"doc_{doctor_id}", [])
    return {"alerts": alerts}


@app.get("/vitals/alerts/patient/{patient_id}")
async def vitals_patient_alerts(patient_id: str):
    alerts = vitals_alerts.get(f"pat_{patient_id}", [])
    return {"alerts": alerts}


@app.put("/vitals/alerts/{alert_id}/read")
async def vitals_mark_alert_read(alert_id: str):
    # Mark alert as read across all alert lists
    for key in vitals_alerts:
        for alert in vitals_alerts[key]:
            if alert.get("id") == alert_id:
                alert["read"] = True
    return {"status": "ok"}


@app.delete("/vitals/alerts/{alert_id}")
async def vitals_delete_alert(alert_id: str):
    """Delete a vitals alert by ID."""
    for key in list(vitals_alerts.keys()):
        vitals_alerts[key] = [a for a in vitals_alerts[key] if a.get("id") != alert_id]
    return {"status": "deleted"}


# ══════════════════════════════════════════════════════════════════════════════
# NEW ENDPOINTS: Explainable AI, Document Parsing, Triage, Safety Pipeline
# ══════════════════════════════════════════════════════════════════════════════

# ── Medical Knowledge Base for Explainability ─────────────────────────────────

CONDITION_KNOWLEDGE = {
    "skin": {
        "Melanoma": {
            "layman_name": "Skin Cancer (Melanoma)",
            "severity": "high",
            "specialist": "Dermatologist",
            "consult_urgency": "within_48_hours",
            "common_symptoms": ["Mole changing size/shape/color", "New irregular growth", "Sore that won't heal", "Itching or tenderness"],
            "precautions": ["Do NOT scratch or pick at the lesion", "Photograph with ruler for size reference", "Avoid sun exposure on affected area", "Do not apply topical treatments without advice"],
            "lifestyle": ["Apply SPF 50+ sunscreen daily", "Wear protective clothing outdoors", "Monthly skin self-exams using ABCDE rule", "Annual full-body skin checks"],
        },
        "Basal Cell Carcinoma": {
            "layman_name": "Skin Cancer (Basal Cell)",
            "severity": "moderate-high",
            "specialist": "Dermatologist",
            "consult_urgency": "within_1_week",
            "common_symptoms": ["Pearly or waxy bump", "Flat flesh-colored lesion", "Bleeding or scabbing sore that heals and returns", "Scar-like area"],
            "precautions": ["Avoid sun exposure", "Don't pick at the area", "Monitor for size changes", "Photograph regularly"],
            "lifestyle": ["Daily sunscreen use", "Avoid tanning beds", "Regular dermatology visits", "Protective clothing"],
        },
        "Actinic Keratoses": {
            "layman_name": "Pre-cancerous Skin Patches",
            "severity": "moderate",
            "specialist": "Dermatologist",
            "consult_urgency": "within_2_weeks",
            "common_symptoms": ["Rough scaly patch", "Flat to slightly raised bump", "Hard wart-like surface", "Color variations (pink, red, brown)"],
            "precautions": ["Protect from UV exposure", "Monitor for changes", "Don't scratch affected areas"],
            "lifestyle": ["Strict sun protection", "Regular skin checks", "Vitamin D supplementation if needed"],
        },
        "Dermatofibroma": {
            "layman_name": "Benign Skin Growth",
            "severity": "low",
            "specialist": "Dermatologist",
            "consult_urgency": "routine",
            "common_symptoms": ["Small firm bump", "May be tender when pressed", "Usually brownish", "Dimples when pinched"],
            "precautions": ["Generally harmless", "Monitor for rapid changes", "No treatment usually needed"],
            "lifestyle": ["Regular skin monitoring", "Normal skincare routine"],
        },
        "Benign Keratosis": {
            "layman_name": "Harmless Skin Growth",
            "severity": "low",
            "specialist": "Dermatologist",
            "consult_urgency": "routine",
            "common_symptoms": ["Waxy stuck-on appearance", "Round or oval shape", "Brown, black, or pale color", "Slightly elevated"],
            "precautions": ["Usually harmless", "Avoid irritation", "See doctor if rapidly changing"],
            "lifestyle": ["Normal skincare", "Sun protection", "Regular self-examination"],
        },
        "Melanocytic Nevi": {
            "layman_name": "Common Mole",
            "severity": "low",
            "specialist": "Dermatologist",
            "consult_urgency": "routine",
            "common_symptoms": ["Usually uniform color", "Round or oval shape", "Smaller than 6mm", "Smooth borders"],
            "precautions": ["Monitor using ABCDE rule", "Photograph for tracking", "Report changes to doctor"],
            "lifestyle": ["Sun protection", "Monthly self-exams", "Annual professional skin check if many moles"],
        },
        "Vascular Lesions": {
            "layman_name": "Blood Vessel Skin Condition",
            "severity": "low-moderate",
            "specialist": "Dermatologist",
            "consult_urgency": "within_2_weeks",
            "common_symptoms": ["Red or purple skin marks", "May be flat or raised", "Can blanch with pressure", "Usually painless"],
            "precautions": ["Avoid trauma to area", "Monitor for bleeding", "Protect from sun"],
            "lifestyle": ["Gentle skincare", "Avoid harsh chemicals on area", "Regular monitoring"],
        },
    },
    "chest": {
        "Pneumonia": {
            "layman_name": "Lung Infection",
            "severity": "high",
            "specialist": "Pulmonologist",
            "consult_urgency": "within_24_hours",
            "common_symptoms": ["Fever and chills", "Cough with phlegm", "Shortness of breath", "Chest pain when breathing"],
            "precautions": ["Seek medical care promptly", "Rest and stay hydrated", "Isolate if infectious", "Monitor breathing difficulty"],
            "lifestyle": ["Complete prescribed antibiotics", "Get pneumonia vaccine", "Practice hand hygiene", "Avoid smoking"],
        },
        "Cardiomegaly": {
            "layman_name": "Enlarged Heart",
            "severity": "high",
            "specialist": "Cardiologist",
            "consult_urgency": "within_48_hours",
            "common_symptoms": ["Shortness of breath", "Swelling in legs", "Fatigue", "Irregular heartbeat"],
            "precautions": ["Limit salt intake immediately", "Avoid strenuous activity", "Monitor weight daily", "Track symptoms"],
            "lifestyle": ["Low-sodium diet", "Regular gentle exercise", "Limit alcohol", "Manage stress"],
        },
        "Atelectasis": {
            "layman_name": "Partial Lung Collapse",
            "severity": "moderate-high",
            "specialist": "Pulmonologist",
            "consult_urgency": "within_48_hours",
            "common_symptoms": ["Difficulty breathing", "Rapid shallow breathing", "Coughing", "Low oxygen levels"],
            "precautions": ["Practice deep breathing exercises", "Use incentive spirometer if available", "Avoid lying flat for long periods"],
            "lifestyle": ["Deep breathing exercises regularly", "Stay active", "Avoid smoking", "Good posture"],
        },
        "Effusion": {
            "layman_name": "Fluid Around the Lungs",
            "severity": "moderate-high",
            "specialist": "Pulmonologist",
            "consult_urgency": "within_48_hours",
            "common_symptoms": ["Shortness of breath", "Chest pain", "Dry cough", "Difficulty lying flat"],
            "precautions": ["Sleep propped up on pillows", "Monitor breathing", "Seek care if worsening"],
            "lifestyle": ["Manage underlying conditions", "Limit salt intake", "Regular follow-up"],
        },
        "Infiltrate": {
            "layman_name": "Lung Inflammation/Infection",
            "severity": "moderate",
            "specialist": "Pulmonologist",
            "consult_urgency": "within_1_week",
            "common_symptoms": ["Cough", "Fever", "Shortness of breath", "Chest discomfort"],
            "precautions": ["Rest adequately", "Stay hydrated", "Monitor temperature"],
            "lifestyle": ["Avoid irritants and smoke", "Good nutrition", "Complete any prescribed treatment"],
        },
        "Mass": {
            "layman_name": "Abnormal Growth in Chest",
            "severity": "high",
            "specialist": "Pulmonologist/Oncologist",
            "consult_urgency": "within_48_hours",
            "common_symptoms": ["Persistent cough", "Unexplained weight loss", "Chest pain", "Coughing blood"],
            "precautions": ["Do not delay medical consultation", "Avoid smoking", "Keep detailed symptom diary"],
            "lifestyle": ["Stop smoking immediately", "Maintain nutrition", "Emotional support resources"],
        },
        "Nodule": {
            "layman_name": "Small Spot on Lung",
            "severity": "moderate",
            "specialist": "Pulmonologist",
            "consult_urgency": "within_1_week",
            "common_symptoms": ["Usually no symptoms", "Found incidentally on imaging", "May cause cough if large"],
            "precautions": ["Follow-up imaging as recommended", "Don't panic - most are benign", "Track any new symptoms"],
            "lifestyle": ["Stop smoking if applicable", "Regular follow-up scans", "Healthy diet"],
        },
        "Pneumothorax": {
            "layman_name": "Collapsed Lung",
            "severity": "critical",
            "specialist": "Emergency Medicine/Pulmonologist",
            "consult_urgency": "immediate",
            "common_symptoms": ["Sudden sharp chest pain", "Shortness of breath", "Rapid heart rate", "Bluish skin color"],
            "precautions": ["SEEK EMERGENCY CARE IMMEDIATELY", "Try to stay calm", "Sit upright to ease breathing", "Call emergency services"],
            "lifestyle": ["Avoid smoking", "Avoid extreme altitude changes", "Avoid scuba diving until cleared"],
        },
    },
    "brain": {
        "Tumor-Cell": {
            "layman_name": "Brain Tumor (Glioma)",
            "severity": "critical",
            "specialist": "Neurologist/Neurosurgeon",
            "consult_urgency": "immediate",
            "common_symptoms": ["Persistent headaches", "Seizures", "Vision changes", "Personality/behavior changes", "Nausea/vomiting"],
            "precautions": ["Seek immediate neurological consultation", "Avoid driving until evaluated", "Have someone stay with you", "Keep a symptom diary"],
            "lifestyle": ["Follow medical team guidance", "Maintain good nutrition", "Seek emotional/psychological support", "Join a support group"],
        },
    },
}

# ── Explainable AI Endpoint ───────────────────────────────────────────────────

class ExplainRequest(BaseModel):
    detection: dict  # {class_name, confidence, category}
    patient_profile: dict = {}
    vitals_baseline: dict = {}
    language: str = "en"

@app.post("/explain")
async def explain_detection(req: ExplainRequest):
    try:
        class_name = req.detection.get("class_name", "Unknown")
        confidence = req.detection.get("confidence", 0)
        category = req.detection.get("category", "unknown")

        # Get condition knowledge
        condition_info = CONDITION_KNOWLEDGE.get(category, {}).get(class_name, {})

        lang_instruction = LANGUAGE_INSTRUCTIONS.get(req.language, LANGUAGE_INSTRUCTIONS["en"])

        prompt = f"""You are a medical AI explanation system. Generate a patient-friendly explanation for an AI detection result.

Detection: {class_name} (category: {category}, confidence: {confidence:.1%})
Condition Info: {json.dumps(condition_info)}
Patient Profile: {json.dumps(req.patient_profile)}
Current Vitals: {json.dumps(req.vitals_baseline)}

Generate a JSON response with these EXACT keys:
{{
  "condition": {{"name": "{class_name}", "layman_name": "...", "category": "{category}"}},
  "what_it_is": "2-3 sentence plain-language explanation of this condition. Frame as 'The AI detected patterns consistent with...'",
  "why_it_occurs": "Why this condition typically develops. Personalize based on patient age, sex, lifestyle, and risk factors if available.",
  "how_it_affects_body": "How this condition affects the body if untreated. Include prognosis context.",
  "ai_confidence": {{
    "score": {confidence},
    "interpretation": "Low/Moderate/Moderate-High/High based on the score",
    "explanation": "What this confidence score means in plain language. Emphasize this is screening, not diagnosis.",
    "factors_affecting_confidence": ["List 2-3 factors"]
  }},
  "associated_symptoms": ["List 4-5 symptoms to watch for"],
  "immediate_precautions": ["List 3-4 things to do/avoid RIGHT NOW"],
  "lifestyle_improvements": ["List 3-4 long-term lifestyle changes"],
  "when_to_consult": {{
    "urgency": "immediate/within_48_hours/within_1_week/within_2_weeks/routine",
    "specialist": "Type of doctor to see",
    "reason": "Why professional consultation is needed",
    "what_doctor_will_do": "What to expect at the appointment"
  }},
  "personalized_risk_context": "1-2 sentences connecting the patient's specific profile to this condition's risk factors.",
  "disclaimer": "This AI analysis is for screening purposes only and does not constitute a medical diagnosis. Always consult a qualified healthcare professional for definitive evaluation."
}}

Rules:
1. Use plain language a high school student would understand
2. Never diagnose — always frame as "the AI detected patterns consistent with..."
3. Be honest about AI confidence limitations
4. Provide actionable, specific advice
5. {lang_instruction}

Return ONLY valid JSON. No markdown, no code blocks."""

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)

        # Merge with known condition data as fallback
        if condition_info:
            if not result.get("associated_symptoms"):
                result["associated_symptoms"] = condition_info.get("common_symptoms", [])
            if not result.get("immediate_precautions"):
                result["immediate_precautions"] = condition_info.get("precautions", [])
            if not result.get("lifestyle_improvements"):
                result["lifestyle_improvements"] = condition_info.get("lifestyle", [])
            if not result.get("when_to_consult", {}).get("specialist"):
                result.setdefault("when_to_consult", {})["specialist"] = condition_info.get("specialist", "")
            if not result.get("when_to_consult", {}).get("urgency"):
                result.setdefault("when_to_consult", {})["urgency"] = condition_info.get("consult_urgency", "routine")

        return result

    except Exception as e:
        print(f"Explain error: {e}")
        # Fallback to knowledge base if LLM fails
        condition_info = CONDITION_KNOWLEDGE.get(
            req.detection.get("category", ""), {}
        ).get(req.detection.get("class_name", ""), {})

        return {
            "condition": {"name": req.detection.get("class_name", "Unknown"), "layman_name": condition_info.get("layman_name", ""), "category": req.detection.get("category", "")},
            "what_it_is": f"The AI detected patterns consistent with {condition_info.get('layman_name', req.detection.get('class_name', 'an unknown condition'))}. Please consult a healthcare professional for proper evaluation.",
            "why_it_occurs": "Multiple factors can contribute to this condition. A healthcare professional can help identify specific causes.",
            "how_it_affects_body": "This condition may require medical attention. Early detection helps with better outcomes.",
            "ai_confidence": {"score": req.detection.get("confidence", 0), "interpretation": "See a professional for confirmation", "explanation": "AI screening results should always be confirmed by a qualified doctor.", "factors_affecting_confidence": ["Image quality", "Model limitations"]},
            "associated_symptoms": condition_info.get("common_symptoms", []),
            "immediate_precautions": condition_info.get("precautions", ["Consult a healthcare professional"]),
            "lifestyle_improvements": condition_info.get("lifestyle", []),
            "when_to_consult": {"urgency": condition_info.get("consult_urgency", "within_1_week"), "specialist": condition_info.get("specialist", "General Physician"), "reason": "AI screening detected patterns that need professional evaluation", "what_doctor_will_do": "Physical examination and possibly additional tests"},
            "personalized_risk_context": "",
            "disclaimer": "This AI analysis is for screening purposes only and does not constitute a medical diagnosis.",
        }


# ── Document Parsing Endpoint ─────────────────────────────────────────────────

REFERENCE_RANGES = {
    "hemoglobin": {"male": {"low": 13.5, "high": 17.5, "critical_low": 7.0, "critical_high": 20.0}, "female": {"low": 12.0, "high": 16.0, "critical_low": 7.0, "critical_high": 20.0}},
    "hematocrit": {"male": {"low": 38.3, "high": 48.6}, "female": {"low": 35.5, "high": 44.9}},
    "wbc": {"low": 4.5, "high": 11.0, "critical_low": 2.0, "critical_high": 30.0},
    "rbc": {"male": {"low": 4.7, "high": 6.1}, "female": {"low": 4.2, "high": 5.4}},
    "platelets": {"low": 150, "high": 400, "critical_low": 50, "critical_high": 1000},
    "mcv": {"low": 80, "high": 100},
    "mch": {"low": 27, "high": 33},
    "mchc": {"low": 32, "high": 36},
    "fasting_glucose": {"low": 70, "high": 100, "critical_low": 40, "critical_high": 500},
    "random_glucose": {"low": 70, "high": 140, "critical_low": 40, "critical_high": 500},
    "hba1c": {"low": 4.0, "high": 5.6},
    "total_cholesterol": {"low": 0, "high": 200},
    "ldl": {"low": 0, "high": 100},
    "hdl": {"male": {"low": 40, "high": 200}, "female": {"low": 50, "high": 200}},
    "triglycerides": {"low": 0, "high": 150},
    "creatinine": {"male": {"low": 0.7, "high": 1.3}, "female": {"low": 0.6, "high": 1.1}},
    "bun": {"low": 7, "high": 20},
    "uric_acid": {"male": {"low": 3.4, "high": 7.0}, "female": {"low": 2.4, "high": 6.0}},
    "sgot_ast": {"low": 0, "high": 40},
    "sgpt_alt": {"low": 0, "high": 40},
    "alkaline_phosphatase": {"low": 44, "high": 147},
    "total_bilirubin": {"low": 0.1, "high": 1.2, "critical_high": 15.0},
    "direct_bilirubin": {"low": 0, "high": 0.3},
    "total_protein": {"low": 6.0, "high": 8.3},
    "albumin": {"low": 3.5, "high": 5.5},
    "calcium": {"low": 8.5, "high": 10.5, "critical_low": 6.0, "critical_high": 13.0},
    "sodium": {"low": 136, "high": 145, "critical_low": 120, "critical_high": 160},
    "potassium": {"low": 3.5, "high": 5.0, "critical_low": 2.5, "critical_high": 6.5},
    "chloride": {"low": 98, "high": 106},
    "tsh": {"low": 0.4, "high": 4.0},
    "t3": {"low": 80, "high": 200},
    "t4": {"low": 5.0, "high": 12.0},
    "free_t4": {"low": 0.8, "high": 1.8},
    "iron": {"male": {"low": 65, "high": 175}, "female": {"low": 50, "high": 170}},
    "ferritin": {"male": {"low": 20, "high": 500}, "female": {"low": 20, "high": 200}},
    "vitamin_d": {"low": 30, "high": 100},
    "vitamin_b12": {"low": 200, "high": 900},
    "esr": {"male": {"low": 0, "high": 15}, "female": {"low": 0, "high": 20}},
    "crp": {"low": 0, "high": 10},
    "psa": {"low": 0, "high": 4.0},
}


class DocumentParseRequest(BaseModel):
    text: str
    file_name: str = "document"
    patient_id: str = ""


@app.post("/documents/parse")
async def parse_document(req: DocumentParseRequest):
    try:
        # Step 1: Extract medical entities and classify document using LLM
        extraction_prompt = f"""You are a medical lab report parser. Extract all medical data from this text.

Document text:
\"\"\"{req.text}\"\"\"

Return a JSON object with:
{{
  "document_type": "blood_test_report" or "lab_report" or "imaging_report" or "prescription" or "discharge_summary" or "pathology_report" or "ecg_report" or "unknown",
  "tests": [
    {{
      "name": "Test name (standardized)",
      "value": numeric_value_or_null,
      "unit": "unit string",
      "reference_range": {{"min": number, "max": number}},
      "category": "hematology/biochemistry/lipid/thyroid/liver/renal/etc"
    }}
  ],
  "patient_info": {{
    "name": "patient name if found",
    "age": "age if found",
    "sex": "male/female if found",
    "date": "report date if found"
  }},
  "ordering_doctor": "doctor name if found",
  "lab_name": "lab name if found",
  "report_date": "date if found",
  "key_observations": ["any textual observations or notes from the report"]
}}

Extract ALL test values you can find. Return ONLY valid JSON."""

        extract_response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0.1,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )

        parsed_data = json.loads(extract_response.choices[0].message.content)

        # Step 2: Flag abnormal values
        abnormal_values = []
        patient_sex = (parsed_data.get("patient_info", {}).get("sex", "") or "").lower()
        tests = parsed_data.get("tests", [])

        for test in tests:
            if test.get("value") is None:
                continue

            test_key = _normalize_test_name(test.get("name", ""))
            ref = REFERENCE_RANGES.get(test_key)
            if not ref:
                continue

            # Get sex-specific ranges if available
            if isinstance(ref.get("low"), dict) or isinstance(ref.get("male"), dict):
                if patient_sex in ("male", "female"):
                    ref = ref.get(patient_sex, ref)
                else:
                    ref = ref.get("male", ref)  # default to male ranges

            val = test["value"]
            flag = "NORMAL"
            if ref.get("critical_low") and val < ref["critical_low"]:
                flag = "CRITICAL_LOW"
            elif ref.get("low") and val < ref["low"]:
                flag = "LOW"
            elif ref.get("critical_high") and val > ref["critical_high"]:
                flag = "CRITICAL_HIGH"
            elif ref.get("high") and val > ref["high"]:
                flag = "HIGH"

            if flag != "NORMAL":
                low = ref.get("low", "?")
                high = ref.get("high", "?")
                unit = test.get("unit", "")

                if flag in ("LOW", "CRITICAL_LOW"):
                    deviation = f"-{((ref.get('low', val) - val) / ref.get('low', 1) * 100):.1f}%" if ref.get("low") else ""
                else:
                    deviation = f"+{((val - ref.get('high', val)) / ref.get('high', 1) * 100):.1f}%" if ref.get("high") else ""

                abnormal_values.append({
                    "name": test.get("name", ""),
                    "value": val,
                    "unit": unit,
                    "flag": flag,
                    "normalRange": f"{low} - {high} {unit}",
                    "deviation": deviation,
                })

        # Step 3: Generate patient-friendly explanation
        explain_prompt = f"""You are a medical report interpreter. Explain this lab report to a patient in simple, clear language.

Parsed data: {json.dumps(parsed_data)}
Abnormal values: {json.dumps(abnormal_values)}

Structure your response as JSON:
{{
  "summary": "One-paragraph overview of what this report shows",
  "key_findings": ["Each abnormal value explained in plain English"],
  "what_this_means": "How these findings relate to the patient's health",
  "correlations": ["Connections between multiple abnormal values if any"],
  "recommended_actions": ["Specific next steps"],
  "questions_for_doctor": ["Smart questions the patient should ask"]
}}

Do NOT diagnose. Frame everything as 'these results may suggest...' or 'these values are consistent with...'
Return ONLY valid JSON."""

        explain_response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": explain_prompt}],
            temperature=0.3,
            max_tokens=1536,
            response_format={"type": "json_object"},
        )

        explanation = json.loads(explain_response.choices[0].message.content)

        # Determine urgency
        urgency = "routine"
        for av in abnormal_values:
            if av["flag"] in ("CRITICAL_LOW", "CRITICAL_HIGH"):
                urgency = "urgent"
                break
            elif av["flag"] in ("LOW", "HIGH"):
                urgency = "follow_up"

        return {
            "document_type": parsed_data.get("document_type", "unknown"),
            "parsed_data": parsed_data,
            "abnormal_values": abnormal_values,
            "explanation": explanation,
            "urgency": urgency,
        }

    except Exception as e:
        print(f"Document parse error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _normalize_test_name(name: str) -> str:
    """Normalize test name to match reference ranges keys."""
    name = name.lower().strip()
    mappings = {
        "hemoglobin": "hemoglobin", "hb": "hemoglobin", "hgb": "hemoglobin",
        "hematocrit": "hematocrit", "hct": "hematocrit", "pcv": "hematocrit",
        "wbc": "wbc", "white blood cell": "wbc", "total wbc": "wbc", "leucocyte": "wbc",
        "rbc": "rbc", "red blood cell": "rbc", "erythrocyte": "rbc",
        "platelet": "platelets", "platelets": "platelets", "plt": "platelets",
        "mcv": "mcv", "mch": "mch", "mchc": "mchc",
        "fasting glucose": "fasting_glucose", "fasting blood sugar": "fasting_glucose", "fbs": "fasting_glucose",
        "random glucose": "random_glucose", "random blood sugar": "random_glucose", "rbs": "random_glucose",
        "hba1c": "hba1c", "glycated hemoglobin": "hba1c", "a1c": "hba1c",
        "total cholesterol": "total_cholesterol", "cholesterol": "total_cholesterol",
        "ldl": "ldl", "ldl cholesterol": "ldl",
        "hdl": "hdl", "hdl cholesterol": "hdl",
        "triglycerides": "triglycerides", "triglyceride": "triglycerides", "tg": "triglycerides",
        "creatinine": "creatinine", "serum creatinine": "creatinine",
        "bun": "bun", "blood urea nitrogen": "bun", "urea": "bun",
        "uric acid": "uric_acid",
        "sgot": "sgot_ast", "ast": "sgot_ast", "aspartate aminotransferase": "sgot_ast",
        "sgpt": "sgpt_alt", "alt": "sgpt_alt", "alanine aminotransferase": "sgpt_alt",
        "alkaline phosphatase": "alkaline_phosphatase", "alp": "alkaline_phosphatase",
        "total bilirubin": "total_bilirubin", "bilirubin total": "total_bilirubin",
        "direct bilirubin": "direct_bilirubin",
        "total protein": "total_protein",
        "albumin": "albumin", "serum albumin": "albumin",
        "calcium": "calcium", "serum calcium": "calcium",
        "sodium": "sodium", "na": "sodium",
        "potassium": "potassium", "k": "potassium",
        "chloride": "chloride", "cl": "chloride",
        "tsh": "tsh", "thyroid stimulating hormone": "tsh",
        "t3": "t3", "triiodothyronine": "t3",
        "t4": "t4", "thyroxine": "t4",
        "free t4": "free_t4", "ft4": "free_t4",
        "iron": "iron", "serum iron": "iron",
        "ferritin": "ferritin", "serum ferritin": "ferritin",
        "vitamin d": "vitamin_d", "25-oh vitamin d": "vitamin_d", "vit d": "vitamin_d",
        "vitamin b12": "vitamin_b12", "vit b12": "vitamin_b12",
        "esr": "esr", "erythrocyte sedimentation rate": "esr",
        "crp": "crp", "c-reactive protein": "crp",
        "psa": "psa", "prostate specific antigen": "psa",
    }
    return mappings.get(name, name.replace(" ", "_"))


# ── Triage Endpoint ───────────────────────────────────────────────────────────

class TriageRequest(BaseModel):
    symptoms: list[str] = []
    patient_profile: dict = {}
    recent_events: list = []
    language: str = "en"


TRIAGE_RULES = {
    "skin": ["rash", "mole", "lesion", "skin", "bump", "spot", "itch", "acne", "melanoma", "discoloration", "pigment", "freckle", "wart", "boil", "blister", "hives", "eczema", "psoriasis", "dermatitis"],
    "chest": ["cough", "breathing", "chest pain", "shortness of breath", "wheezing", "pneumonia", "lung", "respiratory", "bronchitis", "phlegm", "sputum", "asthma", "copd"],
    "brain": ["headache", "seizure", "vision", "dizziness", "confusion", "memory", "neurological", "migraine", "numbness", "tingling", "brain", "tumor", "concussion"],
    "heart": ["palpitation", "heart", "cardiac", "chest tightness", "irregular heartbeat", "murmur", "angina", "arrhythmia", "tachycardia", "bradycardia"],
    "mental_health": ["anxiety", "depression", "stress", "sleep", "insomnia", "panic", "mood", "sadness", "worry", "mental", "emotional", "burnout", "overwhelmed", "lonely"],
    "vitals": ["blood pressure", "hypertension", "hypotension", "oxygen", "spo2", "fever", "temperature"],
}


@app.post("/triage")
async def triage_symptoms(req: TriageRequest):
    try:
        symptoms_text = ", ".join(req.symptoms) if req.symptoms else "general checkup"

        # Rule-based pre-screening
        rule_scores = {}
        symptoms_lower = symptoms_text.lower()
        for module, keywords in TRIAGE_RULES.items():
            score = sum(1 for kw in keywords if kw in symptoms_lower)
            if score > 0:
                rule_scores[module] = score

        # LLM-based triage for nuanced understanding
        lang_instruction = LANGUAGE_INSTRUCTIONS.get(req.language, LANGUAGE_INSTRUCTIONS["en"])

        triage_prompt = f"""You are a medical triage AI for MedicoScope. Based on the patient's symptoms, recommend which diagnostic module to use.

Available modules:
- skin: AI Skin Disease Detection (dermascopy analysis for 7 skin conditions)
- chest: AI Chest X-Ray Analysis (8 lung/chest conditions)
- brain: AI Brain MRI Analysis (tumor detection)
- heart: CardioScope Heart Sound Analysis (5 cardiac conditions)
- mental_health: MindSpace Mental Health Assessment
- vitals: Real-time Vitals Monitoring (HR, BP, SpO2)
- chatbot: General AI Medical Chatbot (for non-specific or multiple symptoms)

Patient symptoms: {symptoms_text}
Patient profile: {json.dumps(req.patient_profile)}
Recent health events: {json.dumps(req.recent_events[:5])}

Return JSON:
{{
  "recommended_module": "module_name",
  "urgency": "routine/urgent/emergency",
  "reasoning": "1-2 sentence explanation of why this module was recommended",
  "alternative_modules": ["other relevant modules"],
  "follow_up_questions": ["1-2 questions to ask for better assessment"]
}}

{lang_instruction}
Return ONLY valid JSON."""

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": triage_prompt}],
            temperature=0.2,
            max_tokens=512,
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)

        # If rule-based and LLM disagree, prefer the one with higher confidence
        if rule_scores and result.get("recommended_module") not in rule_scores:
            top_rule = max(rule_scores, key=rule_scores.get)
            if rule_scores[top_rule] >= 2:
                result["alternative_modules"] = [result["recommended_module"]] + result.get("alternative_modules", [])
                result["recommended_module"] = top_rule

        return result

    except Exception as e:
        print(f"Triage error: {e}")
        # Fallback to rule-based only
        if rule_scores:
            top = max(rule_scores, key=rule_scores.get)
            return {
                "recommended_module": top,
                "urgency": "routine",
                "reasoning": f"Based on symptoms matching {top} keywords",
                "alternative_modules": [k for k in rule_scores if k != top],
                "follow_up_questions": [],
            }
        return {
            "recommended_module": "chatbot",
            "urgency": "routine",
            "reasoning": "General assessment recommended",
            "alternative_modules": [],
            "follow_up_questions": ["Can you describe your main symptom in more detail?"],
        }


# ── Mental Health Safety Pipeline ─────────────────────────────────────────────

RISK_INDICATORS = {
    "critical": [
        "want to die", "kill myself", "end my life", "suicide", "suicidal",
        "no reason to live", "better off dead", "plan to end it",
        "bought pills", "have a gun", "going to jump", "slit my wrists",
        "overdose", "hanging myself", "final goodbye", "last letter",
        "end it all", "can't live anymore",
    ],
    "high": [
        "self-harm", "cutting myself", "hurting myself", "don't want to be here",
        "can't go on", "wish I was dead", "nothing matters anymore",
        "everyone would be better without me", "giving away my things",
        "want to hurt myself", "thinking about death", "no point in living",
    ],
    "moderate": [
        "hopeless", "worthless", "trapped", "burden", "no way out",
        "can't take it anymore", "breaking point", "falling apart",
        "don't care anymore", "numb", "empty inside", "completely alone",
        "nobody understands", "want to disappear",
    ],
}

ANONYMIZATION_PATTERNS = [
    (r"\b(?:my\s+)?(?:girlfriend|gf)\s+([A-Z][a-z]+)", "my partner"),
    (r"\b(?:my\s+)?(?:boyfriend|bf)\s+([A-Z][a-z]+)", "my partner"),
    (r"\b(?:my\s+)?(?:wife)\s+([A-Z][a-z]+)", "my spouse"),
    (r"\b(?:my\s+)?(?:husband)\s+([A-Z][a-z]+)", "my spouse"),
    (r"\b(?:my\s+)?(?:ex[-\s]?girlfriend|ex[-\s]?boyfriend|ex[-\s]?wife|ex[-\s]?husband|ex)\s+([A-Z][a-z]+)", "my ex-partner"),
    (r"\b(?:my\s+)?(?:mom|mother|mum|mama)\s+([A-Z][a-z]+)", "my mother"),
    (r"\b(?:my\s+)?(?:dad|father|papa)\s+([A-Z][a-z]+)", "my father"),
    (r"\b(?:my\s+)?(?:sister)\s+([A-Z][a-z]+)", "my sister"),
    (r"\b(?:my\s+)?(?:brother)\s+([A-Z][a-z]+)", "my brother"),
    (r"\b(?:my\s+)?(?:boss|manager)\s+([A-Z][a-z]+)", "my supervisor"),
    (r"\b(?:my\s+)?(?:friend)\s+([A-Z][a-z]+)", "my friend"),
    (r"\b(?:my\s+)?(?:teacher|professor)\s+([A-Z][a-z]+)", "my teacher"),
    (r"\b(?:my\s+)?(?:therapist|counselor)\s+([A-Z][a-z]+)", "my therapist"),
    # Contact info removal
    (r"\b\d{10,13}\b", "[phone removed]"),
    (r"\b[\w.-]+@[\w.-]+\.\w+\b", "[email removed]"),
]

SAFETY_RESPONSES = {
    4: """I hear you, and I want you to know that your life has value. What you're feeling right now is temporary, even though it doesn't feel that way.

Please reach out right now to one of these helplines:
- Emergency: 112 (India) / 911 (US)
- AASRA (India): 9820466726
- iCall: 9152987821
- Vandrevala Foundation: 1860-2662-345

Your linked doctor has been notified. You are not alone in this.

Can you tell me — are you somewhere safe right now?""",
    3: """I can hear that you're going through something really difficult. Thank you for sharing this with me — it takes courage.

I want to make sure you're safe. Here are some resources available 24/7:
- AASRA: 9820466726
- iCall: 9152987821
- Vandrevala Foundation: 1860-2662-345

Your doctor will be informed to check in on you.

What's one small thing that has helped you feel even slightly better in the past?""",
    2: """Thank you for opening up about how you're feeling. What you're experiencing sounds really challenging, and it's okay to not be okay.

Remember, you can always reach out to:
- iCall: 9152987821
- Vandrevala Foundation: 1860-2662-345

Would you like to talk more about what's been weighing on you?""",
}

SEVERITY_LABELS = {
    0: "SAFE",
    1: "LOW_RISK",
    2: "MODERATE_RISK",
    3: "HIGH_RISK",
    4: "CRITICAL",
}


def anonymize_transcript(text: str) -> tuple[str, dict]:
    """Replace personal names with generic relationship labels."""
    replacements = {}
    anonymized = text
    for pattern, replacement in ANONYMIZATION_PATTERNS:
        matches = re.finditer(pattern, anonymized, re.IGNORECASE)
        for match in matches:
            original = match.group(0)
            replacements[original] = replacement
            anonymized = anonymized.replace(original, replacement)
    return anonymized, replacements


def keyword_risk_screening(text: str) -> tuple[int, list[str]]:
    """Fast keyword-based risk pre-screening."""
    level = 0
    triggers = []
    lower_text = text.lower()

    for severity, keywords in RISK_INDICATORS.items():
        for kw in keywords:
            if kw in lower_text:
                triggers.append(kw)
                if severity == "critical":
                    level = max(level, 4)
                elif severity == "high":
                    level = max(level, 3)
                elif severity == "moderate":
                    level = max(level, 2)

    return level, triggers


async def llm_risk_classification(text: str) -> dict:
    """LLM-based contextual risk classification."""
    try:
        prompt = f"""You are a mental health risk classifier. Analyze this text and classify the risk level.

Text: "{text}"

Risk levels:
0 = SAFE: No risk indicators
1 = LOW_RISK: Mild distress, no safety concerns
2 = MODERATE_RISK: Significant distress, possible passive ideation
3 = HIGH_RISK: Active suicidal/self-harm ideation without clear plan
4 = CRITICAL: Active plan, intent, or means for self-harm/suicide

Return JSON:
{{"level": 0-4, "reasoning": "brief explanation", "confidence": 0.0-1.0}}

Return ONLY valid JSON."""

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=256,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {"level": 0, "reasoning": "Classification unavailable", "confidence": 0.0}


# Override the existing mental-health/analyze endpoint with safety pipeline
@app.post("/mental-health/analyze-safe")
async def analyze_mental_health_safe(
    audio: UploadFile = File(...),
    patient_id: str = Form(...),
    patient_name: str = Form(...),
    doctor_id: Optional[str] = Form(None),
    language: str = Form("en"),
):
    try:
        # Save audio temporarily
        audio_bytes = await audio.read()
        temp_path = f"/tmp/mental_health_{uuid.uuid4()}.m4a"
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)

        # Transcribe with Groq Whisper
        with open(temp_path, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=("audio.m4a", audio_file),
                model="whisper-large-v3-turbo",
                language=language if language != "en" else None,
            )

        transcript = transcription.text
        lang_instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["en"])

        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass

        # ── SAFETY PIPELINE ──
        # Step 1: Anonymize PII
        anonymized_transcript, anonymization_map = anonymize_transcript(transcript)

        # Step 2: Keyword pre-screening
        keyword_level, keyword_triggers = keyword_risk_screening(anonymized_transcript)

        # Step 3: LLM contextual classification
        llm_result = await llm_risk_classification(anonymized_transcript)
        llm_level = llm_result.get("level", 0)

        # Final level = MAX (safety-first: false positives > false negatives)
        final_level = max(keyword_level, llm_level)
        severity_label = SEVERITY_LABELS.get(final_level, "SAFE")

        # Step 4: Generate appropriate response
        safety_response = None
        crisis_resources_shown = False

        if final_level >= 2:
            safety_response = SAFETY_RESPONSES.get(final_level)
            crisis_resources_shown = final_level >= 2

        # Generate user-facing empathetic response
        if final_level >= 3:
            # For high/critical risk, use safety response directly
            user_message = safety_response
        else:
            # Standard empathetic response
            user_prompt = f"""You are a compassionate mental health companion for MedicoScope MindSpace.
A user just shared their feelings through a voice check-in. Here's their transcription:

"{anonymized_transcript}"

Provide a warm, empathetic, and detailed response that:
1. Acknowledges and validates their specific feelings with genuine empathy
2. Reflects back what they shared to show you truly listened
3. Offers 2-3 practical and personalized coping strategies relevant to what they described
4. Ends with an encouraging, hopeful note
{"5. Include mental health helpline numbers (AASRA: 9820466726, iCall: 9152987821) as a gentle resource." if final_level == 2 else ""}

Write 2-3 short paragraphs (8-12 sentences total). Be conversational and caring. {lang_instruction}"""

            user_response = llm.invoke(user_prompt)
            user_message = user_response.content

        # Step 5: Doctor alert for moderate+ risk
        doctor_report = None
        urgency = "low"

        if final_level >= 2 and doctor_id:
            # Generate clinical summary for doctor
            doctor_prompt = f"""You are a clinical mental health analyst. Write a brief clinical note for a doctor.

Patient: {patient_name}
Risk Level: {final_level}/4 ({severity_label})
Key Triggers: {keyword_triggers}
Anonymized Transcript: "{anonymized_transcript}"
LLM Assessment: {llm_result.get('reasoning', '')}

Provide:
1. Brief clinical summary (2-3 sentences)
2. Key risk indicators observed
3. Recommended immediate action
4. Urgency: {'CRITICAL - IMMEDIATE RESPONSE NEEDED' if final_level >= 4 else 'HIGH - URGENT FOLLOW-UP' if final_level >= 3 else 'MODERATE - SCHEDULE FOLLOW-UP'}

Format as a professional clinical note. Respond in English."""

            doctor_response = llm.invoke(doctor_prompt)
            doctor_report = doctor_response.content

            if final_level >= 4:
                urgency = "critical"
            elif final_level >= 3:
                urgency = "high"
            elif final_level >= 2:
                urgency = "moderate"

            # Save notification to Node.js backend
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    await client.post(
                        f"{BACKEND_URL}/mental-health/notifications",
                        json={
                            "doctorId": doctor_id,
                            "patientId": patient_id,
                            "patientName": patient_name,
                            "clinicalReport": doctor_report,
                            "urgency": urgency,
                            "transcript": anonymized_transcript,  # ANONYMIZED, not raw
                            "riskLevel": final_level,
                            "severityLabel": severity_label,
                            "requiresImmediateResponse": final_level >= 3,
                        },
                    )
            except Exception as notif_err:
                print(f"Warning: Failed to save notification: {notif_err}")

        elif doctor_id:
            # Standard report for low-risk
            doctor_prompt = f"""You are a clinical mental health analyst.
Analyze this patient's mental health check-in transcription and provide a clinical summary.

Patient: {patient_name}
Transcription: "{anonymized_transcript}"

Provide:
1. Brief clinical summary (2-3 sentences)
2. Key concerns identified
3. Recommended follow-up actions
4. Urgency level: low

Format as a professional clinical note. Respond in English."""

            doctor_response = llm.invoke(doctor_prompt)
            doctor_report = doctor_response.content

            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    await client.post(
                        f"{BACKEND_URL}/mental-health/notifications",
                        json={
                            "doctorId": doctor_id,
                            "patientId": patient_id,
                            "patientName": patient_name,
                            "clinicalReport": doctor_report,
                            "urgency": "low",
                            "transcript": anonymized_transcript,
                        },
                    )
            except Exception as notif_err:
                print(f"Warning: Failed to save notification: {notif_err}")

        return {
            "user_message": user_message,
            "transcript": transcript,
            "doctor_report": doctor_report,
            "urgency": urgency,
            "coins_earned": 10,
            # Safety pipeline results
            "risk_level": final_level,
            "severity_label": severity_label,
            "keyword_triggers": keyword_triggers,
            "crisis_resources_shown": crisis_resources_shown,
            "anonymized_transcript": anonymized_transcript,
            "safety_response_provided": safety_response is not None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
