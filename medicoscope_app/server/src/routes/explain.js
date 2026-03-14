const express = require('express');
const auth = require('../middleware/auth');
const ExplainableResult = require('../models/ExplainableResult');
const HealthProfile = require('../models/HealthProfile');
const HealthEvent = require('../models/HealthEvent');

const router = express.Router();

const CHATBOT_URL = process.env.CHATBOT_URL || 'https://medicoscope-chatbot-mu7p.onrender.com';

// POST /api/explain - Generate explainable AI result for a detection
router.post('/', auth, async (req, res) => {
  try {
    const { detection, vitalsBaseline, language, detectionId } = req.body;

    // Fetch patient's health profile for personalization
    const healthProfile = await HealthProfile.findOne({ userId: req.user._id });

    // Forward to Python service
    const fetch = (await import('node-fetch')).default;
    const pythonResponse = await fetch(`${CHATBOT_URL}/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        detection,
        patient_profile: healthProfile ? {
          age: healthProfile.demographics?.age || 0,
          sex: healthProfile.demographics?.sex || 'other',
          chronic_conditions: healthProfile.medicalHistory?.chronicConditions || [],
          family_history: healthProfile.medicalHistory?.familyHistory || [],
          allergies: healthProfile.medicalHistory?.allergies || [],
          smoking_status: healthProfile.lifestyle?.smokingStatus || 'never',
          medications: (healthProfile.currentMedications || []).map(m => m.name),
          bmi: healthProfile.demographics?.bmi || 0,
        } : {},
        vitals_baseline: vitalsBaseline || {},
        language: language || 'en',
      }),
    });

    if (!pythonResponse.ok) {
      throw new Error(`Python service error: ${pythonResponse.status}`);
    }

    const explanation = await pythonResponse.json();

    // Save to MongoDB
    const result = await ExplainableResult.create({
      detectionId: detectionId || null,
      patientId: req.user._id,
      condition: explanation.condition || { name: detection.class_name },
      whatItIs: explanation.what_it_is || '',
      whyItOccurs: explanation.why_it_occurs || '',
      howItAffectsBody: explanation.how_it_affects_body || '',
      aiConfidence: explanation.ai_confidence || { score: detection.confidence },
      associatedSymptoms: explanation.associated_symptoms || [],
      immediatePrecautions: explanation.immediate_precautions || [],
      lifestyleImprovements: explanation.lifestyle_improvements || [],
      whenToConsult: explanation.when_to_consult || {},
      personalizedRiskContext: explanation.personalized_risk_context || '',
    });

    // Record health event
    await HealthEvent.create({
      patientId: req.user._id,
      eventType: 'detection',
      data: {
        className: detection.class_name,
        confidence: detection.confidence,
        category: detection.category,
        explanationId: result._id,
      },
    });

    res.json({ explanation: result });
  } catch (error) {
    console.error('Explain error:', error);
    res.status(500).json({ message: 'Server error generating explanation' });
  }
});

// GET /api/explain/:detectionId - Get cached explanation for a detection
router.get('/:detectionId', auth, async (req, res) => {
  try {
    const result = await ExplainableResult.findOne({ detectionId: req.params.detectionId });
    res.json({ explanation: result || null });
  } catch (error) {
    res.status(500).json({ message: 'Server error fetching explanation' });
  }
});

module.exports = router;
