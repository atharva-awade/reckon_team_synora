class TriageResult {
  final String recommendedModule;
  final String urgency;
  final String reasoning;
  final List<String> alternativeModules;
  final List<String> followUpQuestions;

  TriageResult({
    required this.recommendedModule,
    this.urgency = 'routine',
    this.reasoning = '',
    this.alternativeModules = const [],
    this.followUpQuestions = const [],
  });

  factory TriageResult.fromJson(Map<String, dynamic> json) => TriageResult(
        recommendedModule: json['recommendedModule'] ?? json['recommended_module'] ?? 'chatbot',
        urgency: json['urgency'] ?? 'routine',
        reasoning: json['reasoning'] ?? '',
        alternativeModules: List<String>.from(json['alternativeModules'] ?? json['alternative_modules'] ?? []),
        followUpQuestions: List<String>.from(json['followUpQuestions'] ?? json['follow_up_questions'] ?? []),
      );

  bool get isEmergency => urgency == 'emergency';
  bool get isUrgent => urgency == 'urgent';

  String get moduleDisplayName {
    switch (recommendedModule) {
      case 'skin':
        return 'Skin Disease Detection';
      case 'chest':
        return 'Chest X-Ray Analysis';
      case 'brain':
        return 'Brain MRI Analysis';
      case 'heart':
        return 'Heart Sound Analysis';
      case 'mental_health':
        return 'MindSpace Mental Health';
      case 'vitals':
        return 'Vitals Monitoring';
      case 'chatbot':
        return 'AI Medical Chat';
      default:
        return recommendedModule;
    }
  }
}
