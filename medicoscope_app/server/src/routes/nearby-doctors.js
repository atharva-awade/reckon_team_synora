const express = require('express');
const auth = require('../middleware/auth');
const NearbyDoctor = require('../models/NearbyDoctor');

const router = express.Router();

// GET /api/nearby-doctors/search?lat=...&lng=...&radius=...&specialization=...
// Search nearby doctors based on user's location
router.get('/search', auth, async (req, res) => {
  try {
    const { lat, lng, radius, specialization } = req.query;

    if (!lat || !lng) {
      return res.status(400).json({ message: 'Latitude and longitude are required' });
    }

    const latitude = parseFloat(lat);
    const longitude = parseFloat(lng);
    const maxDistance = parseInt(radius) || 10000; // Default 10km in meters

    const query = {
      location: {
        $near: {
          $geometry: {
            type: 'Point',
            coordinates: [longitude, latitude],
          },
          $maxDistance: maxDistance,
        },
      },
    };

    // Filter by specialization if provided
    if (specialization && specialization !== 'All') {
      query.specialization = { $regex: new RegExp(specialization, 'i') };
    }

    const nearbyDoctors = await NearbyDoctor.find(query);

    // Calculate distance for each doctor
    const doctorsWithDistance = nearbyDoctors.map((doc) => {
      const docObj = doc.toObject();
      const [docLng, docLat] = doc.location.coordinates;
      docObj.distance = calculateDistance(latitude, longitude, docLat, docLng);
      return docObj;
    });

    res.json({ nearbyDoctors: doctorsWithDistance });
  } catch (error) {
    console.error('Nearby doctors search error:', error);
    res.status(500).json({ message: 'Server error' });
  }
});

// GET /api/nearby-doctors/specializations - Get list of available specializations
router.get('/specializations', auth, async (req, res) => {
  try {
    const specializations = await NearbyDoctor.distinct('specialization');
    res.json({ specializations });
  } catch (error) {
    console.error('Get specializations error:', error);
    res.status(500).json({ message: 'Server error' });
  }
});

// Haversine formula to calculate distance in meters
function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371000; // Earth's radius in meters
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c);
}

function toRad(deg) {
  return deg * (Math.PI / 180);
}

// POST /api/nearby-doctors/seed - Seed demo doctors around a location (for hackathon demo)
router.post('/seed', async (req, res) => {
  try {
    const { latitude, longitude } = req.body;
    const lat = parseFloat(latitude) || 26.2389;  // Default: Jodhpur
    const lng = parseFloat(longitude) || 73.0243;

    // Check if seed data already exists
    const existing = await NearbyDoctor.countDocuments();
    if (existing >= 10) {
      return res.json({ message: 'Seed data already exists', count: existing });
    }

    const demoDoctors = [
      { name: 'Dr. Arun Sharma', hospitalName: 'City Care Hospital', contactNumber: '+91-9876543210', specialization: 'General Medicine', offset: [0.005, 0.003], address: 'MG Road, Near Clock Tower' },
      { name: 'Dr. Priya Meena', hospitalName: 'Lifeline Clinic', contactNumber: '+91-9876543211', specialization: 'Cardiology', offset: [-0.008, 0.006], address: 'Sardarpura, Main Road' },
      { name: 'Dr. Rajesh Patel', hospitalName: 'Mahatma Gandhi Hospital', contactNumber: '+91-9876543212', specialization: 'Dermatology', offset: [0.012, -0.004], address: 'Residency Road' },
      { name: 'Dr. Sunita Rathore', hospitalName: 'Sun City Hospital', contactNumber: '+91-9876543213', specialization: 'Pulmonology', offset: [-0.003, -0.009], address: 'Paota Circle' },
      { name: 'Dr. Vikram Singh', hospitalName: 'Goyal Hospital', contactNumber: '+91-9876543214', specialization: 'Neurology', offset: [0.015, 0.010], address: 'Ratanada' },
      { name: 'Dr. Kavita Joshi', hospitalName: 'Medipulse Hospital', contactNumber: '+91-9876543215', specialization: 'Psychiatry', offset: [-0.010, 0.012], address: '3rd Road, Sardarpura' },
      { name: 'Dr. Mahesh Gehlot', hospitalName: 'AIIMS Jodhpur', contactNumber: '+91-9876543216', specialization: 'Orthopedics', offset: [0.020, -0.015], address: 'Basni Industrial Area' },
      { name: 'Dr. Nisha Chauhan', hospitalName: 'Umaid Hospital', contactNumber: '+91-9876543217', specialization: 'Pediatrics', offset: [-0.006, -0.005], address: 'High Court Colony' },
      { name: 'Dr. Deepak Vyas', hospitalName: 'SN Medical College', contactNumber: '+91-9876543218', specialization: 'Radiology', offset: [0.008, 0.015], address: 'Shastri Nagar' },
      { name: 'Dr. Anita Kumari', hospitalName: 'Jeevan Rekha Hospital', contactNumber: '+91-9876543219', specialization: 'Emergency Medicine', offset: [-0.014, 0.008], address: 'Chopasni Road' },
    ];

    const created = [];
    for (const doc of demoDoctors) {
      const nearbyDoc = await NearbyDoctor.create({
        name: doc.name,
        hospitalName: doc.hospitalName,
        contactNumber: doc.contactNumber,
        specialization: doc.specialization,
        location: {
          type: 'Point',
          coordinates: [lng + doc.offset[1], lat + doc.offset[0]],
        },
        address: doc.address,
        addedBy: '000000000000000000000000', // placeholder
      });
      created.push(nearbyDoc.name);
    }

    res.status(201).json({ message: 'Seeded demo doctors', doctors: created });
  } catch (error) {
    console.error('Seed nearby doctors error:', error);
    res.status(500).json({ message: 'Server error seeding doctors' });
  }
});

module.exports = router;
