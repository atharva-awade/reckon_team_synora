const mongoose = require('mongoose');

const explainableResultSchema = new mongoose.Schema({
  detectionId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'DetectionRecord',
    default: null,
  },
  patientId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
  },
  condition: {
    name: { type: String, required: true },
    laymanName: { type: String, default: '' },
    category: { type: String, default: '' },
  },
  whatItIs: { type: String, default: '' },
  whyItOccurs: { type: String, default: '' },
  howItAffectsBody: { type: String, default: '' },
  aiConfidence: {
    score: { type: Number, default: 0 },
    interpretation: { type: String, default: '' },
    explanation: { type: String, default: '' },
    factorsAffectingConfidence: [{ type: String }],
  },
  associatedSymptoms: [{ type: String }],
  immediatePrecautions: [{ type: String }],
  lifestyleImprovements: [{ type: String }],
  whenToConsult: {
    urgency: { type: String, default: 'routine' },
    specialist: { type: String, default: '' },
    reason: { type: String, default: '' },
    whatDoctorWillDo: { type: String, default: '' },
  },
  personalizedRiskContext: { type: String, default: '' },
  disclaimer: { type: String, default: 'This AI analysis is for screening purposes only and does not constitute a medical diagnosis. Always consult a qualified healthcare professional.' },
}, {
  timestamps: true,
});

explainableResultSchema.index({ patientId: 1, createdAt: -1 });
explainableResultSchema.index({ detectionId: 1 });

module.exports = mongoose.model('ExplainableResult', explainableResultSchema);
