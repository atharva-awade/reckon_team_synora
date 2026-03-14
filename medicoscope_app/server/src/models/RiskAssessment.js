const mongoose = require('mongoose');

const riskAssessmentSchema = new mongoose.Schema({
  patientId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
  },
  sessionId: { type: String, default: '' },
  riskLevel: {
    type: Number,
    enum: [0, 1, 2, 3, 4],
    required: true,
  },
  severityLabel: {
    type: String,
    enum: ['SAFE', 'LOW_RISK', 'MODERATE_RISK', 'HIGH_RISK', 'CRITICAL'],
    required: true,
  },
  keywordTriggers: [{ type: String }],
  llmReasoning: { type: String, default: '' },
  confidence: { type: Number, default: 0 },
  anonymizedTranscript: { type: String, default: '' },
  anonymizationMap: { type: mongoose.Schema.Types.Mixed, default: {} },
  doctorAlert: {
    sent: { type: Boolean, default: false },
    doctorId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', default: null },
    clinicalSummary: { type: String, default: '' },
    recommendedAction: { type: String, default: '' },
    requiresImmediateResponse: { type: Boolean, default: false },
  },
  safetyResponseProvided: { type: String, default: '' },
  crisisResourcesShown: { type: Boolean, default: false },
}, {
  timestamps: true,
});

riskAssessmentSchema.index({ patientId: 1, createdAt: -1 });
riskAssessmentSchema.index({ riskLevel: 1 });

module.exports = mongoose.model('RiskAssessment', riskAssessmentSchema);
