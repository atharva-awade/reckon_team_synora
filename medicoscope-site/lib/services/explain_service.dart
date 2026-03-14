import '../core/constants/api_constants.dart';
import '../models/explainable_result.dart';
import 'api_service.dart';

class ExplainService {
  final ApiService _api;

  ExplainService(String token) : _api = ApiService(token: token);

  /// Generate explainable AI result for a detection
  Future<ExplainableResult?> generateExplanation({
    required String className,
    required double confidence,
    required String category,
    String? detectionId,
    Map<String, dynamic>? vitalsBaseline,
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
        if (vitalsBaseline != null) 'vitalsBaseline': vitalsBaseline,
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

  /// Get cached explanation for a detection
  Future<ExplainableResult?> getExplanation(String detectionId) async {
    try {
      final response = await _api.get('${ApiConstants.explain}/$detectionId');
      if (response['explanation'] != null) {
        return ExplainableResult.fromJson(response['explanation']);
      }
      return null;
    } catch (e) {
      return null;
    }
  }
}
