import 'model_info.dart';

class Suggestion {
  const Suggestion(this.dishId, this.probability);

  final String dishId;
  final double probability;
}

/// What the app shows after a photo.
class Recognition {
  const Recognition({required this.recognised, required this.suggestions});

  /// True if the first suggestion is confident enough to be shown as the dish.
  /// False means "dish not recognised": the suggestions are then only hints.
  final bool recognised;

  /// Up to three dishes, most likely first (never the "other" label).
  final List<Suggestion> suggestions;
}

/// Applies the rule of model_info.json: show the top label if its probability
/// reaches the threshold and it is not "other"; else "dish not recognised".
Recognition decide(List<double> probabilities, ModelInfo info, {int count = 3}) {
  if (probabilities.length != info.labels.length) {
    throw ArgumentError('expected ${info.labels.length} probabilities, got ${probabilities.length}');
  }
  final order = List<int>.generate(probabilities.length, (i) => i)
    ..sort((a, b) => probabilities[b].compareTo(probabilities[a]));
  final top = order.first;
  final recognised = info.labels[top] != info.otherLabel && probabilities[top] >= info.threshold;
  final suggestions = [
    for (final i in order)
      if (info.labels[i] != info.otherLabel) Suggestion(info.labels[i], probabilities[i]),
  ].take(count).toList();
  return Recognition(recognised: recognised, suggestions: suggestions);
}
