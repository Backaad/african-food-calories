import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../nutrition/dish.dart';

/// One dish eaten: which dish, how many grams, when.
class JournalEntry {
  const JournalEntry({
    required this.id,
    required this.dishId,
    required this.grams,
    required this.portion,
    required this.time,
  });

  factory JournalEntry.fromJson(Map<String, dynamic> json) => JournalEntry(
    id: json['id'] as String,
    dishId: json['dish'] as String,
    grams: (json['grams'] as num).toInt(),
    portion: PortionSize.values.byName(json['portion'] as String),
    time: DateTime.parse(json['time'] as String),
  );

  final String id;
  final String dishId;
  final int grams;
  final PortionSize portion;
  final DateTime time;

  Map<String, dynamic> toJson() => {
    'id': id,
    'dish': dishId,
    'grams': grams,
    'portion': portion.name,
    'time': time.toIso8601String(),
  };
}

/// The food journal, kept on the phone only (shared preferences).
class Journal extends ChangeNotifier {
  Journal._(this._prefs, this._entries);

  static const _key = 'journal.v1';

  static Future<Journal> load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    final entries = <JournalEntry>[];
    if (raw != null) {
      try {
        for (final e in jsonDecode(raw) as List) {
          entries.add(JournalEntry.fromJson(e as Map<String, dynamic>));
        }
      } on Object catch (error) {
        // A damaged journal must not stop the app; start a new one.
        debugPrint('journal unreadable, starting a new one: $error');
      }
    }
    return Journal._(prefs, entries);
  }

  final SharedPreferences _prefs;
  final List<JournalEntry> _entries;
  int _counter = 0;

  /// Entries of the calendar day of [day] (local time), oldest first.
  List<JournalEntry> entriesOn(DateTime day) =>
      _entries.where((e) => _sameDay(e.time, day)).toList()..sort((a, b) => a.time.compareTo(b.time));

  Future<JournalEntry> add(String dishId, Portion portion, {DateTime? time}) async {
    final when = time ?? DateTime.now();
    final entry = JournalEntry(
      id: '${when.microsecondsSinceEpoch}-${_counter++}',
      dishId: dishId,
      grams: portion.grams,
      portion: portion.size,
      time: when,
    );
    _entries.add(entry);
    await _save();
    return entry;
  }

  Future<void> remove(String id) async {
    _entries.removeWhere((e) => e.id == id);
    await _save();
  }

  /// Puts back an entry removed by mistake.
  Future<void> restore(JournalEntry entry) async {
    _entries.add(entry);
    await _save();
  }

  Future<void> _save() async {
    notifyListeners();
    await _prefs.setString(_key, jsonEncode([for (final e in _entries) e.toJson()]));
  }
}

/// Total of a list of entries. Entries of dishes missing from the catalogue are skipped.
Nutrients totalOf(Iterable<JournalEntry> entries, DishCatalog catalog) {
  var total = Nutrients.zero;
  for (final e in entries) {
    final dish = catalog[e.dishId];
    if (dish != null) total = total + dish.forGrams(e.grams);
  }
  return total;
}

bool _sameDay(DateTime a, DateTime b) {
  final x = a.toLocal(), y = b.toLocal();
  return x.year == y.year && x.month == y.month && x.day == y.day;
}
