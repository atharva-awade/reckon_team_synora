import '../core/constants/api_constants.dart';
import '../models/escalation.dart';
import 'api_service.dart';

class EscalationService {
  final ApiService _api;

  EscalationService(String token) : _api = ApiService(token: token);

  Future<Escalation?> createEscalation({
    required String patientId,
    required String doctorId,
    required String sourceType,
    required String escalationType,
    required Map<String, dynamic> summary,
    String? detectionId,
  }) async {
    try {
      final response = await _api.post(ApiConstants.escalations, {
        'patientId': patientId,
        'doctorId': doctorId,
        'sourceType': sourceType,
        'escalationType': escalationType,
        'summary': summary,
        if (detectionId != null) 'detectionId': detectionId,
      });
      if (response['escalation'] != null) {
        return Escalation.fromJson(response['escalation']);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  Future<List<Escalation>> getDoctorEscalations(String doctorId, {String? status}) async {
    try {
      String endpoint = '${ApiConstants.escalations}/doctor/$doctorId';
      if (status != null) endpoint += '?status=$status';

      final response = await _api.get(endpoint);
      final list = response['escalations'] as List? ?? [];
      return list.map((e) => Escalation.fromJson(e)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<List<Escalation>> getPatientEscalations(String patientId) async {
    try {
      final response = await _api.get('${ApiConstants.escalations}/patient/$patientId');
      final list = response['escalations'] as List? ?? [];
      return list.map((e) => Escalation.fromJson(e)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<bool> acknowledgeEscalation(String escalationId) async {
    try {
      await _api.put('${ApiConstants.escalations}/$escalationId/acknowledge', {});
      return true;
    } catch (e) {
      return false;
    }
  }

  Future<bool> resolveEscalation(String escalationId, {String? doctorNotes}) async {
    try {
      await _api.put('${ApiConstants.escalations}/$escalationId/resolve', {
        if (doctorNotes != null) 'doctorNotes': doctorNotes,
      });
      return true;
    } catch (e) {
      return false;
    }
  }

  /// Determine escalation type based on detection result
  static String getEscalationType({
    required String className,
    required double confidence,
    required String category,
  }) {
    // Immediate escalation rules
    if (category == 'brain') return 'immediate'; // Brain tumor at any confidence
    if (className == 'Melanoma' && confidence > 0.3) return 'immediate';
    if (className == 'Basal Cell Carcinoma' && confidence > 0.3) return 'immediate';
    if (className == 'Pneumothorax' && confidence > 0.4) return 'immediate';
    if (className == 'Mass' && confidence > 0.3) return 'immediate';

    // Priority escalation rules
    if (category == 'chest' && confidence > 0.5) return 'priority';
    if (className == 'Cardiomegaly' && confidence > 0.4) return 'priority';
    if (className == 'Actinic Keratoses' && confidence > 0.5) return 'priority';

    // Routine for everything else
    return 'routine';
  }
}
