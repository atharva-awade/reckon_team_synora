import 'package:flutter/foundation.dart';
import '../../models/health_profile.dart';
import '../../services/health_profile_service.dart';

class HealthProfileProvider extends ChangeNotifier {
  HealthProfile? _profile;
  bool _isLoading = false;
  bool _isComplete = false;

  HealthProfile? get profile => _profile;
  bool get isLoading => _isLoading;
  bool get isComplete => _isComplete;
  double get riskScore => _profile?.riskScore ?? 0;

  Future<void> loadProfile(String token) async {
    _isLoading = true;
    notifyListeners();

    try {
      final service = HealthProfileService(token);
      _profile = await service.getProfile();
      _isComplete = _profile?.isComplete ?? false;
    } catch (e) {
      _profile = null;
      _isComplete = false;
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<bool> saveProfile(String token, HealthProfile profile) async {
    _isLoading = true;
    notifyListeners();

    try {
      final service = HealthProfileService(token);
      final saved = await service.saveProfile(profile);
      if (saved != null) {
        _profile = saved;
        _isComplete = true;
        _isLoading = false;
        notifyListeners();
        return true;
      }
    } catch (e) {
      // Failed to save
    }

    _isLoading = false;
    notifyListeners();
    return false;
  }

  void clear() {
    _profile = null;
    _isComplete = false;
    _isLoading = false;
    notifyListeners();
  }
}
