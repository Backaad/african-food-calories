import 'dart:convert';

/// What the app needs from `training/results/<run>/model_info.json`.
class ModelInfo {
  const ModelInfo({
    required this.labels,
    required this.otherLabel,
    required this.inputSize,
    required this.threshold,
    required this.license,
  });

  factory ModelInfo.fromJsonString(String text) {
    final json = jsonDecode(text) as Map<String, dynamic>;
    final input = json['input'] as Map<String, dynamic>;
    final size = List<int>.from(input['size'] as List);
    final range = List<num>.from(input['range'] as List);
    if (size[0] != size[1] || input['channels'] != 'RGB' || range[0] != 0 || range[1] != 255) {
      throw FormatException('unsupported model input: $input');
    }
    return ModelInfo(
      labels: List<String>.from(json['labels'] as List),
      otherLabel: json['other_label'] as String,
      inputSize: size[0],
      threshold: (json['threshold'] as num).toDouble(),
      license: json['license'] as String,
    );
  }

  /// One label per model output, in order; [otherLabel] means "dish not recognised".
  final List<String> labels;
  final String otherLabel;

  /// The model takes inputSize x inputSize RGB pixels in 0-255.
  final int inputSize;

  /// A dish is shown only if its probability reaches this value (chosen on validation).
  final double threshold;
  final String license;
}
