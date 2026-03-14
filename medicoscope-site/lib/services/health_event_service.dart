import '../core/constants/api_constants.dart';
import '../models/health_event.dart';
import 'api_service.dart';

class HealthEventService {
  final ApiService _api;

  HealthEventService(String token) : _api = ApiService(token: token);

  Future<HealthEvent?> recordEvent({
    required String eventType,
    required Map<String, dynamic> data,
    String? patientId,
    String? linkedDoctor,
  }) async {
    try {
      final response = await _api.post(ApiConstants.healthEvents, {
        'eventType': eventType,
        'data': data,
        if (patientId != null) 'patientId': patientId,
        if (linkedDoctor != null) 'linkedDoctor': linkedDoctor,
      });
      if (response['event'] != null) {
        return HealthEvent.fromJson(response['event']);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  Future<List<HealthEvent>> getTimeline({String? eventType, int limit = 50}) async {
    try {
      String endpoint = ApiConstants.healthEvents;
      final params = <String>[];
      if (eventType != null) params.add('eventType=$eventType');
      if (limit != 50) params.add('limit=$limit');
      if (params.isNotEmpty) endpoint += '?${params.join('&')}';

      final response = await _api.get(endpoint);
      final events = response['events'] as List? ?? [];
      return events.map((e) => HealthEvent.fromJson(e)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<List<HealthEvent>> getPatientTimeline(String patientId, {String? eventType}) async {
    try {
      String endpoint = '${ApiConstants.healthEvents}/patient/$patientId';
      if (eventType != null) endpoint += '?eventType=$eventType';

      final response = await _api.get(endpoint);
      final events = response['events'] as List? ?? [];
      return events.map((e) => HealthEvent.fromJson(e)).toList();
    } catch (e) {
      return [];
    }
  }
}
