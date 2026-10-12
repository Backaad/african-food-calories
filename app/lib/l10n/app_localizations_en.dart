// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'African Food Calories';

  @override
  String get today => 'Today';

  @override
  String get journalEmpty => 'Nothing logged today. Take a photo of your dish or choose it from the list.';

  @override
  String get totalToday => 'Total today';

  @override
  String get takePhoto => 'Take a photo';

  @override
  String get choosePhoto => 'Choose a photo';

  @override
  String get chooseFromList => 'Choose from the list';

  @override
  String get addDish => 'Add a dish';

  @override
  String get recognising => 'Recognising the dish…';

  @override
  String get resultTitle => 'Your dish';

  @override
  String get notRecognised => 'Dish not recognised';

  @override
  String notRecognisedHelp(int recognised, int count) {
    return 'For now the app recognises $recognised dishes on photos. Choose yours from the list of $count dishes.';
  }

  @override
  String get mostLikely => 'Most likely';

  @override
  String get otherSuggestions => 'Or perhaps';

  @override
  String get unsureSuggestions => 'Unsure guesses';

  @override
  String get notInSuggestions => 'Not this dish? Choose it from the list.';

  @override
  String get photoError => 'This photo could not be read.';

  @override
  String get modelUnavailable =>
      'Photo recognition is not available on this phone. You can still choose the dish from the list.';

  @override
  String get searchDishes => 'Search a dish';

  @override
  String get noDishFound => 'No dish found.';

  @override
  String get recognisedOnPhotos => 'Recognised on photos';

  @override
  String kcalPer100g(String kcal) {
    return '$kcal kcal per 100 g';
  }

  @override
  String get portion => 'Portion';

  @override
  String get portionSmall => 'Small';

  @override
  String get portionMedium => 'Medium';

  @override
  String get portionLarge => 'Large';

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
    return 'between $low and $high';
  }

  @override
  String get energy => 'Energy';

  @override
  String get protein => 'Protein';

  @override
  String get carbohydrate => 'Carbohydrate';

  @override
  String get fat => 'Fat';

  @override
  String get fibre => 'Fibre';

  @override
  String get nutrientsForPortion => 'For this portion';

  @override
  String get rangeExplanation => 'Values are a range because recipes vary, above all the amount of oil.';

  @override
  String get recipeNotValidated => 'Typical recipe, not yet checked by a nutritionist.';

  @override
  String get addToJournal => 'Add to today\'s journal';

  @override
  String get addedToJournal => 'Added to the journal';

  @override
  String get removedFromJournal => 'Removed from the journal';

  @override
  String get undo => 'Undo';

  @override
  String get delete => 'Delete';

  @override
  String get settings => 'Settings';

  @override
  String get language => 'Language';

  @override
  String get languageSystem => 'Phone language';

  @override
  String get theme => 'Theme';

  @override
  String get themeSystem => 'Like the phone';

  @override
  String get themeLight => 'Light';

  @override
  String get themeDark => 'Dark';

  @override
  String get about => 'About';

  @override
  String get aboutOffline =>
      'Everything runs on your phone, without an internet connection. Photos and the journal never leave it.';

  @override
  String aboutModel(String license) {
    return 'Recognition model: licence $license, for non-commercial use.';
  }

  @override
  String get aboutNutrition => 'Nutrition values are calculated from typical recipes and this table:';

  @override
  String get aboutCode => 'Open-source code (MIT licence): github.com/Backaad/african-food-calories';
}
