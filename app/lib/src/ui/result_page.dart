import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../nutrition/dish.dart';
import '../recognition/decision.dart';
import '../services.dart';
import 'dish_list_page.dart';
import 'format.dart';
import 'portion_page.dart';

/// The photo, then the most likely dish with two alternatives, or "dish not recognised".
class ResultPage extends StatefulWidget {
  const ResultPage({super.key, required this.photo});

  final Uint8List photo;

  @override
  State<ResultPage> createState() => _ResultPageState();
}

class _ResultPageState extends State<ResultPage> {
  Future<Recognition>? _recognition;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _recognition ??= Services.of(context).classifier!.recognise(widget.photo);
  }

  @override
  Widget build(BuildContext context) {
    final fmt = Fmt(context);
    return Scaffold(
      appBar: AppBar(title: Text(fmt.l10n.resultTitle)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: SizedBox(
              height: 200,
              child: Image.memory(widget.photo, fit: BoxFit.cover, errorBuilder: (_, _, _) => const SizedBox()),
            ),
          ),
          const SizedBox(height: 16),
          FutureBuilder<Recognition>(
            future: _recognition,
            builder: (context, snapshot) {
              if (snapshot.hasError) {
                return _Message(icon: Icons.broken_image_outlined, text: fmt.l10n.photoError);
              }
              if (!snapshot.hasData) {
                return Column(
                  children: [const CircularProgressIndicator(), const SizedBox(height: 8), Text(fmt.l10n.recognising)],
                );
              }
              return _Suggestions(recognition: snapshot.data!);
            },
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            key: const Key('choose-from-list'),
            onPressed: () => Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => const DishListPage())),
            icon: const Icon(Icons.list_alt_outlined),
            label: Text(fmt.l10n.chooseFromList),
          ),
        ],
      ),
    );
  }
}

class _Suggestions extends StatelessWidget {
  const _Suggestions({required this.recognition});

  final Recognition recognition;

  @override
  Widget build(BuildContext context) {
    final services = Services.of(context);
    final fmt = Fmt(context);
    final theme = Theme.of(context);
    final dishes = [
      for (final s in recognition.suggestions)
        if (services.catalog[s.dishId] case final Dish d) d,
    ];
    if (recognition.recognised && dishes.isNotEmpty) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(fmt.l10n.mostLikely, style: theme.textTheme.labelLarge),
          const SizedBox(height: 8),
          FilledButton(
            key: const Key('top-dish'),
            onPressed: () => _open(context, dishes.first),
            style: FilledButton.styleFrom(padding: const EdgeInsets.all(16)),
            child: Text(
              dishes.first.name(fmt.language),
              style: theme.textTheme.titleLarge?.copyWith(color: theme.colorScheme.onPrimary),
            ),
          ),
          if (dishes.length > 1) ...[
            const SizedBox(height: 16),
            Text(fmt.l10n.otherSuggestions, style: theme.textTheme.labelLarge),
            const SizedBox(height: 8),
            _Chips(dishes: dishes.skip(1).toList()),
          ],
          const SizedBox(height: 8),
          Text(fmt.l10n.notInSuggestions, style: theme.textTheme.bodySmall),
        ],
      );
    }
    final recognisable = services.classifier!.info.labels.where((l) => l != services.classifier!.info.otherLabel);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _Message(icon: Icons.help_outline, text: fmt.l10n.notRecognised, key: const Key('not-recognised')),
        const SizedBox(height: 4),
        Text(
          fmt.l10n.notRecognisedHelp(recognisable.length, services.catalog.dishes.length),
          textAlign: TextAlign.center,
        ),
        if (dishes.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text(fmt.l10n.unsureSuggestions, style: theme.textTheme.labelLarge),
          const SizedBox(height: 8),
          _Chips(dishes: dishes),
        ],
      ],
    );
  }
}

class _Chips extends StatelessWidget {
  const _Chips({required this.dishes});

  final List<Dish> dishes;

  @override
  Widget build(BuildContext context) {
    final language = Localizations.localeOf(context).languageCode;
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [for (final d in dishes) ActionChip(label: Text(d.name(language)), onPressed: () => _open(context, d))],
    );
  }
}

class _Message extends StatelessWidget {
  const _Message({super.key, required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Icon(icon, size: 40),
      const SizedBox(height: 8),
      Text(text, style: Theme.of(context).textTheme.titleLarge, textAlign: TextAlign.center),
    ],
  );
}

void _open(BuildContext context, Dish dish) =>
    Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => PortionPage(dish: dish)));
