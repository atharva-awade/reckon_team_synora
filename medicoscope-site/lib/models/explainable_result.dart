class ExplainableResult {
  final String? id;
  final String conditionName;
  final String laymanName;
  final String category;
  final String whatItIs;
  final String whyItOccurs;
  final String howItAffectsBody;
  final AiConfidence aiConfidence;
  final List<String> associatedSymptoms;
  final List<String> immediatePrecautions;
  final List<String> lifestyleImprovements;
  final ConsultGuidance whenToConsult;
  final String personalizedRiskContext;
  final String disclaimer;

  ExplainableResult({
    this.id,
    required this.conditionName,
    this.laymanName = '',
    this.category = '',
    this.whatItIs = '',
    this.whyItOccurs = '',
    this.howItAffectsBody = '',
    required this.aiConfidence,
    this.associatedSymptoms = const [],
    this.immediatePrecautions = const [],
    this.lifestyleImprovements = const [],
    required this.whenToConsult,
    this.personalizedRiskContext = '',
    this.disclaimer = 'This AI analysis is for screening purposes only.',
  });

  factory ExplainableResult.fromJson(Map<String, dynamic> json) {
    final condition = json['condition'] as Map<String, dynamic>? ?? {};
    return ExplainableResult(
      id: json['_id']?.toString(),
      conditionName: condition['name'] ?? json['conditionName'] ?? '',
      laymanName: condition['layman_name'] ?? condition['laymanName'] ?? json['laymanName'] ?? '',
      category: condition['category'] ?? json['category'] ?? '',
      whatItIs: json['what_it_is'] ?? json['whatItIs'] ?? '',
      whyItOccurs: json['why_it_occurs'] ?? json['whyItOccurs'] ?? '',
      howItAffectsBody: json['how_it_affects_body'] ?? json['howItAffectsBody'] ?? '',
      aiConfidence: AiConfidence.fromJson(json['ai_confidence'] ?? json['aiConfidence'] ?? {}),
      associatedSymptoms: List<String>.from(json['associated_symptoms'] ?? json['associatedSymptoms'] ?? []),
      immediatePrecautions: List<String>.from(json['immediate_precautions'] ?? json['immediatePrecautions'] ?? []),
      lifestyleImprovements: List<String>.from(json['lifestyle_improvements'] ?? json['lifestyleImprovements'] ?? []),
      whenToConsult: ConsultGuidance.fromJson(json['when_to_consult'] ?? json['whenToConsult'] ?? {}),
      personalizedRiskContext: json['personalized_risk_context'] ?? json['personalizedRiskContext'] ?? '',
      disclaimer: json['disclaimer'] ?? 'This AI analysis is for screening purposes only.',
    );
  }

  Map<String, dynamic> toJson() => {
        'condition': {'name': conditionName, 'layman_name': laymanName, 'category': category},
        'what_it_is': whatItIs,
        'why_it_occurs': whyItOccurs,
        'how_it_affects_body': howItAffectsBody,
        'ai_confidence': aiConfidence.toJson(),
        'associated_symptoms': associatedSymptoms,
        'immediate_precautions': immediatePrecautions,
        'lifestyle_improvements': lifestyleImprovements,
        'when_to_consult': whenToConsult.toJson(),
        'personalized_risk_context': personalizedRiskContext,
        'disclaimer': disclaimer,
      };
}

class AiConfidence {
  final double score;
  final String interpretation;
  final String explanation;
  final List<String> factorsAffectingConfidence;

  AiConfidence({
    this.score = 0,
    this.interpretation = '',
    this.explanation = '',
    this.factorsAffectingConfidence = const [],
  });

  factory AiConfidence.fromJson(Map<String, dynamic> json) => AiConfidence(
        score: (json['score'] as num?)?.toDouble() ?? 0,
        interpretation: json['interpretation'] ?? '',
        explanation: json['explanation'] ?? '',
        factorsAffectingConfidence: List<String>.from(
            json['factors_affecting_confidence'] ?? json['factorsAffectingConfidence'] ?? []),
      );

  Map<String, dynamic> toJson() => {
        'score': score,
        'interpretation': interpretation,
        'explanation': explanation,
        'factors_affecting_confidence': factorsAffectingConfidence,
      };
}

class ConsultGuidance {
  final String urgency;
  final String specialist;
  final String reason;
  final String whatDoctorWillDo;

  ConsultGuidance({
    this.urgency = 'routine',
    this.specialist = '',
    this.reason = '',
    this.whatDoctorWillDo = '',
  });

  factory ConsultGuidance.fromJson(Map<String, dynamic> json) =>
      ConsultGuidance(
        urgency: json['urgency'] ?? 'routine',
        specialist: json['specialist'] ?? '',
        reason: json['reason'] ?? '',
        whatDoctorWillDo: json['what_doctor_will_do'] ?? json['whatDoctorWillDo'] ?? '',
      );

  Map<String, dynamic> toJson() => {
        'urgency': urgency,
        'specialist': specialist,
        'reason': reason,
        'what_doctor_will_do': whatDoctorWillDo,
      };
}
