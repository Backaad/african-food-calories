import 'dart:io';

import 'package:african_food_calories/src/nutrition/dish.dart';
import 'package:african_food_calories/src/recognition/model_info.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final catalog = DishCatalog.fromJsonString(File('assets/dishes.json').readAsStringSync());

  test('every dish of dishes.json is readable and consistent', () {
    expect(catalog.dishes.length, 44);
    for (final d in catalog.dishes) {
      expect(d.names.keys, containsAll(['en', 'fr']), reason: d.id);
      expect(d.portions.map((p) => p.size), PortionSize.values, reason: d.id);
      for (final r in [d.per100g.energyKcal, d.per100g.proteinG, d.per100g.fatG, d.per100g.carbohydrateG]) {
        expect(r.low <= r.typical && r.typical <= r.high, isTrue, reason: d.id);
      }
    }
  });

  test('every dish the model can name is in the catalogue', () {
    final info = ModelInfo.fromJsonString(File('assets/model_info.json').readAsStringSync());
    for (final label in info.labels.where((l) => l != info.otherLabel)) {
      expect(catalog[label], isNotNull, reason: label);
    }
  });

  test('a portion scales the values for 100 g', () {
    final ndole = catalog['ndole']!;
    final medium = ndole.portions.firstWhere((p) => p.size == PortionSize.medium);
    final n = ndole.forGrams(medium.grams);
    expect(n.energyKcal.typical, closeTo(ndole.per100g.energyKcal.typical * medium.grams / 100, 1e-9));
    expect(n.energyKcal.low, lessThan(n.energyKcal.high));
  });

  test('search ignores accents and case, and sorts by name', () {
    expect(catalog.search('ndole', 'fr').map((d) => d.id), contains('ndole'));
    expect(catalog.search('NDOLÉ', 'en').map((d) => d.id), contains('ndole'));
    expect(catalog.search('xyz', 'fr'), isEmpty);
    final all = catalog.search('', 'fr');
    expect(all.length, 44);
    final names = all.map((d) => foldText(d.name('fr'))).toList();
    expect(names, [...names]..sort());
  });

  test('ranges add up', () {
    const a = Range(1, 2, 3), b = Range(10, 20, 30);
    final s = a + b;
    expect([s.low, s.typical, s.high], [11, 22, 33]);
  });
}
