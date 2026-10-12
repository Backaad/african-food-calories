import 'dart:io';

import 'package:african_food_calories/src/recognition/decision.dart';
import 'package:african_food_calories/src/recognition/model_info.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  const info = ModelInfo(
    labels: ['alloco', 'bobolo', 'fufu', 'puff_puff', 'ugali', 'other'],
    otherLabel: 'other',
    inputSize: 224,
    threshold: 0.65,
    license: 'CC BY-NC 4.0',
  );

  test('shows the top dish when it reaches the threshold, with two alternatives', () {
    final r = decide([0.05, 0.70, 0.10, 0.02, 0.03, 0.10], info);
    expect(r.recognised, isTrue);
    expect(r.suggestions.map((s) => s.dishId), ['bobolo', 'fufu', 'alloco']);
  });

  test('a probability exactly at the threshold is accepted', () {
    expect(decide([0.65, 0.1, 0.1, 0.05, 0.05, 0.05], info).recognised, isTrue);
  });

  test('refuses below the threshold', () {
    final r = decide([0.40, 0.30, 0.10, 0.05, 0.05, 0.10], info);
    expect(r.recognised, isFalse);
    expect(r.suggestions.first.dishId, 'alloco');
  });

  test('refuses when "other" comes first, and never suggests "other"', () {
    final r = decide([0.01, 0.01, 0.01, 0.01, 0.01, 0.95], info);
    expect(r.recognised, isFalse);
    expect(r.suggestions, hasLength(3));
    expect(r.suggestions.map((s) => s.dishId), isNot(contains('other')));
  });

  test('rejects a wrong number of probabilities', () {
    expect(() => decide([0.5, 0.5], info), throwsArgumentError);
  });

  test('reads the model_info.json shipped with the app', () {
    final real = ModelInfo.fromJsonString(File('assets/model_info.json').readAsStringSync());
    expect(real.labels.last, real.otherLabel);
    expect(real.inputSize, 224);
    expect(real.threshold, inInclusiveRange(0, 1));
  });
}
