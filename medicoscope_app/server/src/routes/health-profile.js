const express = require('express');
const auth = require('../middleware/auth');
const HealthProfile = require('../models/HealthProfile');

const router = express.Router();

// POST /api/health-profile - Create or update health profile
router.post('/', auth, async (req, res) => {
  try {
    const {
      demographics, medicalHistory, lifestyle,
      currentMedications, primarySymptoms,
    } = req.body;

    let profile = await HealthProfile.findOne({ userId: req.user._id });

    if (profile) {
      // Update existing
      if (demographics) profile.demographics = { ...profile.demographics.toObject(), ...demographics };
      if (medicalHistory) profile.medicalHistory = { ...profile.medicalHistory.toObject(), ...medicalHistory };
      if (lifestyle) profile.lifestyle = { ...profile.lifestyle.toObject(), ...lifestyle };
      if (currentMedications) profile.currentMedications = currentMedications;
      if (primarySymptoms) profile.primarySymptoms = primarySymptoms;
      profile.isComplete = true;

      // Compute risk score
      profile.riskScore = computeRiskScore(profile);
      await profile.save();
    } else {
      // Create new
      profile = new HealthProfile({
        userId: req.user._id,
        demographics: demographics || {},
        medicalHistory: medicalHistory || {},
        lifestyle: lifestyle || {},
        currentMedications: currentMedications || [],
        primarySymptoms: primarySymptoms || [],
        isComplete: true,
      });
      profile.riskScore = computeRiskScore(profile);
      await profile.save();
    }

    res.json({ profile });
  } catch (error) {
    console.error('Health profile save error:', error);
    res.status(500).json({ message: 'Server error saving health profile' });
  }
});

// GET /api/health-profile - Get current user's health profile
router.get('/', auth, async (req, res) => {
  try {
    const profile = await HealthProfile.findOne({ userId: req.user._id });
    res.json({ profile: profile || null, isComplete: profile?.isComplete || false });
  } catch (error) {
    console.error('Health profile fetch error:', error);
    res.status(500).json({ message: 'Server error fetching health profile' });
  }
});

// GET /api/health-profile/:patientId - Get a patient's health profile (for doctors)
router.get('/:patientId', auth, async (req, res) => {
  try {
    const profile = await HealthProfile.findOne({ userId: req.params.patientId });
    res.json({ profile: profile || null });
  } catch (error) {
    console.error('Health profile fetch error:', error);
    res.status(500).json({ message: 'Server error fetching health profile' });
  }
});

function computeRiskScore(profile) {
  let score = 0;
  const d = profile.demographics || {};
  const m = profile.medicalHistory || {};
  const l = profile.lifestyle || {};

  // Age risk
  if (d.age > 60) score += 20;
  else if (d.age > 45) score += 10;
  else if (d.age > 30) score += 5;

  // BMI risk
  if (d.bmi > 35) score += 15;
  else if (d.bmi > 30) score += 10;
  else if (d.bmi > 25) score += 5;

  // Chronic conditions
  const conditions = m.chronicConditions || [];
  score += conditions.length * 8;

  // Family history
  const family = m.familyHistory || [];
  score += family.length * 5;

  // Lifestyle
  if (l.smokingStatus === 'current') score += 15;
  else if (l.smokingStatus === 'former') score += 5;

  if (l.alcoholConsumption === 'heavy') score += 10;
  else if (l.alcoholConsumption === 'moderate') score += 3;

  if (l.exerciseFrequency === 'none') score += 8;
  else if (l.exerciseFrequency === 'light') score += 3;

  // Allergies
  score += (m.allergies || []).length * 2;

  return Math.min(100, score);
}

module.exports = router;
