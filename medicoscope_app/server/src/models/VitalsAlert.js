const mongoose = require('mongoose');

const vitalsAlertSchema = new mongoose.Schema({
  patientId: {
    type: String,
    required: true,
    index: true,
  },
  doctorId: {
    type: String,
    default: '',
    index: true,
  },
  patientName: { type: String, default: '' },
  type: { type: String, default: 'threshold_breach' },
  severity: { type: String, enum: ['critical', 'high', 'warning', 'low'], default: 'high' },
  message: { type: String, default: '' },
  vital: { type: String, default: '' },
  currentValue: { type: Number, default: 0 },
  predictedValue: { type: Number, default: 0 },
  location: { type: String, default: '' },
  latitude: { type: Number, default: 0 },
  longitude: { type: Number, default: 0 },
  mapsUrl: { type: String, default: '' },
  emergencyContactName: { type: String, default: '' },
  emergencyContactPhone: { type: String, default: '' },
  read: { type: Boolean, default: false },
  doctorNotified: { type: Boolean, default: false },
  emergencyNotified: { type: Boolean, default: false },
}, {
  timestamps: true,
});

vitalsAlertSchema.index({ doctorId: 1, createdAt: -1 });
vitalsAlertSchema.index({ patientId: 1, createdAt: -1 });

module.exports = mongoose.model('VitalsAlert', vitalsAlertSchema);
