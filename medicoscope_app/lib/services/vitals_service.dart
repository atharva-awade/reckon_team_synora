import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:medicoscope/core/constants/api_constants.dart';
import 'package:medicoscope/services/api_service.dart';

class VitalsService {
  /// Save a vitals session summary to MongoDB via Node.js backend.
  static Future<void> saveSessionSummary({
    required String token,
    required Map<String, dynamic> sessionData,
  }) async {
    final api = ApiService(token: token);
    await api.post(ApiConstants.vitalsSummary, sessionData);
  }

  static Future<Map<String, dynamic>> startSession({
    required String patientId,
    required String patientName,
    required String doctorId,
    String emergencyContactName = '',
    String emergencyContactPhone = '',
    String location = 'Unknown',
    double latitude = 0.0,
    double longitude = 0.0,
  }) async {
    final url = Uri.parse(
      '${ApiConstants.chatbotBaseUrl}${ApiConstants.vitalsStart}',
    );

    final response = await http
        .post(
          url,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'patient_id': patientId,
            'patient_name': patientName,
            'doctor_id': doctorId,
            'emergency_contact_name': emergencyContactName,
            'emergency_contact_phone': emergencyContactPhone,
            'location': location,
            'latitude': latitude,
            'longitude': longitude,
          }),
        )
        .timeout(const Duration(seconds: 30));

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else if (response.statusCode == 503) {
      throw Exception('Service is warming up. Please try again in a moment.');
    } else {
      throw Exception('Failed to start session: ${response.statusCode}');
    }
  }

  static Future<Map<String, dynamic>> tick({
    required String sessionId,
  }) async {
    final url = Uri.parse(
      '${ApiConstants.chatbotBaseUrl}${ApiConstants.vitalsTick}',
    );

    final response = await http
        .post(
          url,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'session_id': sessionId}),
        )
        .timeout(const Duration(seconds: 5));

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else if (response.statusCode == 404) {
      throw Exception('Session expired or not found.');
    } else {
      throw Exception('Tick failed: ${response.statusCode}');
    }
  }

  static Future<void> stopSession({required String sessionId}) async {
    final url = Uri.parse(
      '${ApiConstants.chatbotBaseUrl}${ApiConstants.vitalsSession}/$sessionId',
    );

    await http.delete(url).timeout(const Duration(seconds: 10));
  }

  // ── Persistent alert methods (via Node.js → MongoDB) ───────────────────

  /// Save a vitals alert — tries Node.js MongoDB first, then Python in-memory
  static Future<void> saveAlert({
    required String token,
    required Map<String, dynamic> alertData,
  }) async {
    // Try Node.js MongoDB (persistent)
    try {
      final api = ApiService(token: token);
      await api.post('/vitals/alerts', alertData);
      return; // Success — no need for fallback
    } catch (_) {}

    // Fallback: push to Python in-memory store
    try {
      final url = Uri.parse('${ApiConstants.chatbotBaseUrl}/vitals/alerts/push');
      await http
          .post(
            url,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'id': '${DateTime.now().millisecondsSinceEpoch}_${alertData['vital']}',
              'type': alertData['type'] ?? 'threshold_breach',
              'severity': alertData['severity'] ?? 'high',
              'message': alertData['message'] ?? '',
              'vital': alertData['vital'] ?? '',
              'current_value': alertData['currentValue'] ?? 0,
              'predicted_value': alertData['predictedValue'] ?? 0,
              'timestamp': DateTime.now().toUtc().toIso8601String() + 'Z',
              'location': alertData['location'] ?? '',
              'latitude': alertData['latitude'] ?? 0,
              'longitude': alertData['longitude'] ?? 0,
              'maps_url': alertData['mapsUrl'] ?? '',
              'emergency_contact_name': alertData['emergencyContactName'] ?? '',
              'emergency_contact_phone': alertData['emergencyContactPhone'] ?? '',
              'patient_id': alertData['patientId'] ?? '',
              'patient_name': alertData['patientName'] ?? '',
              'doctor_id': alertData['doctorId'] ?? '',
              'created_at': DateTime.now().toUtc().toIso8601String() + 'Z',
            }),
          )
          .timeout(const Duration(seconds: 3));
    } catch (_) {
      // Both failed — alert is still shown locally on patient side
    }
  }

  /// Get doctor's vitals alerts — merge from both MongoDB and Python
  static Future<List<Map<String, dynamic>>> getDoctorAlerts({
    required String doctorId,
    String? token,
  }) async {
    final allAlerts = <Map<String, dynamic>>[];

    // Source 1: Node.js MongoDB (persistent)
    try {
      if (token != null) {
        final api = ApiService(token: token);
        final response = await api.get('/vitals/alerts/doctor/$doctorId');
        allAlerts.addAll(List<Map<String, dynamic>>.from(response['alerts'] ?? []));
      }
    } catch (_) {}

    // Source 2: Python in-memory
    try {
      final url = Uri.parse(
        '${ApiConstants.chatbotBaseUrl}${ApiConstants.vitalsDoctorAlerts}/$doctorId',
      );
      final response = await http.get(url).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final pythonAlerts = List<Map<String, dynamic>>.from(data['alerts'] ?? []);
        // Add python alerts that aren't already in MongoDB results
        final existingIds = allAlerts.map((a) => a['id']).toSet();
        for (final a in pythonAlerts) {
          if (!existingIds.contains(a['id'])) {
            a['doctor_notified'] = a['doctor_notified'] ?? true;
            a['emergency_notified'] = a['emergency_notified'] ??
                (a['emergency_contact_phone'] != null && (a['emergency_contact_phone'] as String).isNotEmpty);
            allAlerts.add(a);
          }
        }
      }
    } catch (_) {}

    // Sort newest first
    allAlerts.sort((a, b) {
      final aTime = a['created_at']?.toString() ?? a['createdAt']?.toString() ?? '';
      final bTime = b['created_at']?.toString() ?? b['createdAt']?.toString() ?? '';
      return bTime.compareTo(aTime);
    });

    return allAlerts;
  }

  /// Get patient's vitals alerts — merge from both MongoDB and Python
  static Future<List<Map<String, dynamic>>> getPatientAlerts({
    required String patientId,
    String? token,
  }) async {
    final allAlerts = <Map<String, dynamic>>[];

    // Source 1: Node.js MongoDB
    try {
      if (token != null) {
        final api = ApiService(token: token);
        final response = await api.get('/vitals/alerts/patient/$patientId');
        allAlerts.addAll(List<Map<String, dynamic>>.from(response['alerts'] ?? []));
      }
    } catch (_) {}

    // Source 2: Python in-memory
    try {
      final url = Uri.parse(
        '${ApiConstants.chatbotBaseUrl}${ApiConstants.vitalsPatientAlerts}/$patientId',
      );
      final response = await http.get(url).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final pythonAlerts = List<Map<String, dynamic>>.from(data['alerts'] ?? []);
        final existingIds = allAlerts.map((a) => a['id']).toSet();
        for (final a in pythonAlerts) {
          if (!existingIds.contains(a['id'])) {
            a['doctor_notified'] = a['doctor_notified'] ??
                (a['doctor_id'] != null && (a['doctor_id'] as String).isNotEmpty);
            a['emergency_notified'] = a['emergency_notified'] ??
                (a['emergency_contact_phone'] != null && (a['emergency_contact_phone'] as String).isNotEmpty);
            allAlerts.add(a);
          }
        }
      }
    } catch (_) {}

    allAlerts.sort((a, b) {
      final aTime = a['created_at']?.toString() ?? a['createdAt']?.toString() ?? '';
      final bTime = b['created_at']?.toString() ?? b['createdAt']?.toString() ?? '';
      return bTime.compareTo(aTime);
    });

    return allAlerts;
  }

  static Future<void> markAlertRead({
    required String alertId,
    String? token,
  }) async {
    try {
      if (token != null) {
        final api = ApiService(token: token);
        await api.put('/vitals/alerts/$alertId/read', {});
        return;
      }
    } catch (_) {}

    // Fallback
    final url = Uri.parse(
      '${ApiConstants.chatbotBaseUrl}/vitals/alerts/$alertId/read',
    );
    await http.put(url).timeout(const Duration(seconds: 10));
  }

  static Future<void> deleteAlert({
    required String alertId,
    String? token,
  }) async {
    try {
      if (token != null) {
        final api = ApiService(token: token);
        await api.delete('/vitals/alerts/$alertId');
        return;
      }
    } catch (_) {}

    // Fallback
    final url = Uri.parse(
      '${ApiConstants.chatbotBaseUrl}/vitals/alerts/$alertId',
    );
    await http.delete(url).timeout(const Duration(seconds: 10));
  }
}
