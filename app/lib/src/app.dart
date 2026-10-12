import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import '../l10n/app_localizations.dart';
import 'services.dart';
import 'ui/home_page.dart';

const _seed = Color(0xFFB4561E); // palm-oil orange

class AfcApp extends StatelessWidget {
  const AfcApp({super.key});

  @override
  Widget build(BuildContext context) {
    final settings = Services.of(context).settings;
    return ListenableBuilder(
      listenable: settings,
      builder: (context, _) => MaterialApp(
        debugShowCheckedModeBanner: false,
        onGenerateTitle: (context) => AppLocalizations.of(context).appTitle,
        theme: ThemeData(colorSchemeSeed: _seed, brightness: Brightness.light),
        darkTheme: ThemeData(colorSchemeSeed: _seed, brightness: Brightness.dark),
        themeMode: settings.themeMode,
        locale: settings.locale,
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: const HomePage(),
      ),
    );
  }
}
