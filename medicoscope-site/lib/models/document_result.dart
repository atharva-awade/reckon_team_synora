class DocumentResult {
  final String? id;
  final String documentType;
  final String fileName;
  final List<LabTest> tests;
  final List<AbnormalValue> abnormalValues;
  final DocumentExplanation explanation;
  final String urgency;
  final DateTime? createdAt;

  DocumentResult({
    this.id,
    this.documentType = 'unknown',
    this.fileName = '',
    this.tests = const [],
    this.abnormalValues = const [],
    required this.explanation,
    this.urgency = 'routine',
    this.createdAt,
  });

  factory DocumentResult.fromJson(Map<String, dynamic> json) {
    final parsedData = json['parsedData'] ?? json['parsed_data'] ?? {};
    return DocumentResult(
      id: json['_id']?.toString(),
      documentType: json['documentType'] ?? json['document_type'] ?? 'unknown',
      fileName: json['fileName'] ?? '',
      tests: (parsedData['tests'] as List?)
              ?.map((t) => LabTest.fromJson(t))
              .toList() ??
          [],
      abnormalValues: (json['abnormalValues'] ?? json['abnormal_values'] as List?)
              ?.map((a) => AbnormalValue.fromJson(a))
              .toList() ??
          [],
      explanation: DocumentExplanation.fromJson(json['explanation'] ?? {}),
      urgency: json['urgency'] ?? 'routine',
      createdAt: json['createdAt'] != null ? DateTime.tryParse(json['createdAt']) : null,
    );
  }

  bool get hasAbnormals => abnormalValues.isNotEmpty;
  bool get isUrgent => urgency == 'urgent';

  int get criticalCount =>
      abnormalValues.where((a) => a.flag.contains('CRITICAL')).length;
}

class LabTest {
  final String name;
  final double? value;
  final String unit;
  final double? refMin;
  final double? refMax;
  final String category;

  LabTest({
    required this.name,
    this.value,
    this.unit = '',
    this.refMin,
    this.refMax,
    this.category = '',
  });

  factory LabTest.fromJson(Map<String, dynamic> json) {
    final ref = json['referenceRange'] ?? json['reference_range'] ?? {};
    return LabTest(
      name: json['name'] ?? '',
      value: (json['value'] as num?)?.toDouble(),
      unit: json['unit'] ?? '',
      refMin: (ref['min'] as num?)?.toDouble(),
      refMax: (ref['max'] as num?)?.toDouble(),
      category: json['category'] ?? '',
    );
  }
}

class AbnormalValue {
  final String name;
  final double value;
  final String unit;
  final String flag;
  final String normalRange;
  final String deviation;

  AbnormalValue({
    required this.name,
    required this.value,
    this.unit = '',
    required this.flag,
    this.normalRange = '',
    this.deviation = '',
  });

  factory AbnormalValue.fromJson(Map<String, dynamic> json) => AbnormalValue(
        name: json['name'] ?? '',
        value: (json['value'] as num?)?.toDouble() ?? 0,
        unit: json['unit'] ?? '',
        flag: json['flag'] ?? 'NORMAL',
        normalRange: json['normalRange'] ?? json['normal_range'] ?? '',
        deviation: json['deviation'] ?? '',
      );

  bool get isCritical => flag.contains('CRITICAL');
  bool get isHigh => flag == 'HIGH' || flag == 'CRITICAL_HIGH';
  bool get isLow => flag == 'LOW' || flag == 'CRITICAL_LOW';
}

class DocumentExplanation {
  final String summary;
  final List<String> keyFindings;
  final String whatThisMeans;
  final List<String> correlations;
  final List<String> recommendedActions;
  final List<String> questionsForDoctor;

  DocumentExplanation({
    this.summary = '',
    this.keyFindings = const [],
    this.whatThisMeans = '',
    this.correlations = const [],
    this.recommendedActions = const [],
    this.questionsForDoctor = const [],
  });

  factory DocumentExplanation.fromJson(Map<String, dynamic> json) =>
      DocumentExplanation(
        summary: json['summary'] ?? '',
        keyFindings: List<String>.from(json['keyFindings'] ?? json['key_findings'] ?? []),
        whatThisMeans: json['whatThisMeans'] ?? json['what_this_means'] ?? '',
        correlations: List<String>.from(json['correlations'] ?? []),
        recommendedActions: List<String>.from(json['recommendedActions'] ?? json['recommended_actions'] ?? []),
        questionsForDoctor: List<String>.from(json['questionsForDoctor'] ?? json['questions_for_doctor'] ?? []),
      );
}
