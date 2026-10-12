import 'dart:convert';

/// A value given as a range: the recipe, above all its oil, varies between cooks.
class Range {
  const Range(this.low, this.typical, this.high);

  factory Range.fromJson(Map<String, dynamic> json) =>
      Range((json['low'] as num).toDouble(), (json['typical'] as num).toDouble(), (json['high'] as num).toDouble());

  static const zero = Range(0, 0, 0);

  final double low;
  final double typical;
  final double high;

  Range operator +(Range other) => Range(low + other.low, typical + other.typical, high + other.high);

  Range scale(double factor) => Range(low * factor, typical * factor, high * factor);
}

/// Energy and nutrients of a quantity of dish.
class Nutrients {
  const Nutrients({
    required this.energyKcal,
    required this.proteinG,
    required this.fatG,
    required this.carbohydrateG,
    required this.fibreG,
  });

  factory Nutrients.fromJson(Map<String, dynamic> json) => Nutrients(
    energyKcal: Range.fromJson(json['energy_kcal']),
    proteinG: Range.fromJson(json['protein_g']),
    fatG: Range.fromJson(json['fat_g']),
    carbohydrateG: Range.fromJson(json['carbohydrate_g']),
    fibreG: Range.fromJson(json['fibre_g']),
  );

  static const zero = Nutrients(
    energyKcal: Range.zero,
    proteinG: Range.zero,
    fatG: Range.zero,
    carbohydrateG: Range.zero,
    fibreG: Range.zero,
  );

  final Range energyKcal;
  final Range proteinG;
  final Range fatG;
  final Range carbohydrateG;
  final Range fibreG;

  Nutrients operator +(Nutrients o) => Nutrients(
    energyKcal: energyKcal + o.energyKcal,
    proteinG: proteinG + o.proteinG,
    fatG: fatG + o.fatG,
    carbohydrateG: carbohydrateG + o.carbohydrateG,
    fibreG: fibreG + o.fibreG,
  );

  Nutrients scale(double factor) => Nutrients(
    energyKcal: energyKcal.scale(factor),
    proteinG: proteinG.scale(factor),
    fatG: fatG.scale(factor),
    carbohydrateG: carbohydrateG.scale(factor),
    fibreG: fibreG.scale(factor),
  );
}

enum PortionSize { small, medium, large }

class Portion {
  const Portion(this.size, this.grams);

  final PortionSize size;
  final int grams;
}

class Dish {
  const Dish({
    required this.id,
    required this.names,
    required this.countries,
    required this.per100g,
    required this.portions,
    required this.recipeSources,
    required this.validatedByNutritionist,
  });

  factory Dish.fromJson(Map<String, dynamic> json) => Dish(
    id: json['id'] as String,
    names: Map<String, String>.from(json['names'] as Map),
    countries: List<String>.from(json['countries'] as List),
    per100g: Nutrients.fromJson(json['per_100g']),
    portions: [
      for (final p in json['portions'] as List)
        Portion(PortionSize.values.byName(p['size'] as String), (p['grams'] as num).toInt()),
    ],
    recipeSources: List<String>.from(json['recipe_sources'] as List? ?? []),
    validatedByNutritionist: json['validated_by_nutritionist'] == true,
  );

  final String id;
  final Map<String, String> names;
  final List<String> countries;
  final Nutrients per100g;
  final List<Portion> portions;
  final List<String> recipeSources;
  final bool validatedByNutritionist;

  /// Name in the given language, English if missing.
  String name(String languageCode) => names[languageCode] ?? names['en'] ?? id;

  Nutrients forGrams(num grams) => per100g.scale(grams / 100);
}

/// All dishes of nutrition/dishes.json, with its disclaimer and source.
class DishCatalog {
  DishCatalog({required List<Dish> dishes, required this.disclaimer, required this.source, required this.sourceTerms})
    : _byId = {for (final d in dishes) d.id: d};

  factory DishCatalog.fromJsonString(String text) {
    final json = jsonDecode(text) as Map<String, dynamic>;
    return DishCatalog(
      dishes: [for (final d in json['dishes'] as List) Dish.fromJson(d as Map<String, dynamic>)],
      disclaimer: Map<String, String>.from(json['disclaimer'] as Map),
      source: json['source'] as String,
      sourceTerms: json['source_terms'] as String,
    );
  }

  final Map<String, Dish> _byId;
  final Map<String, String> disclaimer;
  final String source;
  final String sourceTerms;

  Iterable<Dish> get dishes => _byId.values;

  Dish? operator [](String id) => _byId[id];

  /// Dishes sorted by their name in [languageCode], keeping only those whose
  /// name or id contains [query] (accents and case ignored).
  List<Dish> search(String query, String languageCode) {
    final q = foldText(query.trim());
    final found = dishes.where(
      (d) =>
          q.isEmpty ||
          foldText(d.name(languageCode)).contains(q) ||
          foldText(d.name('en')).contains(q) ||
          d.id.contains(q),
    );
    return found.toList()..sort((a, b) => foldText(a.name(languageCode)).compareTo(foldText(b.name(languageCode))));
  }
}

const _accents = {
  'à': 'a',
  'á': 'a',
  'â': 'a',
  'ä': 'a',
  'ã': 'a',
  'ç': 'c',
  'è': 'e',
  'é': 'e',
  'ê': 'e',
  'ë': 'e',
  'ì': 'i',
  'í': 'i',
  'î': 'i',
  'ï': 'i',
  'ñ': 'n',
  'ò': 'o',
  'ó': 'o',
  'ô': 'o',
  'ö': 'o',
  'õ': 'o',
  'ù': 'u',
  'ú': 'u',
  'û': 'u',
  'ü': 'u',
  'ÿ': 'y',
};

/// Lower case without accents, so "ndole" finds "Ndolé".
String foldText(String text) => text.toLowerCase().split('').map((c) => _accents[c] ?? c).join();
