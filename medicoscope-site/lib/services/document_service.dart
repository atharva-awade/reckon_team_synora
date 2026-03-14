import '../core/constants/api_constants.dart';
import '../models/document_result.dart';
import 'api_service.dart';

class DocumentService {
  final ApiService _api;

  DocumentService(String token) : _api = ApiService(token: token);

  /// Upload extracted text from a document for parsing
  Future<DocumentResult?> uploadDocument({
    required String extractedText,
    String? fileName,
    String? documentType,
  }) async {
    try {
      final response = await _api.post('${ApiConstants.documents}/upload', {
        'extractedText': extractedText,
        'fileName': fileName ?? 'document',
        if (documentType != null) 'documentType': documentType,
      });
      if (response['document'] != null) {
        return DocumentResult.fromJson(response['document']);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  /// Get list of patient's documents
  Future<List<DocumentResult>> getDocuments() async {
    try {
      final response = await _api.get(ApiConstants.documents);
      final docs = response['documents'] as List? ?? [];
      return docs.map((d) => DocumentResult.fromJson(d)).toList();
    } catch (e) {
      return [];
    }
  }

  /// Get a specific parsed document
  Future<DocumentResult?> getDocument(String documentId) async {
    try {
      final response = await _api.get('${ApiConstants.documents}/$documentId');
      if (response['document'] != null) {
        return DocumentResult.fromJson(response['document']);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  /// Get patient's documents (doctor view)
  Future<List<DocumentResult>> getPatientDocuments(String patientId) async {
    try {
      final response = await _api.get('${ApiConstants.documents}/patient/$patientId');
      final docs = response['documents'] as List? ?? [];
      return docs.map((d) => DocumentResult.fromJson(d)).toList();
    } catch (e) {
      return [];
    }
  }
}
