const express = require('express');
const auth = require('../middleware/auth');
const HealthEvent = require('../models/HealthEvent');

const router = express.Router();

// POST /api/health-events - Record a health event
router.post('/', auth, async (req, res) => {
  try {
    const { patientId, eventType, data, linkedDoctor, escalation } = req.body;

    const event = await HealthEvent.create({
      patientId: patientId || req.user._id,
      eventType,
      data: data || {},
      linkedDoctor: linkedDoctor || null,
      escalation: escalation || {},
    });

    res.status(201).json({ event });
  } catch (error) {
    console.error('Health event save error:', error);
    res.status(500).json({ message: 'Server error saving health event' });
  }
});

// GET /api/health-events - Get health timeline for current patient
router.get('/', auth, async (req, res) => {
  try {
    const { eventType, limit = 50 } = req.query;
    const filter = { patientId: req.user._id };
    if (eventType) filter.eventType = eventType;

    const events = await HealthEvent.find(filter)
      .sort({ createdAt: -1 })
      .limit(parseInt(limit))
      .populate('linkedDoctor', 'name');

    res.json({ events });
  } catch (error) {
    console.error('Health events fetch error:', error);
    res.status(500).json({ message: 'Server error fetching health events' });
  }
});

// GET /api/health-events/patient/:patientId - Get timeline for a specific patient (doctor view)
router.get('/patient/:patientId', auth, async (req, res) => {
  try {
    const { eventType, limit = 50 } = req.query;
    const filter = { patientId: req.params.patientId };
    if (eventType) filter.eventType = eventType;

    const events = await HealthEvent.find(filter)
      .sort({ createdAt: -1 })
      .limit(parseInt(limit));

    res.json({ events });
  } catch (error) {
    console.error('Health events fetch error:', error);
    res.status(500).json({ message: 'Server error fetching health events' });
  }
});

module.exports = router;
