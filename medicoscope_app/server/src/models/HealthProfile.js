const mongoose = require('mongoose');

const healthProfileSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    unique: true,
  },
  demographics: {
    age: { type: Number, default: 0 },
    sex: { type: String, enum: ['male', 'female', 'other'], default: 'other' },
    height_cm: { type: Number, default: 0 },
    weight_kg: { type: Number, default: 0 },
    bmi: { type: Number, default: 0 },
  },
  medicalHistory: {
    chronicConditions: [{ type: String }],
    surgeries: [{
      name: String,
      year: Number,
    }],
    familyHistory: [{
      condition: String,
      relation: String,
    }],
    allergies: [{ type: String }],
  },
  lifestyle: {
    smokingStatus: { type: String, enum: ['never', 'former', 'current'], default: 'never' },
    alcoholConsumption: { type: String, enum: ['none', 'occasional', 'moderate', 'heavy'], default: 'none' },
    exerciseFrequency: { type: String, enum: ['none', 'light', 'moderate', 'active', 'very_active'], default: 'none' },
    dietType: { type: String, default: 'regular' },
  },
  currentMedications: [{
    name: String,
    dosage: String,
    frequency: String,
    startDate: String,
  }],
  primarySymptoms: [{ type: String }],
  riskScore: { type: Number, default: 0 },
  isComplete: { type: Boolean, default: false },
}, {
  timestamps: true,
});

// Auto-compute BMI before save
healthProfileSchema.pre('save', function (next) {
  if (this.demographics.height_cm > 0 && this.demographics.weight_kg > 0) {
    const heightM = this.demographics.height_cm / 100;
    this.demographics.bmi = parseFloat((this.demographics.weight_kg / (heightM * heightM)).toFixed(1));
  }
  next();
});

module.exports = mongoose.model('HealthProfile', healthProfileSchema);
