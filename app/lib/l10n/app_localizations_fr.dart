// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for French (`fr`).
class AppLocalizationsFr extends AppLocalizations {
  AppLocalizationsFr([String locale = 'fr']) : super(locale);

  @override
  String get appTitle => 'Calories des plats africains';

  @override
  String get today => 'Aujourd\'hui';

  @override
  String get journalEmpty => 'Rien de noté aujourd\'hui. Prenez votre plat en photo ou choisissez-le dans la liste.';

  @override
  String get totalToday => 'Total du jour';

  @override
  String get takePhoto => 'Prendre une photo';

  @override
  String get choosePhoto => 'Choisir une photo';

  @override
  String get chooseFromList => 'Choisir dans la liste';

  @override
  String get addDish => 'Ajouter un plat';

  @override
  String get recognising => 'Reconnaissance du plat…';

  @override
  String get resultTitle => 'Votre plat';

  @override
  String get notRecognised => 'Plat non reconnu';

  @override
  String notRecognisedHelp(int recognised, int count) {
    return 'Pour l\'instant, l\'application reconnaît $recognised plats sur les photos. Choisissez le vôtre dans la liste de $count plats.';
  }

  @override
  String get mostLikely => 'Le plus probable';

  @override
  String get otherSuggestions => 'Ou peut-être';

  @override
  String get unsureSuggestions => 'Propositions peu sûres';

  @override
  String get notInSuggestions => 'Ce n\'est pas ce plat ? Choisissez-le dans la liste.';

  @override
  String get photoError => 'Impossible de lire cette photo.';

  @override
  String get modelUnavailable =>
      'La reconnaissance par photo n\'est pas disponible sur ce téléphone. Vous pouvez choisir le plat dans la liste.';

  @override
  String get searchDishes => 'Chercher un plat';

  @override
  String get noDishFound => 'Aucun plat trouvé.';

  @override
  String get recognisedOnPhotos => 'Reconnu sur les photos';

  @override
  String kcalPer100g(String kcal) {
    return '$kcal kcal pour 100 g';
  }

  @override
  String get portion => 'Portion';

  @override
  String get portionSmall => 'Petite';

  @override
  String get portionMedium => 'Moyenne';

  @override
  String get portionLarge => 'Grande';

  @override
  String grams(int grams) {
    return '$grams g';
  }

  @override
  String kcal(String value) {
    return '$value kcal';
  }

  @override
  String range(String low, String high) {
    return 'entre $low et $high';
  }

  @override
  String get energy => 'Énergie';

  @override
  String get protein => 'Protéines';

  @override
  String get carbohydrate => 'Glucides';

  @override
  String get fat => 'Lipides';

  @override
  String get fibre => 'Fibres';

  @override
  String get nutrientsForPortion => 'Pour cette portion';

  @override
  String get rangeExplanation =>
      'Les valeurs sont une fourchette, car les recettes varient, surtout la quantité d\'huile.';

  @override
  String get recipeNotValidated => 'Recette type, pas encore vérifiée par un nutritionniste.';

  @override
  String get addToJournal => 'Ajouter au journal du jour';

  @override
  String get addedToJournal => 'Ajouté au journal';

  @override
  String get removedFromJournal => 'Retiré du journal';

  @override
  String get undo => 'Annuler';

  @override
  String get delete => 'Supprimer';

  @override
  String get settings => 'Réglages';

  @override
  String get language => 'Langue';

  @override
  String get languageSystem => 'Langue du téléphone';

  @override
  String get theme => 'Thème';

  @override
  String get themeSystem => 'Comme le téléphone';

  @override
  String get themeLight => 'Clair';

  @override
  String get themeDark => 'Sombre';

  @override
  String get about => 'À propos';

  @override
  String get aboutOffline =>
      'Tout fonctionne sur votre téléphone, sans connexion internet. Les photos et le journal n\'en sortent jamais.';

  @override
  String aboutModel(String license) {
    return 'Modèle de reconnaissance : licence $license, pour un usage non commercial.';
  }

  @override
  String get aboutNutrition =>
      'Les valeurs nutritionnelles sont calculées à partir de recettes types et de cette table :';

  @override
  String get aboutCode => 'Code open source (licence MIT) : github.com/Backaad/african-food-calories';
}
