class HealthEvent {
  final String? id;
  final String patientId;
  final String eventType;
  final Map<String, dynamic> data;
  final String? linkedDoctor;
  final EventEscalation? escalation;
  final DateTime? createdAt;

  HealthEvent({
    this.id,
    required this.patientId,
    required this.eventType,
    this.data = const {},
    this.linkedDoctor,
    this.escalation,
    this.createdAt,
  });

  factory HealthEvent.fromJson(Map<String, dynamic> json) => HealthEvent(
        id: json['_id']?.toString(),
        patientId: json['patientId']?.toString() ?? '',
        eventType: json['eventType'] ?? '',
        data: Map<String, dynamic>.from(json['data'] ?? {}),
        linkedDoctor: json['linkedDoctor']?.toString(),
        escalation: json['escalation'] != null
            ? EventEscalation.fromJson(json['escalation'])
            : null,
        createdAt: json['createdAt'] != null
            ? DateTime.tryParse(json['createdAt'])
            : null,
      );

  Map<String, dynamic> toJson() => {
        'patientId': patientId,
        'eventType': eventType,
        'data': data,
        if (linkedDoctor != null) 'linkedDoctor': linkedDoctor,
        if (escalation != null) 'escalation': escalation!.toJson(),
      };
}

class EventEscalation {
  final String? type;
  final String? status;
  final int? responseTime;

  EventEscalation({this.type, this.status, this.responseTime});

  factory EventEscalation.fromJson(Map<String, dynamic> json) =>
      EventEscalation(
        type: json['type'],
        status: json['status'],
        responseTime: json['responseTime'],
      );

  Map<String, dynamic> toJson() => {
        if (type != null) 'type': type,
        if (status != null) 'status': status,
        if (responseTime != null) 'responseTime': responseTime,
      };
}
