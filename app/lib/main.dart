import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'src/app.dart';
import 'src/journal/journal.dart';
import 'src/nutrition/dish.dart';
import 'src/recognition/classifier.dart';
import 'src/services.dart';
import 'src/settings.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final catalog = DishCatalog.fromJsonString(await rootBundle.loadString('assets/dishes.json'));
  DishClassifier? classifier;
  try {
    classifier = await TfliteDishClassifier.load();
  } on Object catch (error) {
    // The dish list and the journal work without the model.
    debugPrint('model not loaded: $error');
  }
  runApp(
    Services(
      catalog: catalog,
      classifier: classifier,
      journal: await Journal.load(),
      settings: await Settings.load(),
      photos: ImagePickerPhotoSource(),
      child: const AfcApp(),
    ),
  );
}
