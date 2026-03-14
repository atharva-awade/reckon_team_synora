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

  /// Save a vitals alert to MongoDB so doctor can see it
  static Future<void> saveAlert({
    required String token,
    required Map<String, dynamic> alertData,
  }) async {
    try {
      final api = ApiService(token: token);
      await api.post('/vitals/alerts', alertData);
    } catch (_) {
      // Best effort — don't block vitals monitoring
    }
  }

  /// Get doctor's vitals alerts from MongoDB
  static Future<List<Map<String, dynamic>>> getDoctorAlerts({
    required String doctorId,
    String? token,
  }) async {
    try {
      // Try Node.js (persistent MongoDB) first
      if (token != null) {
        final api = ApiService(token: token);
        final response = await api.get('/vitals/alerts/doctor/$doctorId');
        return List<Map<String, dynamic>>.from(response['alerts'] ?? []);
      }
    } catch (_) {}

    // Fallback to Python in-memory
    try {
      final url = Uri.parse(
        '${ApiConstants.chatbotBaseUrl}${ApiConstants.vitalsDoctorAlerts}/$doctorId',
      );
      final response = await http.get(url).timeout(const Duration(seconds: 15));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return List<Map<String, dynamic>>.from(data['alerts'] ?? []);
      }
    } catch (_) {}

    return [];
  }

  /// Get patient's vitals alerts from MongoDB
  static Future<List<Map<String, dynamic>>> getPatientAlerts({
    required String patientId,
    String? token,
  }) async {
    try {
      // Try Node.js (persistent MongoDB) first
      if (token != null) {
        final api = ApiService(token: token);
        final response = await api.get('/vitals/alerts/patient/$patientId');
        return List<Map<String, dynamic>>.from(response['alerts'] ?? []);
      }
    } catch (_) {}

    // Fallback to Python in-memory
    try {
      final url = Uri.parse(
        '${ApiConstants.chatbotBaseUrl}${ApiConstants.vitalsPatientAlerts}/$patientId',
      );
      final response = await http.get(url).timeout(const Duration(seconds: 15));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return List<Map<String, dynamic>>.from(data['alerts'] ?? []);
      }
    } catch (_) {}

    return [];
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
