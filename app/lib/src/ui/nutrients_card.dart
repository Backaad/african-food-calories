import 'package:flutter/material.dart';

import '../nutrition/dish.dart';
import 'format.dart';

/// Energy in large type, then the nutrients, each with its range.
class NutrientsCard extends StatelessWidget {
  const NutrientsCard({super.key, required this.title, required this.nutrients});

  final String title;
  final Nutrients nutrients;

  @override
  Widget build(BuildContext context) {
    final fmt = Fmt(context);
    final theme = Theme.of(context);
    final rows = [
      (fmt.l10n.protein, nutrients.proteinG),
      (fmt.l10n.carbohydrate, nutrients.carbohydrateG),
      (fmt.l10n.fat, nutrients.fatG),
      (fmt.l10n.fibre, nutrients.fibreG),
    ];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: theme.textTheme.titleSmall),
            const SizedBox(height: 4),
            Text(
              fmt.l10n.kcal(fmt.kcal(nutrients.energyKcal.typical)),
              key: const Key('energy'),
              style: theme.textTheme.displaySmall?.copyWith(color: theme.colorScheme.primary),
            ),
            Text(fmt.kcalRange(nutrients.energyKcal), style: theme.textTheme.bodyMedium),
            const Divider(height: 24),
            for (final (name, range) in rows)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    Expanded(child: Text(name)),
                    Text('${fmt.grams(range.typical)} g', style: theme.textTheme.titleSmall),
                    const SizedBox(width: 12),
                    SizedBox(
                      width: 130,
                      child: Text(fmt.gramsRange(range), textAlign: TextAlign.end, style: theme.textTheme.bodySmall),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
