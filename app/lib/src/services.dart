import 'dart:typed_data';

import 'package:flutter/widgets.dart';
import 'package:image_picker/image_picker.dart';

import 'journal/journal.dart';
import 'nutrition/dish.dart';
import 'recognition/classifier.dart';
import 'settings.dart';

enum PhotoOrigin { camera, gallery }

/// Where photos come from; replaced by a fake in tests.
abstract class PhotoSource {
  /// The photo's bytes, or null if the user cancelled.
  Future<Uint8List?> pick(PhotoOrigin origin);
}

class ImagePickerPhotoSource implements PhotoSource {
  final _picker = ImagePicker();

  @override
  Future<Uint8List?> pick(PhotoOrigin origin) async {
    final file = await _picker.pickImage(
      source: origin == PhotoOrigin.camera ? ImageSource.camera : ImageSource.gallery,
      // Training images were stored at most 512 px wide or high.
      maxWidth: 512,
      maxHeight: 512,
      imageQuality: 90,
    );
    return file?.readAsBytes();
  }
}

/// Everything the screens need, given once at the top of the app.
class Services extends InheritedWidget {
  const Services({
    super.key,
    required this.catalog,
    required this.classifier,
    required this.journal,
    required this.settings,
    required this.photos,
    required super.child,
  });

  final DishCatalog catalog;

  /// Null if the model could not be loaded on this phone: the list still works.
  final DishClassifier? classifier;
  final Journal journal;
  final Settings settings;
  final PhotoSource photos;

  static Services of(BuildContext context) => context.dependOnInheritedWidgetOfExactType<Services>()!;

  @override
  bool updateShouldNotify(Services oldWidget) =>
      catalog != oldWidget.catalog ||
      classifier != oldWidget.classifier ||
      journal != oldWidget.journal ||
      settings != oldWidget.settings ||
      photos != oldWidget.photos;
}
