import 'dart:math' as math;
import 'dart:typed_data';

import 'package:image/image.dart' as img;

/// Decodes a photo and turns it into the model input: the whole image resized
/// to [size] x [size], RGB, float 0-255, row by row (height, width, channel).
///
/// It must match training (`load_image` in training/afctrain/model.py):
/// `tf.image.resize` bilinear with half-pixel centres and no antialiasing,
/// without cropping. test/preprocess_test.dart checks it against TensorFlow.
Float32List photoToInput(Uint8List bytes, int size) {
  final decoded = img.decodeImage(bytes);
  if (decoded == null) {
    throw const FormatException('not an image');
  }
  // Apply the EXIF rotation, as the photo appears in the gallery.
  final image = img.bakeOrientation(decoded);
  return resizeBilinear(image, size, size);
}

/// 8-bit RGB copy of any decoded image (grey, palette, 16-bit, with alpha).
img.Image toRgb8(img.Image image) {
  if (image.format == img.Format.uint8 && image.numChannels == 3 && !image.hasPalette) {
    return image;
  }
  return image.convert(format: img.Format.uint8, numChannels: 3);
}

Float32List resizeBilinear(img.Image source, int outHeight, int outWidth) {
  final image = toRgb8(source);
  final h = image.height, w = image.width;
  final rgb = Float32List(h * w * 3);
  var k = 0;
  for (var y = 0; y < h; y++) {
    for (var x = 0; x < w; x++) {
      final p = image.getPixel(x, y);
      rgb[k++] = p.r.toDouble();
      rgb[k++] = p.g.toDouble();
      rgb[k++] = p.b.toDouble();
    }
  }

  final ys = _Axis(h, outHeight), xs = _Axis(w, outWidth);
  final out = Float32List(outHeight * outWidth * 3);
  var o = 0;
  for (var oy = 0; oy < outHeight; oy++) {
    final y0 = ys.lo[oy], y1 = ys.hi[oy], fy = ys.frac[oy];
    for (var ox = 0; ox < outWidth; ox++) {
      final x0 = xs.lo[ox], x1 = xs.hi[ox], fx = xs.frac[ox];
      for (var c = 0; c < 3; c++) {
        final tl = rgb[(y0 * w + x0) * 3 + c], tr = rgb[(y0 * w + x1) * 3 + c];
        final bl = rgb[(y1 * w + x0) * 3 + c], br = rgb[(y1 * w + x1) * 3 + c];
        final top = tl + (tr - tl) * fx;
        final bottom = bl + (br - bl) * fx;
        out[o++] = (top + (bottom - top) * fy).clamp(0, 255);
      }
    }
  }
  return out;
}

/// Source positions of each output row or column (TensorFlow's half-pixel rule).
class _Axis {
  _Axis(int inSize, int outSize) : lo = Int32List(outSize), hi = Int32List(outSize), frac = Float64List(outSize) {
    final scale = inSize / outSize;
    for (var i = 0; i < outSize; i++) {
      final pos = (i + 0.5) * scale - 0.5;
      final f = pos.floorToDouble();
      lo[i] = math.max(f.toInt(), 0);
      hi[i] = math.min(pos.ceil(), inSize - 1);
      frac[i] = pos - f;
    }
  }

  final Int32List lo;
  final Int32List hi;
  final Float64List frac;
}
