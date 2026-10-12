import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Language and theme chosen by the user; by default those of the phone.
class Settings extends ChangeNotifier {
  Settings._(this._prefs)
    : _themeMode = ThemeMode.values.asNameMap()[_prefs.getString(_themeKey)] ?? ThemeMode.system,
      _languageCode = _prefs.getString(_languageKey);

  static const _themeKey = 'settings.theme';
  static const _languageKey = 'settings.language';

  static Future<Settings> load() async => Settings._(await SharedPreferences.getInstance());

  final SharedPreferences _prefs;
  ThemeMode _themeMode;
  String? _languageCode;

  ThemeMode get themeMode => _themeMode;

  /// 'en', 'fr', or null for the phone's language.
  String? get languageCode => _languageCode;

  Locale? get locale => _languageCode == null ? null : Locale(_languageCode!);

  Future<void> setThemeMode(ThemeMode mode) async {
    _themeMode = mode;
    notifyListeners();
    await _prefs.setString(_themeKey, mode.name);
  }

  Future<void> setLanguageCode(String? code) async {
    _languageCode = code;
    notifyListeners();
    if (code == null) {
      await _prefs.remove(_languageKey);
    } else {
      await _prefs.setString(_languageKey, code);
    }
  }
}
