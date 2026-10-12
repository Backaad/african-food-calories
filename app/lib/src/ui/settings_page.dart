import 'package:flutter/material.dart';

import '../services.dart';
import 'format.dart';

/// Language, theme, and where the numbers come from.
class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final services = Services.of(context);
    final settings = services.settings;
    final fmt = Fmt(context);
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(fmt.l10n.settings)),
      body: ListenableBuilder(
        listenable: settings,
        builder: (context, _) => ListView(
          padding: const EdgeInsets.symmetric(vertical: 8),
          children: [
            _Header(fmt.l10n.language),
            RadioGroup<String>(
              groupValue: settings.languageCode ?? 'system',
              onChanged: (v) => settings.setLanguageCode(v == 'system' ? null : v),
              child: Column(
                children: [
                  RadioListTile(value: 'system', title: Text(fmt.l10n.languageSystem)),
                  const RadioListTile(value: 'fr', title: Text('Français')),
                  const RadioListTile(value: 'en', title: Text('English')),
                ],
              ),
            ),
            _Header(fmt.l10n.theme),
            RadioGroup<ThemeMode>(
              groupValue: settings.themeMode,
              onChanged: (v) => settings.setThemeMode(v ?? ThemeMode.system),
              child: Column(
                children: [
                  RadioListTile(value: ThemeMode.system, title: Text(fmt.l10n.themeSystem)),
                  RadioListTile(value: ThemeMode.light, title: Text(fmt.l10n.themeLight)),
                  RadioListTile(value: ThemeMode.dark, title: Text(fmt.l10n.themeDark)),
                ],
              ),
            ),
            _Header(fmt.l10n.about),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(fmt.l10n.aboutOffline),
                  const SizedBox(height: 12),
                  Text(
                    services.catalog.disclaimer[fmt.language] ?? services.catalog.disclaimer['en']!,
                    style: theme.textTheme.titleSmall,
                  ),
                  const SizedBox(height: 12),
                  Text(fmt.l10n.aboutNutrition),
                  const SizedBox(height: 4),
                  Text(services.catalog.source, style: theme.textTheme.bodySmall),
                  const SizedBox(height: 4),
                  Text(services.catalog.sourceTerms, style: theme.textTheme.bodySmall),
                  if (services.classifier case final classifier?) ...[
                    const SizedBox(height: 12),
                    Text(fmt.l10n.aboutModel(classifier.info.license)),
                  ],
                  const SizedBox(height: 12),
                  Text(fmt.l10n.aboutCode),
                  const SizedBox(height: 24),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header(this.text);

  final String text;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
    child: Text(
      text,
      style: Theme.of(context).textTheme.titleSmall?.copyWith(color: Theme.of(context).colorScheme.primary),
    ),
  );
}
