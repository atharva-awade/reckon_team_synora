import '../core/constants/api_constants.dart';
import '../models/health_profile.dart';
import 'api_service.dart';

class HealthProfileService {
  final ApiService _api;

  HealthProfileService(String token) : _api = ApiService(token: token);

  Future<HealthProfile?> getProfile() async {
    try {
      final response = await _api.get(ApiConstants.healthProfile);
      if (response['profile'] != null) {
        return HealthProfile.fromJson(response['profile']);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  Future<bool> isProfileComplete() async {
    try {
      final response = await _api.get(ApiConstants.healthProfile);
      return response['isComplete'] == true;
    } catch (e) {
      return false;
    }
  }

  Future<HealthProfile?> saveProfile(HealthProfile profile) async {
    try {
      final response = await _api.post(
        ApiConstants.healthProfile,
        profile.toJson(),
      );
      if (response['profile'] != null) {
        return HealthProfile.fromJson(response['profile']);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  Future<HealthProfile?> getPatientProfile(String patientId) async {
    try {
      final response = await _api.get('${ApiConstants.healthProfile}/$patientId');
      if (response['profile'] != null) {
        return HealthProfile.fromJson(response['profile']);
      }
      return null;
    } catch (e) {
      return null;
    }
  }
}
