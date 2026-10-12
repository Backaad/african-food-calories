import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_fr.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale) : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate = _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates = <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[Locale('en'), Locale('fr')];

  /// No description provided for @appTitle.
  ///
  /// In en, this message translates to:
  /// **'African Food Calories'**
  String get appTitle;

  /// No description provided for @today.
  ///
  /// In en, this message translates to:
  /// **'Today'**
  String get today;

  /// No description provided for @journalEmpty.
  ///
  /// In en, this message translates to:
  /// **'Nothing logged today. Take a photo of your dish or choose it from the list.'**
  String get journalEmpty;

  /// No description provided for @totalToday.
  ///
  /// In en, this message translates to:
  /// **'Total today'**
  String get totalToday;

  /// No description provided for @takePhoto.
  ///
  /// In en, this message translates to:
  /// **'Take a photo'**
  String get takePhoto;

  /// No description provided for @choosePhoto.
  ///
  /// In en, this message translates to:
  /// **'Choose a photo'**
  String get choosePhoto;

  /// No description provided for @chooseFromList.
  ///
  /// In en, this message translates to:
  /// **'Choose from the list'**
  String get chooseFromList;

  /// No description provided for @addDish.
  ///
  /// In en, this message translates to:
  /// **'Add a dish'**
  String get addDish;

  /// No description provided for @recognising.
  ///
  /// In en, this message translates to:
  /// **'Recognising the dish…'**
  String get recognising;

  /// No description provided for @resultTitle.
  ///
  /// In en, this message translates to:
  /// **'Your dish'**
  String get resultTitle;

  /// No description provided for @notRecognised.
  ///
  /// In en, this message translates to:
  /// **'Dish not recognised'**
  String get notRecognised;

  /// No description provided for @notRecognisedHelp.
  ///
  /// In en, this message translates to:
  /// **'For now the app recognises {recognised} dishes on photos. Choose yours from the list of {count} dishes.'**
  String notRecognisedHelp(int recognised, int count);

  /// No description provided for @mostLikely.
  ///
  /// In en, this message translates to:
  /// **'Most likely'**
  String get mostLikely;

  /// No description provided for @otherSuggestions.
  ///
  /// In en, this message translates to:
  /// **'Or perhaps'**
  String get otherSuggestions;

  /// No description provided for @unsureSuggestions.
  ///
  /// In en, this message translates to:
  /// **'Unsure guesses'**
  String get unsureSuggestions;

  /// No description provided for @notInSuggestions.
  ///
  /// In en, this message translates to:
  /// **'Not this dish? Choose it from the list.'**
  String get notInSuggestions;

  /// No description provided for @photoError.
  ///
  /// In en, this message translates to:
  /// **'This photo could not be read.'**
  String get photoError;

  /// No description provided for @modelUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Photo recognition is not available on this phone. You can still choose the dish from the list.'**
  String get modelUnavailable;

  /// No description provided for @searchDishes.
  ///
  /// In en, this message translates to:
  /// **'Search a dish'**
  String get searchDishes;

  /// No description provided for @noDishFound.
  ///
  /// In en, this message translates to:
  /// **'No dish found.'**
  String get noDishFound;

  /// No description provided for @recognisedOnPhotos.
  ///
  /// In en, this message translates to:
  /// **'Recognised on photos'**
  String get recognisedOnPhotos;

  /// No description provided for @kcalPer100g.
  ///
  /// In en, this message translates to:
  /// **'{kcal} kcal per 100 g'**
  String kcalPer100g(String kcal);

  /// No description provided for @portion.
  ///
  /// In en, this message translates to:
  /// **'Portion'**
  String get portion;

  /// No description provided for @portionSmall.
  ///
  /// In en, this message translates to:
  /// **'Small'**
  String get portionSmall;

  /// No description provided for @portionMedium.
  ///
  /// In en, this message translates to:
  /// **'Medium'**
  String get portionMedium;

  /// No description provided for @portionLarge.
  ///
  /// In en, this message translates to:
  /// **'Large'**
  String get portionLarge;

  /// No description provided for @grams.
  ///
  /// In en, this message translates to:
  /// **'{grams} g'**
  String grams(int grams);

  /// No description provided for @kcal.
  ///
  /// In en, this message translates to:
  /// **'{value} kcal'**
  String kcal(String value);

  /// No description provided for @range.
  ///
  /// In en, this message translates to:
  /// **'between {low} and {high}'**
  String range(String low, String high);

  /// No description provided for @energy.
  ///
  /// In en, this message translates to:
  /// **'Energy'**
  String get energy;

  /// No description provided for @protein.
  ///
  /// In en, this message translates to:
  /// **'Protein'**
  String get protein;

  /// No description provided for @carbohydrate.
  ///
  /// In en, this message translates to:
  /// **'Carbohydrate'**
  String get carbohydrate;

  /// No description provided for @fat.
  ///
  /// In en, this message translates to:
  /// **'Fat'**
  String get fat;

  /// No description provided for @fibre.
  ///
  /// In en, this message translates to:
  /// **'Fibre'**
  String get fibre;

  /// No description provided for @nutrientsForPortion.
  ///
  /// In en, this message translates to:
  /// **'For this portion'**
  String get nutrientsForPortion;

  /// No description provided for @rangeExplanation.
  ///
  /// In en, this message translates to:
  /// **'Values are a range because recipes vary, above all the amount of oil.'**
  String get rangeExplanation;

  /// No description provided for @recipeNotValidated.
  ///
  /// In en, this message translates to:
  /// **'Typical recipe, not yet checked by a nutritionist.'**
  String get recipeNotValidated;

  /// No description provided for @addToJournal.
  ///
  /// In en, this message translates to:
  /// **'Add to today\'s journal'**
  String get addToJournal;

  /// No description provided for @addedToJournal.
  ///
  /// In en, this message translates to:
  /// **'Added to the journal'**
  String get addedToJournal;

  /// No description provided for @removedFromJournal.
  ///
  /// In en, this message translates to:
  /// **'Removed from the journal'**
  String get removedFromJournal;

  /// No description provided for @undo.
  ///
  /// In en, this message translates to:
  /// **'Undo'**
  String get undo;

  /// No description provided for @delete.
  ///
  /// In en, this message translates to:
  /// **'Delete'**
  String get delete;

  /// No description provided for @settings.
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get settings;

  /// No description provided for @language.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get language;

  /// No description provided for @languageSystem.
  ///
  /// In en, this message translates to:
  /// **'Phone language'**
  String get languageSystem;

  /// No description provided for @theme.
  ///
  /// In en, this message translates to:
  /// **'Theme'**
  String get theme;

  /// No description provided for @themeSystem.
  ///
  /// In en, this message translates to:
  /// **'Like the phone'**
  String get themeSystem;

  /// No description provided for @themeLight.
  ///
  /// In en, this message translates to:
  /// **'Light'**
  String get themeLight;

  /// No description provided for @themeDark.
  ///
  /// In en, this message translates to:
  /// **'Dark'**
  String get themeDark;

  /// No description provided for @about.
  ///
  /// In en, this message translates to:
  /// **'About'**
  String get about;

  /// No description provided for @aboutOffline.
  ///
  /// In en, this message translates to:
  /// **'Everything runs on your phone, without an internet connection. Photos and the journal never leave it.'**
  String get aboutOffline;

  /// No description provided for @aboutModel.
  ///
  /// In en, this message translates to:
  /// **'Recognition model: licence {license}, for non-commercial use.'**
  String aboutModel(String license);

  /// No description provided for @aboutNutrition.
  ///
  /// In en, this message translates to:
  /// **'Nutrition values are calculated from typical recipes and this table:'**
  String get aboutNutrition;

  /// No description provided for @aboutCode.
  ///
  /// In en, this message translates to:
  /// **'Open-source code (MIT licence): github.com/Backaad/african-food-calories'**
  String get aboutCode;
}

class _AppLocalizationsDelegate extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) => <String>['en', 'fr'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'fr':
      return AppLocalizationsFr();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
