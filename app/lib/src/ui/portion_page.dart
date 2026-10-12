import 'package:flutter/material.dart';

import '../nutrition/dish.dart';
import '../services.dart';
import 'format.dart';
import 'nutrients_card.dart';

/// Choose the portion, see the calories and nutrients, add to the journal.
class PortionPage extends StatefulWidget {
  const PortionPage({super.key, required this.dish});

  final Dish dish;

  @override
  State<PortionPage> createState() => _PortionPageState();
}

class _PortionPageState extends State<PortionPage> {
  PortionSize _size = PortionSize.medium;

  @override
  Widget build(BuildContext context) {
    final services = Services.of(context);
    final fmt = Fmt(context);
    final theme = Theme.of(context);
    final dish = widget.dish;
    final portion = dish.portions.firstWhere((p) => p.size == _size, orElse: () => dish.portions.first);
    final note = theme.textTheme.bodySmall;
    return Scaffold(
      appBar: AppBar(title: Text(dish.name(fmt.language))),
      // Always visible, under the scrolling details.
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
          child: FilledButton.icon(
            key: const Key('add-to-journal'),
            onPressed: () async {
              final navigator = Navigator.of(context);
              final messenger = ScaffoldMessenger.of(context);
              await services.journal.add(dish.id, portion);
              navigator.popUntil((route) => route.isFirst);
              messenger.showSnackBar(SnackBar(content: Text(fmt.l10n.addedToJournal)));
            },
            icon: const Icon(Icons.add),
            label: Text(fmt.l10n.addToJournal),
          ),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(fmt.l10n.portion, style: theme.textTheme.titleMedium),
          const SizedBox(height: 8),
          SegmentedButton<PortionSize>(
            key: const Key('portion'),
            showSelectedIcon: false,
            segments: [
              for (final p in dish.portions)
                ButtonSegment(
                  value: p.size,
                  label: Text('${fmt.portionName(p.size)}\n${fmt.l10n.grams(p.grams)}', textAlign: TextAlign.center),
                ),
            ],
            selected: {portion.size},
            onSelectionChanged: (s) => setState(() => _size = s.first),
          ),
          const SizedBox(height: 16),
          NutrientsCard(title: fmt.l10n.nutrientsForPortion, nutrients: dish.forGrams(portion.grams)),
          const SizedBox(height: 8),
          Text(fmt.l10n.rangeExplanation, style: note),
          if (!dish.validatedByNutritionist) Text(fmt.l10n.recipeNotValidated, style: note),
          Text(services.catalog.disclaimer[fmt.language] ?? services.catalog.disclaimer['en']!, style: note),
        ],
      ),
    );
  }
}
