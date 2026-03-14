const mongoose = require('mongoose');

const documentSchema = new mongoose.Schema({
  patientId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
  },
  documentType: {
    type: String,
    enum: ['blood_test_report', 'lab_report', 'imaging_report', 'prescription', 'discharge_summary', 'pathology_report', 'ecg_report', 'unknown'],
    default: 'unknown',
  },
  fileName: { type: String, default: '' },
  extractedText: { type: String, default: '' },
  parsedData: {
    tests: [{
      name: String,
      value: Number,
      unit: String,
      referenceRange: { min: Number, max: Number },
      status: { type: String, enum: ['NORMAL', 'LOW', 'HIGH', 'CRITICAL_LOW', 'CRITICAL_HIGH'] },
      category: String,
    }],
    patientInfo: {
      name: String,
      age: String,
      date: String,
    },
    orderingDoctor: String,
    labName: String,
    reportDate: String,
  },
  abnormalValues: [{
    name: String,
    value: Number,
    unit: String,
    flag: String,
    normalRange: String,
    deviation: String,
  }],
  explanation: {
    summary: { type: String, default: '' },
    keyFindings: [{ type: String }],
    whatThisMeans: { type: String, default: '' },
    correlations: [{ type: String }],
    recommendedActions: [{ type: String }],
    questionsForDoctor: [{ type: String }],
  },
  urgency: {
    type: String,
    enum: ['routine', 'follow_up', 'urgent'],
    default: 'routine',
  },
}, {
  timestamps: true,
});

documentSchema.index({ patientId: 1, createdAt: -1 });

module.exports = mongoose.model('Document', documentSchema);
