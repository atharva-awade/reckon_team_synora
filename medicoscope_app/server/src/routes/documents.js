const express = require('express');
const auth = require('../middleware/auth');
const Document = require('../models/Document');
const HealthEvent = require('../models/HealthEvent');
const httpProxy = require('http');

const router = express.Router();

const CHATBOT_URL = process.env.CHATBOT_URL || 'https://medicoscope-chatbot-mu7p.onrender.com';

// POST /api/documents/upload - Upload and parse medical document
router.post('/upload', auth, async (req, res) => {
  try {
    const { extractedText, fileName, documentType } = req.body;

    // Forward to Python service for parsing
    const fetch = (await import('node-fetch')).default;
    const pythonResponse = await fetch(`${CHATBOT_URL}/documents/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: extractedText,
        file_name: fileName || 'document',
        patient_id: req.user._id.toString(),
      }),
    });

    if (!pythonResponse.ok) {
      throw new Error(`Python service error: ${pythonResponse.status}`);
    }

    const parsed = await pythonResponse.json();

    // Save to MongoDB
    const doc = await Document.create({
      patientId: req.user._id,
      documentType: parsed.document_type || documentType || 'unknown',
      fileName: fileName || '',
      extractedText: extractedText || '',
      parsedData: parsed.parsed_data || {},
      abnormalValues: parsed.abnormal_values || [],
      explanation: parsed.explanation || {},
      urgency: parsed.urgency || 'routine',
    });

    // Record health event
    await HealthEvent.create({
      patientId: req.user._id,
      eventType: 'document_upload',
      data: {
        documentId: doc._id,
        documentType: doc.documentType,
        keyFindings: (parsed.abnormal_values || []).map(v => `${v.name}: ${v.flag}`),
        urgency: doc.urgency,
      },
    });

    res.status(201).json({ document: doc });
  } catch (error) {
    console.error('Document upload error:', error);
    res.status(500).json({ message: 'Server error processing document' });
  }
});

// GET /api/documents - List patient's documents
router.get('/', auth, async (req, res) => {
  try {
    const docs = await Document.find({ patientId: req.user._id })
      .sort({ createdAt: -1 })
      .select('-extractedText') // Don't send full text in list view
      .limit(50);

    res.json({ documents: docs });
  } catch (error) {
    console.error('Documents fetch error:', error);
    res.status(500).json({ message: 'Server error fetching documents' });
  }
});

// GET /api/documents/:id - Get full parsed document
router.get('/:id', auth, async (req, res) => {
  try {
    const doc = await Document.findById(req.params.id);
    if (!doc) return res.status(404).json({ message: 'Document not found' });
    res.json({ document: doc });
  } catch (error) {
    console.error('Document fetch error:', error);
    res.status(500).json({ message: 'Server error fetching document' });
  }
});

// GET /api/documents/patient/:patientId - Doctor view of patient documents
router.get('/patient/:patientId', auth, async (req, res) => {
  try {
    const docs = await Document.find({ patientId: req.params.patientId })
      .sort({ createdAt: -1 })
      .limit(50);

    res.json({ documents: docs });
  } catch (error) {
    res.status(500).json({ message: 'Server error fetching documents' });
  }
});

module.exports = router;
