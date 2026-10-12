import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../journal/journal.dart';
import '../services.dart';
import 'dish_list_page.dart';
import 'format.dart';
import 'nutrients_card.dart';
import 'result_page.dart';
import 'settings_page.dart';

/// Today's journal with its total, and the button to add a dish.
class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final services = Services.of(context);
    final fmt = Fmt(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(fmt.l10n.appTitle),
        actions: [
          IconButton(
            tooltip: fmt.l10n.settings,
            icon: const Icon(Icons.settings_outlined),
            onPressed: () => Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => const SettingsPage())),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        key: const Key('add-dish'),
        onPressed: () => _showAddSheet(context),
        icon: const Icon(Icons.add_a_photo_outlined),
        label: Text(fmt.l10n.addDish),
      ),
      body: ListenableBuilder(
        listenable: services.journal,
        builder: (context, _) {
          final entries = services.journal.entriesOn(DateTime.now());
          return ListView(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 96),
            children: [
              NutrientsCard(title: fmt.l10n.totalToday, nutrients: totalOf(entries, services.catalog)),
              const SizedBox(height: 16),
              Text(fmt.l10n.today, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              if (entries.isEmpty)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 24),
                  child: Text(fmt.l10n.journalEmpty, textAlign: TextAlign.center),
                ),
              for (final entry in entries.reversed) _EntryTile(entry: entry),
            ],
          );
        },
      ),
    );
  }

  Future<void> _showAddSheet(BuildContext context) async {
    final services = Services.of(context);
    final l10n = Fmt(context).l10n;
    final canRecognise = services.classifier != null;
    final choice = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (canRecognise) ...[
              ListTile(
                leading: const Icon(Icons.photo_camera_outlined),
                title: Text(l10n.takePhoto),
                onTap: () => Navigator.pop(context, 'camera'),
              ),
              ListTile(
                leading: const Icon(Icons.photo_library_outlined),
                title: Text(l10n.choosePhoto),
                onTap: () => Navigator.pop(context, 'gallery'),
              ),
            ] else
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Text(l10n.modelUnavailable),
              ),
            ListTile(
              leading: const Icon(Icons.list_alt_outlined),
              title: Text(l10n.chooseFromList),
              onTap: () => Navigator.pop(context, 'list'),
            ),
          ],
        ),
      ),
    );
    if (choice == null || !context.mounted) return;
    if (choice == 'list') {
      await Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => const DishListPage()));
      return;
    }
    final photo = await services.photos.pick(choice == 'camera' ? PhotoOrigin.camera : PhotoOrigin.gallery);
    if (photo == null || !context.mounted) return;
    await Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => ResultPage(photo: photo)));
  }
}

class _EntryTile extends StatelessWidget {
  const _EntryTile({required this.entry});

  final JournalEntry entry;

  @override
  Widget build(BuildContext context) {
    final services = Services.of(context);
    final fmt = Fmt(context);
    final dish = services.catalog[entry.dishId];
    final time = DateFormat.Hm(Localizations.localeOf(context).toString()).format(entry.time);
    final energy = dish?.forGrams(entry.grams).energyKcal;
    return Dismissible(
      key: ValueKey(entry.id),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 16),
        color: Theme.of(context).colorScheme.errorContainer,
        child: Icon(Icons.delete_outline, semanticLabel: fmt.l10n.delete),
      ),
      onDismissed: (_) async {
        final messenger = ScaffoldMessenger.of(context);
        await services.journal.remove(entry.id);
        messenger.showSnackBar(
          SnackBar(
            content: Text(fmt.l10n.removedFromJournal),
            action: SnackBarAction(label: fmt.l10n.undo, onPressed: () => services.journal.restore(entry)),
          ),
        );
      },
      child: ListTile(
        contentPadding: EdgeInsets.zero,
        title: Text(dish?.name(fmt.language) ?? entry.dishId),
        subtitle: Text('$time · ${fmt.portionName(entry.portion)} · ${fmt.l10n.grams(entry.grams)}'),
        trailing: energy == null
            ? null
            : Text(fmt.l10n.kcal(fmt.kcal(energy.typical)), style: Theme.of(context).textTheme.titleSmall),
      ),
    );
  }
}
