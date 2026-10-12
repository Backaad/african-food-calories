import 'dart:io';
import 'dart:typed_data';

import 'package:african_food_calories/src/app.dart';
import 'package:african_food_calories/src/journal/journal.dart';
import 'package:african_food_calories/src/nutrition/dish.dart';
import 'package:african_food_calories/src/recognition/classifier.dart';
import 'package:african_food_calories/src/recognition/model_info.dart';
import 'package:african_food_calories/src/services.dart';
import 'package:african_food_calories/src/settings.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;
import 'package:shared_preferences/shared_preferences.dart';

/// Answers fixed probabilities instead of running the model.
class FakeClassifier extends DishClassifier {
  FakeClassifier(this.output);

  List<double> output;

  @override
  final ModelInfo info = ModelInfo.fromJsonString(File('assets/model_info.json').readAsStringSync());

  @override
  Future<List<double>> probabilities(Uint8List photo) async => output;
}

class FakePhotos implements PhotoSource {
  final photo = Uint8List.fromList(img.encodePng(img.Image(width: 8, height: 6)));
  final asked = <PhotoOrigin>[];

  @override
  Future<Uint8List?> pick(PhotoOrigin origin) async {
    asked.add(origin);
    return photo;
  }
}

final catalog = DishCatalog.fromJsonString(File('assets/dishes.json').readAsStringSync());

// Labels: alloco, bobolo, fufu, puff_puff, ugali, other.
const sureBobolo = [0.02, 0.90, 0.05, 0.01, 0.01, 0.01];
const unsure = [0.10, 0.05, 0.20, 0.05, 0.10, 0.50];

Future<Services> pumpApp(WidgetTester tester, {DishClassifier? classifier, String language = 'fr'}) async {
  final settings = await Settings.load();
  await settings.setLanguageCode(language);
  final services = Services(
    catalog: catalog,
    classifier: classifier,
    journal: await Journal.load(),
    settings: settings,
    photos: FakePhotos(),
    child: const AfcApp(),
  );
  await tester.pumpWidget(services);
  await tester.pumpAndSettle();
  return services;
}

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  testWidgets('starts with an empty journal, in French', (tester) async {
    await pumpApp(tester, classifier: FakeClassifier(sureBobolo));
    expect(find.text('Calories des plats africains'), findsOneWidget);
    expect(find.text('Total du jour'), findsOneWidget);
    expect(find.text('0 kcal'), findsOneWidget);
    expect(find.textContaining('Rien de noté aujourd'), findsOneWidget);
  });

  testWidgets('photo, recognised dish, portion, journal', (tester) async {
    final services = await pumpApp(tester, classifier: FakeClassifier(sureBobolo));
    await tester.tap(find.byKey(const Key('add-dish')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Prendre une photo'));
    await tester.pumpAndSettle();
    expect((services.photos as FakePhotos).asked, [PhotoOrigin.camera]);

    // Most likely dish, then two alternatives.
    final bobolo = catalog['bobolo']!;
    expect(find.text('Le plus probable'), findsOneWidget);
    expect(
      find.descendant(of: find.byKey(const Key('top-dish')), matching: find.text(bobolo.name('fr'))),
      findsOneWidget,
    );
    expect(find.text(catalog['fufu']!.name('fr')), findsOneWidget);
    expect(find.text(catalog['alloco']!.name('fr')), findsOneWidget);

    await tester.tap(find.byKey(const Key('top-dish')));
    await tester.pumpAndSettle();
    final large = bobolo.portions.firstWhere((p) => p.size == PortionSize.large);
    await tester.tap(find.textContaining('Grande'));
    await tester.pumpAndSettle();
    final kcal = bobolo.forGrams(large.grams).energyKcal.typical.round();
    expect(tester.widget<Text>(find.byKey(const Key('energy'))).data, '$kcal kcal');
    // Below the fold on a small screen, but on the page.
    expect(find.textContaining('nutritionniste', skipOffstage: false), findsWidgets);

    await tester.tap(find.byKey(const Key('add-to-journal')));
    await tester.pumpAndSettle();
    expect(find.text('Ajouté au journal'), findsOneWidget);
    final entries = services.journal.entriesOn(DateTime.now());
    expect(entries.single.dishId, 'bobolo');
    expect(entries.single.grams, large.grams);
    expect(find.text(bobolo.name('fr')), findsOneWidget); // the journal line
  });

  testWidgets('dish not recognised, then chosen from the list', (tester) async {
    final services = await pumpApp(tester, classifier: FakeClassifier(unsure));
    await tester.tap(find.byKey(const Key('add-dish')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Choisir une photo'));
    await tester.pumpAndSettle();
    expect(find.text('Plat non reconnu'), findsOneWidget);
    expect(find.text('Propositions peu sûres'), findsOneWidget);
    expect(find.byKey(const Key('top-dish')), findsNothing);

    await tester.tap(find.byKey(const Key('choose-from-list')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('search')), 'ndole');
    await tester.pumpAndSettle();
    await tester.tap(find.text('Ndolé'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('add-to-journal')));
    await tester.pumpAndSettle();
    expect(services.journal.entriesOn(DateTime.now()).single.dishId, 'ndole');
    expect(find.text('Ndolé'), findsOneWidget);
  });

  testWidgets('a journal line can be deleted and put back', (tester) async {
    final services = await pumpApp(tester, classifier: FakeClassifier(sureBobolo));
    await services.journal.add('ndole', catalog['ndole']!.portions.first);
    await tester.pumpAndSettle();
    await tester.drag(find.text('Ndolé'), const Offset(-600, 0));
    await tester.pumpAndSettle();
    expect(services.journal.entriesOn(DateTime.now()), isEmpty);
    await tester.tap(find.text('Annuler'));
    await tester.pumpAndSettle();
    expect(services.journal.entriesOn(DateTime.now()), hasLength(1));
  });

  testWidgets('without a model, dishes can still be chosen from the list', (tester) async {
    await pumpApp(tester);
    await tester.tap(find.byKey(const Key('add-dish')));
    await tester.pumpAndSettle();
    expect(find.text('Prendre une photo'), findsNothing);
    expect(find.textContaining('reconnaissance par photo'), findsOneWidget);
    await tester.tap(find.text('Choisir dans la liste'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('search')), findsOneWidget);
  });

  testWidgets('language and theme can be changed', (tester) async {
    final services = await pumpApp(tester, classifier: FakeClassifier(sureBobolo));
    await tester.tap(find.byTooltip('Réglages'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('English'));
    await tester.pumpAndSettle();
    expect(find.text('Settings'), findsOneWidget);
    await tester.scrollUntilVisible(find.text('Dark'), 100);
    await tester.tap(find.text('Dark'));
    await tester.pumpAndSettle();
    expect(services.settings.themeMode, ThemeMode.dark);
    expect(Theme.of(tester.element(find.text('Settings'))).brightness, Brightness.dark);
    // The FAO source must be acknowledged (WAFCT terms of use).
    expect(find.textContaining('FAO'), findsWidgets);

    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(find.text('Total today'), findsOneWidget);
    // Kept for the next launch.
    final reloaded = await Settings.load();
    expect([reloaded.languageCode, reloaded.themeMode], ['en', ThemeMode.dark]);
  });
}
