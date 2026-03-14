const mongoose = require('mongoose');

const healthEventSchema = new mongoose.Schema({
  patientId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true,
  },
  eventType: {
    type: String,
    enum: ['detection', 'vitals_session', 'chat_session', 'mindspace', 'document_upload', 'triage'],
    required: true,
  },
  data: {
    // Polymorphic — depends on eventType
    // detection: { className, confidence, category, explanation }
    // vitals_session: { duration, avgHR, avgBP, alerts[] }
    // chat_session: { sessionId, topicSummary }
    // mindspace: { transcript, urgency, riskLevel }
    // document_upload: { documentType, keyFindings[], urgency }
    // triage: { recommendedModule, urgency, reasoning }
    type: mongoose.Schema.Types.Mixed,
    default: {},
  },
  linkedDoctor: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    default: null,
  },
  escalation: {
    type: { type: String, enum: ['immediate', 'priority', 'routine', null], default: null },
    status: { type: String, enum: ['pending', 'acknowledged', 'resolved', null], default: null },
    responseTime: { type: Number, default: null }, // minutes
  },
}, {
  timestamps: true,
});

healthEventSchema.index({ patientId: 1, createdAt: -1 });
healthEventSchema.index({ patientId: 1, eventType: 1 });

module.exports = mongoose.model('HealthEvent', healthEventSchema);
