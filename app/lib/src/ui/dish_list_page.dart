import 'package:flutter/material.dart';

import '../services.dart';
import 'format.dart';
import 'portion_page.dart';

/// Every dish of the catalogue, searchable, for manual entry.
class DishListPage extends StatefulWidget {
  const DishListPage({super.key});

  @override
  State<DishListPage> createState() => _DishListPageState();
}

class _DishListPageState extends State<DishListPage> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final services = Services.of(context);
    final fmt = Fmt(context);
    final recognisable = services.classifier?.info.labels.toSet() ?? const <String>{};
    final dishes = services.catalog.search(_query, fmt.language);
    return Scaffold(
      appBar: AppBar(title: Text(fmt.l10n.chooseFromList)),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
            child: TextField(
              key: const Key('search'),
              autofocus: false,
              decoration: InputDecoration(
                prefixIcon: const Icon(Icons.search),
                hintText: fmt.l10n.searchDishes,
                border: const OutlineInputBorder(),
              ),
              onChanged: (value) => setState(() => _query = value),
            ),
          ),
          Expanded(
            child: dishes.isEmpty
                ? Center(child: Text(fmt.l10n.noDishFound))
                : ListView.builder(
                    itemCount: dishes.length,
                    itemBuilder: (context, i) {
                      final dish = dishes[i];
                      return ListTile(
                        title: Text(dish.name(fmt.language)),
                        subtitle: Text(fmt.l10n.kcalPer100g(fmt.kcal(dish.per100g.energyKcal.typical))),
                        trailing: recognisable.contains(dish.id)
                            ? Tooltip(
                                message: fmt.l10n.recognisedOnPhotos,
                                child: Icon(Icons.photo_camera_outlined, semanticLabel: fmt.l10n.recognisedOnPhotos),
                              )
                            : null,
                        onTap: () =>
                            Navigator.of(context)
                                .push(MaterialPageRoute<void>(builder: (_) => PortionPage(dish: dish))),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
