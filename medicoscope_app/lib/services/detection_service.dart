import '../core/constants/api_constants.dart';
import '../models/detection_record.dart';
import '../models/explainable_result.dart';
import '../models/escalation.dart';
import 'api_service.dart';
import 'escalation_service.dart';

class DetectionService {
  final ApiService _api;
  final String _token;

  DetectionService(String token) : _api = ApiService(token: token), _token = token;

  Future<DetectionRecord?> saveRecord({
    required String className,
    required double confidence,
    required String category,
    String? description,
    String? patientId,
  }) async {
    try {
      final response = await _api.post(ApiConstants.detections, {
        'className': className,
        'confidence': confidence,
        'category': category,
        'description': description ?? '',
        if (patientId != null) 'patientId': patientId,
      });
      return DetectionRecord.fromJson(response['record']);
    } catch (e) {
      // Silently fail - detection saving should not block the results screen
      return null;
    }
  }

  /// Save detection and trigger escalation + explanation in background
  Future<DetectionRecord?> saveRecordWithEscalation({
    required String className,
    required double confidence,
    required String category,
    String? description,
    String? patientId,
    String? doctorId,
  }) async {
    final record = await saveRecord(
      className: className,
      confidence: confidence,
      category: category,
      description: description,
      patientId: patientId,
    );

    // Trigger escalation if doctor is linked and condition warrants it
    if (record != null && doctorId != null) {
      try {
        final escalationType = EscalationService.getEscalationType(
          className: className,
          confidence: confidence,
          category: category,
        );

        final escalationService = EscalationService(_token);
        await escalationService.createEscalation(
          patientId: patientId ?? '',
          doctorId: doctorId,
          sourceType: 'detection',
          escalationType: escalationType,
          detectionId: record.id,
          summary: {
            'condition': className,
            'confidence': confidence,
            'message': '$className detected with ${(confidence * 100).toStringAsFixed(1)}% confidence ($category scan)',
          },
        );
      } catch (_) {
        // Don't block on escalation failure
      }
    }

    return record;
  }

  /// Fetch explainable AI result for a detection
  Future<ExplainableResult?> getExplanation({
    required String className,
    required double confidence,
    required String category,
    String? detectionId,
    String language = 'en',
  }) async {
    try {
      final response = await _api.post(ApiConstants.explain, {
        'detection': {
          'class_name': className,
          'confidence': confidence,
          'category': category,
        },
        if (detectionId != null) 'detectionId': detectionId,
        'language': language,
      });
      if (response['explanation'] != null) {
        return ExplainableResult.fromJson(response['explanation']);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  Future<List<DetectionRecord>> getMyRecords() async {
    try {
      final response = await _api.get(ApiConstants.patientRecords);
      final records = response['records'] as List;
      return records.map((r) => DetectionRecord.fromJson(r)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<List<DetectionRecord>> getPatientRecords(String patientId) async {
    try {
      final response = await _api.get('${ApiConstants.detections}/$patientId');
      final records = response['records'] as List;
      return records.map((r) => DetectionRecord.fromJson(r)).toList();
    } catch (e) {
      return [];
    }
  }
}
