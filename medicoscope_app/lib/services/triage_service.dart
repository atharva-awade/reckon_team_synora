import '../core/constants/api_constants.dart';
import '../models/triage_result.dart';
import 'api_service.dart';

class TriageService {
  final ApiService _api;

  TriageService(String token) : _api = ApiService(token: token);

  Future<TriageResult?> runTriage({
    required List<String> symptoms,
    String language = 'en',
  }) async {
    try {
      final response = await _api.post(ApiConstants.triage, {
        'symptoms': symptoms,
        'language': language,
      });
      return TriageResult.fromJson(response);
    } catch (e) {
      return null;
    }
  }
}
