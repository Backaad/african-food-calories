import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:tflite_flutter/tflite_flutter.dart';

import 'decision.dart';
import 'model_info.dart';
import 'preprocess.dart';

/// Recognises the dish on a photo. Everything runs on the phone.
abstract class DishClassifier {
  ModelInfo get info;

  /// One probability per label of [info], in the same order.
  Future<List<double>> probabilities(Uint8List photo);

  Future<Recognition> recognise(Uint8List photo) async => decide(await probabilities(photo), info);

  void close() {}
}

class TfliteDishClassifier extends DishClassifier {
  TfliteDishClassifier._(this.info, this._interpreter);

  static Future<TfliteDishClassifier> load({
    String model = 'assets/model.tflite',
    String modelInfo = 'assets/model_info.json',
  }) async {
    final info = ModelInfo.fromJsonString(await rootBundle.loadString(modelInfo));
    final interpreter = await Interpreter.fromAsset(model, options: InterpreterOptions()..threads = 2);
    final input = interpreter.getInputTensor(0).shape;
    final output = interpreter.getOutputTensor(0).shape;
    if (input.length != 4 ||
        input[1] != info.inputSize ||
        input[2] != info.inputSize ||
        input[3] != 3 ||
        output.last != info.labels.length) {
      interpreter.close();
      throw StateError('model shape $input -> $output does not match model_info.json');
    }
    return TfliteDishClassifier._(info, interpreter);
  }

  @override
  final ModelInfo info;
  final Interpreter _interpreter;

  @override
  Future<List<double>> probabilities(Uint8List photo) async {
    // Decoding a photo takes a moment: do it away from the screen's thread.
    final size = info.inputSize;
    final input = await compute((Uint8List b) => photoToInput(b, size), photo);
    final output = Float32List(info.labels.length);
    _interpreter.run(input.buffer, output.buffer);
    return output.toList();
  }

  @override
  void close() => _interpreter.close();
}
