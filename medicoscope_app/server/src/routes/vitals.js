const express = require('express');
const auth = require('../middleware/auth');
const roleCheck = require('../middleware/roleCheck');
const VitalsSummary = require('../models/VitalsSummary');
const VitalsAlert = require('../models/VitalsAlert');

const router = express.Router();

// POST /api/vitals/summary - save a vitals session summary (patient only)
router.post('/summary', auth, roleCheck('patient'), async (req, res) => {
  try {
    const {
      sessionId,
      duration,
      dataPointCount,
      avgHeartRate,
      maxHeartRate,
      minHeartRate,
      avgSystolic,
      maxSystolic,
      avgDiastolic,
      avgSpO2,
      minSpO2,
      alerts,
      location,
    } = req.body;

    if (!sessionId) {
      return res.status(400).json({ message: 'sessionId is required' });
    }

    const summary = await VitalsSummary.create({
      patientId: req.user._id,
      sessionId,
      duration: duration || 0,
      dataPointCount: dataPointCount || 0,
      avgHeartRate: avgHeartRate || 0,
      maxHeartRate: maxHeartRate || 0,
      minHeartRate: minHeartRate || 0,
      avgSystolic: avgSystolic || 0,
      maxSystolic: maxSystolic || 0,
      avgDiastolic: avgDiastolic || 0,
      avgSpO2: avgSpO2 || 0,
      minSpO2: minSpO2 || 0,
      alerts: alerts || [],
      location: location || 'Unknown',
    });

    res.status(201).json({ summary });
  } catch (error) {
    console.error('Save vitals summary error:', error);
    res.status(500).json({ message: 'Server error saving vitals summary' });
  }
});

// GET /api/vitals/summaries - get own vitals summaries (patient)
router.get('/summaries', auth, roleCheck('patient'), async (req, res) => {
  try {
    const summaries = await VitalsSummary.find({ patientId: req.user._id })
      .sort({ createdAt: -1 })
      .limit(20);

    res.json({ summaries });
  } catch (error) {
    console.error('Fetch vitals summaries error:', error);
    res.status(500).json({ message: 'Server error fetching vitals summaries' });
  }
});

// GET /api/vitals/summaries/:patientId - get patient's vitals summaries (doctor)
router.get('/summaries/:patientId', auth, roleCheck('doctor'), async (req, res) => {
  try {
    const summaries = await VitalsSummary.find({ patientId: req.params.patientId })
      .sort({ createdAt: -1 })
      .limit(20);

    res.json({ summaries });
  } catch (error) {
    console.error('Fetch patient vitals error:', error);
    res.status(500).json({ message: 'Server error fetching patient vitals' });
  }
});

// ── Persistent Vitals Alerts (MongoDB) ────────────────────────────────────

// POST /api/vitals/alerts - Save a vitals alert (called from app)
router.post('/alerts', auth, async (req, res) => {
  try {
    const {
      patientId, doctorId, patientName, type, severity, message,
      vital, currentValue, predictedValue, location,
      latitude, longitude, mapsUrl,
      emergencyContactName, emergencyContactPhone,
    } = req.body;

    const alert = await VitalsAlert.create({
      patientId: patientId || req.user._id.toString(),
      doctorId: doctorId || '',
      patientName: patientName || '',
      type: type || 'threshold_breach',
      severity: severity || 'high',
      message: message || '',
      vital: vital || '',
      currentValue: currentValue || 0,
      predictedValue: predictedValue || 0,
      location: location || '',
      latitude: latitude || 0,
      longitude: longitude || 0,
      mapsUrl: mapsUrl || '',
      emergencyContactName: emergencyContactName || '',
      emergencyContactPhone: emergencyContactPhone || '',
      doctorNotified: !!doctorId,
      emergencyNotified: !!emergencyContactPhone,
    });

    res.status(201).json({ alert });
  } catch (error) {
    console.error('Save vitals alert error:', error);
    res.status(500).json({ message: 'Server error saving alert' });
  }
});

// GET /api/vitals/alerts/doctor/:doctorId - Get alerts for doctor
router.get('/alerts/doctor/:doctorId', auth, async (req, res) => {
  try {
    const alerts = await VitalsAlert.find({ doctorId: req.params.doctorId })
      .sort({ createdAt: -1 })
      .limit(50)
      .lean();

    const mapped = alerts.map(a => ({
      id: a._id.toString(),
      type: a.type,
      alert_type: a.type,
      severity: a.severity,
      message: a.message,
      vital: a.vital,
      current_value: a.currentValue,
      predicted_value: a.predictedValue,
      timestamp: a.createdAt.toISOString(),
      location: a.location,
      latitude: a.latitude,
      longitude: a.longitude,
      maps_url: a.mapsUrl,
      emergency_contact_name: a.emergencyContactName,
      emergency_contact_phone: a.emergencyContactPhone,
      patient_id: a.patientId,
      patient_name: a.patientName,
      doctor_id: a.doctorId,
      doctor_notified: a.doctorNotified,
      emergency_notified: a.emergencyNotified,
      read: a.read,
      created_at: a.createdAt.toISOString(),
    }));

    res.json({ alerts: mapped });
  } catch (error) {
    console.error('Get doctor vitals alerts error:', error);
    res.status(500).json({ message: 'Server error' });
  }
});

// GET /api/vitals/alerts/patient/:patientId - Get alerts for patient
router.get('/alerts/patient/:patientId', auth, async (req, res) => {
  try {
    const alerts = await VitalsAlert.find({ patientId: req.params.patientId })
      .sort({ createdAt: -1 })
      .limit(50)
      .lean();

    const mapped = alerts.map(a => ({
      id: a._id.toString(),
      type: a.type,
      alert_type: a.type,
      severity: a.severity,
      message: a.message,
      vital: a.vital,
      current_value: a.currentValue,
      predicted_value: a.predictedValue,
      timestamp: a.createdAt.toISOString(),
      location: a.location,
      latitude: a.latitude,
      longitude: a.longitude,
      maps_url: a.mapsUrl,
      emergency_contact_name: a.emergencyContactName,
      emergency_contact_phone: a.emergencyContactPhone,
      patient_id: a.patientId,
      patient_name: a.patientName,
      doctor_id: a.doctorId,
      doctor_notified: a.doctorNotified,
      emergency_notified: a.emergencyNotified,
      read: a.read,
      created_at: a.createdAt.toISOString(),
    }));

    res.json({ alerts: mapped });
  } catch (error) {
    console.error('Get patient vitals alerts error:', error);
    res.status(500).json({ message: 'Server error' });
  }
});

// PUT /api/vitals/alerts/:id/read - Mark alert as read
router.put('/alerts/:id/read', auth, async (req, res) => {
  try {
    await VitalsAlert.findByIdAndUpdate(req.params.id, { read: true });
    res.json({ status: 'ok' });
  } catch (error) {
    res.status(500).json({ message: 'Server error' });
  }
});

// DELETE /api/vitals/alerts/:id - Delete alert
router.delete('/alerts/:id', auth, async (req, res) => {
  try {
    await VitalsAlert.findByIdAndDelete(req.params.id);
    res.json({ status: 'deleted' });
  } catch (error) {
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;
