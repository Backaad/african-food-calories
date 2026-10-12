import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:african_food_calories/src/recognition/preprocess.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;

/// The app must prepare photos exactly as training did. The references were
/// computed with TensorFlow by tool/make_preprocess_fixtures.py.
void main() {
  for (final name in ['downscale', 'upscale']) {
    test('matches TensorFlow on $name.png', () {
      final ref = jsonDecode(File('test/fixtures/$name.json').readAsStringSync()) as Map<String, dynamic>;
      final size = ref['size'] as int;
      final step = ref['step'] as int;
      final out = photoToInput(File('test/fixtures/$name.png').readAsBytesSync(), size);
      expect(out.length, size * size * 3);

      final expected = List<num>.from(ref['values'] as List);
      var worst = 0.0;
      for (var i = 0; i < expected.length; i++) {
        final diff = (out[i * step] - expected[i]).abs();
        if (diff > worst) worst = diff;
      }
      expect(worst, lessThan(0.01), reason: 'largest difference with TensorFlow: $worst');

      final means = List<num>.from(ref['channel_means'] as List);
      for (var c = 0; c < 3; c++) {
        var sum = 0.0;
        for (var i = c; i < out.length; i += 3) {
          sum += out[i];
        }
        expect(sum / (size * size), closeTo(means[c], 0.01));
      }
    });
  }

  test('keeps the RGB order and the 0-255 range', () {
    final image = img.Image(width: 10, height: 6);
    img.fill(image, color: img.ColorRgb8(200, 100, 0));
    final out = photoToInput(Uint8List.fromList(img.encodePng(image)), 4);
    expect(out.sublist(0, 3), [200, 100, 0]);
    expect(out.every((v) => v >= 0 && v <= 255), isTrue);
  });

  test('turns grey images into RGB', () {
    final image = img.Image(width: 5, height: 5, numChannels: 1);
    img.fill(image, color: img.ColorUint8.rgb(80, 80, 80));
    final out = photoToInput(Uint8List.fromList(img.encodePng(image)), 3);
    expect(out.toSet(), {80});
  });

  test('applies the EXIF rotation', () {
    // 4 wide x 2 high, left half red, right half blue, stored rotated 90 degrees.
    final image = img.Image(width: 4, height: 2);
    for (var y = 0; y < 2; y++) {
      for (var x = 0; x < 4; x++) {
        image.setPixelRgb(x, y, x < 2 ? 255 : 0, 0, x < 2 ? 0 : 255);
      }
    }
    image.exif.imageIfd.orientation = 6; // shown rotated 90 degrees clockwise
    final out = photoToInput(Uint8List.fromList(img.encodeJpg(image, quality: 100)), 2);
    // After rotation the red half is on top: first row red, second row blue.
    expect(out[0], greaterThan(out[2]));
    expect(out[2 * 2 * 3 - 1], greaterThan(out[2 * 2 * 3 - 3]));
  });

  test('refuses something that is not an image', () {
    expect(() => photoToInput(Uint8List.fromList([1, 2, 3]), 4), throwsFormatException);
  });
}
