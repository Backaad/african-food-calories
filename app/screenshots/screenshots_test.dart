// Screenshots for the README, made from the real screens.
//
//   python3 tool/screenshot_photo.py /tmp/shots      # photo + the real model's answer
//   SCREENSHOT_INPUT=/tmp/shots flutter test screenshots --update-goldens
//
// Writes docs/screenshots/*.png. Not part of `flutter test` (it lives outside test/).
// The model cannot run in `flutter test`, so the result screen uses the
// probabilities that tool/screenshot_photo.py got from the real model.

import 'dart:convert';
import 'dart:io';

import 'package:african_food_calories/src/app.dart';
import 'package:african_food_calories/src/journal/journal.dart';
import 'package:african_food_calories/src/nutrition/dish.dart';
import 'package:african_food_calories/src/recognition/classifier.dart';
import 'package:african_food_calories/src/recognition/model_info.dart';
import 'package:african_food_calories/src/services.dart';
import 'package:african_food_calories/src/settings.dart';
import 'package:african_food_calories/src/ui/dish_list_page.dart';
import 'package:african_food_calories/src/ui/portion_page.dart';
import 'package:african_food_calories/src/ui/result_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

const out = '../../docs/screenshots';

class RecordedClassifier extends DishClassifier {
  RecordedClassifier(this.output);

  final List<double> output;

  @override
  final ModelInfo info = ModelInfo.fromJsonString(File('assets/model_info.json').readAsStringSync());

  @override
  Future<List<double>> probabilities(Uint8List photo) async => output;
}

class NoPhotos implements PhotoSource {
  @override
  Future<Uint8List?> pick(PhotoOrigin origin) async => null;
}

Future<void> loadFonts() async {
  final dir =
      Platform.environment['FONTS_DIR'] ?? '${Platform.environment['FLUTTER_ROOT']}/bin/cache/artifacts/material_fonts';
  Future<ByteData> font(String name) async => ByteData.sublistView(File('$dir/$name').readAsBytesSync());
  await (FontLoader('Roboto')
        ..addFont(font('Roboto-Regular.ttf'))
        ..addFont(font('Roboto-Medium.ttf'))
        ..addFont(font('Roboto-Bold.ttf')))
      .load();
  await (FontLoader('MaterialIcons')..addFont(font('MaterialIcons-Regular.otf'))).load();
}

void main() {
  final input = Platform.environment['SCREENSHOT_INPUT'];
  if (input == null) {
    test('screenshots', () {}, skip: 'set SCREENSHOT_INPUT (see the top of this file)');
    return;
  }
  final catalog = DishCatalog.fromJsonString(File('assets/dishes.json').readAsStringSync());
  final prediction = jsonDecode(File('$input/prediction.json').readAsStringSync()) as Map<String, dynamic>;
  final probabilities = List<double>.from((prediction['probabilities'] as List).map((p) => (p as num).toDouble()));
  final photo = File('$input/photo.jpg').readAsBytesSync();

  setUpAll(loadFonts);

  Future<Services> pumpApp(WidgetTester tester, {required String language, ThemeMode theme = ThemeMode.light}) async {
    tester.view.physicalSize = const Size(780, 1688);
    tester.view.devicePixelRatio = 2;
    // Tests draw shadows as black outlines unless told otherwise; [shoot] restores it.
    debugDisableShadows = false;
    addTearDown(tester.view.reset);
    // ignore: invalid_use_of_visible_for_testing_member (a test, outside test/)
    SharedPreferences.setMockInitialValues({});
    final settings = await Settings.load();
    await settings.setLanguageCode(language);
    await settings.setThemeMode(theme);
    final journal = await Journal.load();
    final today = DateTime.now();
    Portion portion(String id, PortionSize size) => catalog[id]!.portions.firstWhere((p) => p.size == size);
    await journal.add(
      'puff_puff',
      portion('puff_puff', PortionSize.small),
      time: DateTime(today.year, today.month, today.day, 8, 15),
    );
    await journal.add(
      'ndole',
      portion('ndole', PortionSize.medium),
      time: DateTime(today.year, today.month, today.day, 13, 0),
    );
    await journal.add(
      'alloco',
      portion('alloco', PortionSize.medium),
      time: DateTime(today.year, today.month, today.day, 19, 30),
    );
    final services = Services(
      catalog: catalog,
      classifier: RecordedClassifier(probabilities),
      journal: journal,
      settings: settings,
      photos: NoPhotos(),
      child: const AfcApp(),
    );
    await tester.pumpWidget(services);
    await tester.pumpAndSettle();
    return services;
  }

  Future<void> push(WidgetTester tester, Widget page) async {
    Navigator.of(tester.element(find.byType(Scaffold).first)).push(MaterialPageRoute<void>(builder: (_) => page));
    await tester.pumpAndSettle();
  }

  Future<void> shoot(String name) async {
    await expectLater(find.byType(AfcApp), matchesGoldenFile('$out/$name.png'));
    debugDisableShadows = true;
  }

  testWidgets('journal (fr)', (tester) async {
    await pumpApp(tester, language: 'fr');
    await shoot('1-journal-fr');
  });

  testWidgets('result (fr)', (tester) async {
    await pumpApp(tester, language: 'fr');
    await tester.runAsync(() => precacheImage(MemoryImage(photo), tester.element(find.byType(Scaffold).first)));
    await push(tester, ResultPage(photo: photo));
    await shoot('2-result-fr');
  });

  testWidgets('portion (fr)', (tester) async {
    await pumpApp(tester, language: 'fr');
    await push(tester, PortionPage(dish: catalog['alloco']!));
    await shoot('3-portion-fr');
  });

  testWidgets('dish list (fr)', (tester) async {
    await pumpApp(tester, language: 'fr');
    await push(tester, const DishListPage());
    await shoot('4-list-fr');
  });

  testWidgets('journal (en, dark)', (tester) async {
    await pumpApp(tester, language: 'en', theme: ThemeMode.dark);
    await shoot('5-journal-en-dark');
  });
}
