const express = require('express');
const auth = require('../middleware/auth');
const HealthProfile = require('../models/HealthProfile');
const HealthEvent = require('../models/HealthEvent');

const router = express.Router();

const CHATBOT_URL = process.env.CHATBOT_URL || 'https://medicoscope-chatbot-mu7p.onrender.com';

// POST /api/triage - Run symptom triage to recommend diagnostic module
router.post('/', auth, async (req, res) => {
  try {
    const { symptoms, language } = req.body;

    // Fetch health profile and recent events for context
    const healthProfile = await HealthProfile.findOne({ userId: req.user._id });
    const recentEvents = await HealthEvent.find({ patientId: req.user._id })
      .sort({ createdAt: -1 })
      .limit(10);

    // Forward to Python triage engine
    const fetch = (await import('node-fetch')).default;
    const pythonResponse = await fetch(`${CHATBOT_URL}/triage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symptoms: symptoms || [],
        patient_profile: healthProfile ? {
          age: healthProfile.demographics?.age || 0,
          sex: healthProfile.demographics?.sex || 'other',
          chronic_conditions: healthProfile.medicalHistory?.chronicConditions || [],
          risk_score: healthProfile.riskScore || 0,
        } : {},
        recent_events: recentEvents.map(e => ({
          type: e.eventType,
          data: e.data,
          date: e.createdAt,
        })),
        language: language || 'en',
      }),
    });

    if (!pythonResponse.ok) {
      throw new Error(`Python triage error: ${pythonResponse.status}`);
    }

    const triageResult = await pythonResponse.json();

    // Record triage event
    await HealthEvent.create({
      patientId: req.user._id,
      eventType: 'triage',
      data: {
        symptoms,
        recommendedModule: triageResult.recommended_module,
        urgency: triageResult.urgency,
        reasoning: triageResult.reasoning,
      },
    });

    res.json({
      recommendedModule: triageResult.recommended_module,
      urgency: triageResult.urgency,
      reasoning: triageResult.reasoning,
      alternativeModules: triageResult.alternative_modules || [],
      followUpQuestions: triageResult.follow_up_questions || [],
    });
  } catch (error) {
    console.error('Triage error:', error);
    res.status(500).json({ message: 'Server error running triage' });
  }
});

module.exports = router;
