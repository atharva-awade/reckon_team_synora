require('dotenv').config();
const express = require('express');
const cors = require('cors');
const connectDB = require('./config/db');

const authRoutes = require('./routes/auth');
const userRoutes = require('./routes/users');
const doctorRoutes = require('./routes/doctors');
const patientRoutes = require('./routes/patients');
const detectionRoutes = require('./routes/detections');
const vitalsRoutes = require('./routes/vitals');
const chatRoutes = require('./routes/chat');
const mindspaceRoutes = require('./routes/mindspace');
const rewardsRoutes = require('./routes/rewards');
const mentalHealthRoutes = require('./routes/mental-health');
const claimedRewardsRoutes = require('./routes/claimed-rewards');
const adminRoutes = require('./routes/admin');
const nearbyDoctorsRoutes = require('./routes/nearby-doctors');
const healthProfileRoutes = require('./routes/health-profile');
const healthEventsRoutes = require('./routes/health-events');
const escalationsRoutes = require('./routes/escalations');
const documentsRoutes = require('./routes/documents');
const explainRoutes = require('./routes/explain');
const triageRoutes = require('./routes/triage');

const app = express();
const PORT = process.env.PORT || 5000;

console.log('Starting MedicoScope server...');
console.log(`PORT: ${PORT}`);
console.log(`MONGODB_URI set: ${!!process.env.MONGODB_URI}`);
console.log(`JWT_SECRET set: ${!!process.env.JWT_SECRET}`);

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);
app.use('/api/doctors', doctorRoutes);
app.use('/api/patients', patientRoutes);
app.use('/api/detections', detectionRoutes);
app.use('/api/vitals', vitalsRoutes);
app.use('/api/chat', chatRoutes);
app.use('/api/mindspace', mindspaceRoutes);
app.use('/api/rewards', rewardsRoutes);
app.use('/api/mental-health', mentalHealthRoutes);
app.use('/api/claimed-rewards', claimedRewardsRoutes);
app.use('/api/admin', adminRoutes);
app.use('/api/nearby-doctors', nearbyDoctorsRoutes);
app.use('/api/health-profile', healthProfileRoutes);
app.use('/api/health-events', healthEventsRoutes);
app.use('/api/escalations', escalationsRoutes);
app.use('/api/documents', documentsRoutes);
app.use('/api/explain', explainRoutes);
app.use('/api/triage', triageRoutes);

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Connect DB and start server
connectDB().then(() => {
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`MedicoScope server running on port ${PORT}`);
  });
}).catch((err) => {
  console.error('Failed to start server:', err.message || err);
  process.exit(1);
});
