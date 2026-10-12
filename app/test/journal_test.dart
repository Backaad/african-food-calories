import 'package:african_food_calories/src/journal/journal.dart';
import 'package:african_food_calories/src/nutrition/dish.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  final catalog = DishCatalog(
    dishes: [
      const Dish(
        id: 'fufu',
        names: {'en': 'Fufu', 'fr': 'Foufou'},
        countries: ['GH'],
        per100g: Nutrients(
          energyKcal: Range(100, 120, 140),
          proteinG: Range(1, 1, 1),
          fatG: Range(0, 0.5, 1),
          carbohydrateG: Range(25, 28, 30),
          fibreG: Range(1, 1, 1),
        ),
        portions: [Portion(PortionSize.small, 200), Portion(PortionSize.medium, 300), Portion(PortionSize.large, 400)],
        recipeSources: [],
        validatedByNutritionist: false,
      ),
    ],
    disclaimer: const {'en': 'x', 'fr': 'x'},
    source: 's',
    sourceTerms: 't',
  );

  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('entries are kept on the phone and totalled per day', () async {
    final journal = await Journal.load();
    final today = DateTime(2026, 10, 12, 12);
    await journal.add('fufu', const Portion(PortionSize.small, 200), time: today);
    await journal.add('fufu', const Portion(PortionSize.medium, 300), time: today.add(const Duration(hours: 6)));
    await journal.add('fufu', const Portion(PortionSize.large, 400), time: today.subtract(const Duration(days: 1)));

    final reloaded = await Journal.load();
    final entries = reloaded.entriesOn(today);
    expect(entries.map((e) => e.grams), [200, 300]);
    final total = totalOf(entries, catalog);
    expect([total.energyKcal.low, total.energyKcal.typical, total.energyKcal.high], [500, 600, 700]);
  });

  test('remove and undo', () async {
    final journal = await Journal.load();
    final entry = await journal.add('fufu', const Portion(PortionSize.small, 200));
    await journal.remove(entry.id);
    expect(journal.entriesOn(DateTime.now()), isEmpty);
    await journal.restore(entry);
    expect((await Journal.load()).entriesOn(DateTime.now()).single.id, entry.id);
  });

  test('a damaged journal does not stop the app', () async {
    SharedPreferences.setMockInitialValues({'journal.v1': 'not json'});
    final journal = await Journal.load();
    expect(journal.entriesOn(DateTime.now()), isEmpty);
  });

  test('entries of unknown dishes are left out of the total', () async {
    final journal = await Journal.load();
    await journal.add('removed_dish', const Portion(PortionSize.small, 200));
    expect(totalOf(journal.entriesOn(DateTime.now()), catalog).energyKcal.typical, 0);
  });
}
