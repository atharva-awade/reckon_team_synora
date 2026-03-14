class HealthProfile {
  final String? id;
  final String userId;
  final Demographics demographics;
  final MedicalHistory medicalHistory;
  final Lifestyle lifestyle;
  final List<Medication> currentMedications;
  final List<String> primarySymptoms;
  final double riskScore;
  final bool isComplete;

  HealthProfile({
    this.id,
    required this.userId,
    required this.demographics,
    required this.medicalHistory,
    required this.lifestyle,
    this.currentMedications = const [],
    this.primarySymptoms = const [],
    this.riskScore = 0,
    this.isComplete = false,
  });

  factory HealthProfile.fromJson(Map<String, dynamic> json) {
    return HealthProfile(
      id: json['_id']?.toString(),
      userId: json['userId']?.toString() ?? '',
      demographics: Demographics.fromJson(json['demographics'] ?? {}),
      medicalHistory: MedicalHistory.fromJson(json['medicalHistory'] ?? {}),
      lifestyle: Lifestyle.fromJson(json['lifestyle'] ?? {}),
      currentMedications: (json['currentMedications'] as List?)
              ?.map((m) => Medication.fromJson(m))
              .toList() ??
          [],
      primarySymptoms:
          List<String>.from(json['primarySymptoms'] ?? []),
      riskScore: (json['riskScore'] as num?)?.toDouble() ?? 0,
      isComplete: json['isComplete'] ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
        'demographics': demographics.toJson(),
        'medicalHistory': medicalHistory.toJson(),
        'lifestyle': lifestyle.toJson(),
        'currentMedications': currentMedications.map((m) => m.toJson()).toList(),
        'primarySymptoms': primarySymptoms,
      };
}

class Demographics {
  final int age;
  final String sex;
  final double heightCm;
  final double weightKg;
  final double bmi;

  Demographics({
    this.age = 0,
    this.sex = 'other',
    this.heightCm = 0,
    this.weightKg = 0,
    this.bmi = 0,
  });

  factory Demographics.fromJson(Map<String, dynamic> json) => Demographics(
        age: json['age'] ?? 0,
        sex: json['sex'] ?? 'other',
        heightCm: (json['height_cm'] as num?)?.toDouble() ?? 0,
        weightKg: (json['weight_kg'] as num?)?.toDouble() ?? 0,
        bmi: (json['bmi'] as num?)?.toDouble() ?? 0,
      );

  Map<String, dynamic> toJson() => {
        'age': age,
        'sex': sex,
        'height_cm': heightCm,
        'weight_kg': weightKg,
      };
}

class MedicalHistory {
  final List<String> chronicConditions;
  final List<Surgery> surgeries;
  final List<FamilyCondition> familyHistory;
  final List<String> allergies;

  MedicalHistory({
    this.chronicConditions = const [],
    this.surgeries = const [],
    this.familyHistory = const [],
    this.allergies = const [],
  });

  factory MedicalHistory.fromJson(Map<String, dynamic> json) => MedicalHistory(
        chronicConditions:
            List<String>.from(json['chronicConditions'] ?? []),
        surgeries: (json['surgeries'] as List?)
                ?.map((s) => Surgery.fromJson(s))
                .toList() ??
            [],
        familyHistory: (json['familyHistory'] as List?)
                ?.map((f) => FamilyCondition.fromJson(f))
                .toList() ??
            [],
        allergies: List<String>.from(json['allergies'] ?? []),
      );

  Map<String, dynamic> toJson() => {
        'chronicConditions': chronicConditions,
        'surgeries': surgeries.map((s) => s.toJson()).toList(),
        'familyHistory': familyHistory.map((f) => f.toJson()).toList(),
        'allergies': allergies,
      };
}

class Surgery {
  final String name;
  final int year;

  Surgery({required this.name, required this.year});

  factory Surgery.fromJson(Map<String, dynamic> json) => Surgery(
        name: json['name'] ?? '',
        year: json['year'] ?? 0,
      );

  Map<String, dynamic> toJson() => {'name': name, 'year': year};
}

class FamilyCondition {
  final String condition;
  final String relation;

  FamilyCondition({required this.condition, required this.relation});

  factory FamilyCondition.fromJson(Map<String, dynamic> json) =>
      FamilyCondition(
        condition: json['condition'] ?? '',
        relation: json['relation'] ?? '',
      );

  Map<String, dynamic> toJson() => {'condition': condition, 'relation': relation};
}

class Lifestyle {
  final String smokingStatus;
  final String alcoholConsumption;
  final String exerciseFrequency;
  final String dietType;

  Lifestyle({
    this.smokingStatus = 'never',
    this.alcoholConsumption = 'none',
    this.exerciseFrequency = 'none',
    this.dietType = 'regular',
  });

  factory Lifestyle.fromJson(Map<String, dynamic> json) => Lifestyle(
        smokingStatus: json['smokingStatus'] ?? 'never',
        alcoholConsumption: json['alcoholConsumption'] ?? 'none',
        exerciseFrequency: json['exerciseFrequency'] ?? 'none',
        dietType: json['dietType'] ?? 'regular',
      );

  Map<String, dynamic> toJson() => {
        'smokingStatus': smokingStatus,
        'alcoholConsumption': alcoholConsumption,
        'exerciseFrequency': exerciseFrequency,
        'dietType': dietType,
      };
}

class Medication {
  final String name;
  final String dosage;
  final String frequency;
  final String startDate;

  Medication({
    required this.name,
    this.dosage = '',
    this.frequency = '',
    this.startDate = '',
  });

  factory Medication.fromJson(Map<String, dynamic> json) => Medication(
        name: json['name'] ?? '',
        dosage: json['dosage'] ?? '',
        frequency: json['frequency'] ?? '',
        startDate: json['startDate'] ?? '',
      );

  Map<String, dynamic> toJson() => {
        'name': name,
        'dosage': dosage,
        'frequency': frequency,
        'startDate': startDate,
      };
}
