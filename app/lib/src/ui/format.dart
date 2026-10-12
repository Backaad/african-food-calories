import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../l10n/app_localizations.dart';
import '../nutrition/dish.dart';

/// Number formatting in the user's language (1 234,5 in French).
class Fmt {
  Fmt(BuildContext context)
    : l10n = AppLocalizations.of(context),
      language = Localizations.localeOf(context).languageCode,
      _whole = NumberFormat.decimalPattern(Localizations.localeOf(context).toString()),
      _oneDecimal = NumberFormat('0.0', Localizations.localeOf(context).toString());

  final AppLocalizations l10n;
  final String language;
  final NumberFormat _whole;
  final NumberFormat _oneDecimal;

  String kcal(double value) => _whole.format(value.round());

  /// Grams: one decimal below 10 g, whole grams above.
  String grams(double value) => value < 10 ? _oneDecimal.format(value) : _whole.format(value.round());

  String kcalRange(Range r) => l10n.range(kcal(r.low), kcal(r.high));

  String gramsRange(Range r) => l10n.range(grams(r.low), grams(r.high));

  String portionName(PortionSize size) => switch (size) {
    PortionSize.small => l10n.portionSmall,
    PortionSize.medium => l10n.portionMedium,
    PortionSize.large => l10n.portionLarge,
  };
}
