# Calories des plats africains

[English](README.md)

Une application open source pour téléphone qui reconnaît les plats africains
sur une photo et estime leurs calories, sans connexion. Les applications de
calories connues ne connaissent ni le ndolé, ni l'eru, ni le waakye. Ce projet
commence à combler ce manque avec des données ouvertes, un modèle ouvert et une
méthode de calcul des calories que chacun peut vérifier.

<p>
  <img src="docs/screenshots/1-journal-fr.png" width="180" alt="Journal du jour avec son total">
  <img src="docs/screenshots/2-result-fr.png" width="180" alt="Photo d'alloco reconnue">
  <img src="docs/screenshots/3-portion-fr.png" width="180" alt="Portion, calories et nutriments en fourchette">
  <img src="docs/screenshots/4-list-fr.png" width="180" alt="Liste des 44 plats, avec recherche">
  <img src="docs/screenshots/5-journal-en-dark.png" width="180" alt="Journal en anglais, thème sombre">
</p>

## Ce que fait l'application

1. Prenez votre assiette en photo, ou choisissez une photo dans la galerie.
2. L'application affiche le plat le plus probable et deux autres propositions,
   ou « Plat non reconnu ». Vous pouvez toujours choisir le plat dans la liste
   complète.
3. Choisissez la portion : petite, moyenne ou grande.
4. Voyez les calories et les nutriments (protéines, glucides, lipides, fibres)
   sous forme de **fourchette** : les recettes varient, surtout la quantité
   d'huile.
5. Tenez le journal du jour, avec son total.

Tout se passe sur le téléphone : pas de compte, pas de connexion internet, et
les photos n'en sortent jamais. En français et en anglais, en thème clair et
sombre.

## Où en est le projet : première version

- **44 plats** peuvent être notés depuis la liste, chacun avec ses calories.
- **5 plats sont reconnus sur les photos** pour l'instant : alloco, bobolo,
  foufou, puff-puff (beignets) et ougali. Pour les autres, il faut davantage de
  photos sous licence ouverte.
- Sur le jeu de test, pour les photos de ces cinq plats, le modèle donne le bon
  plat dans 77 % des cas, refuse dans 20 % (« Plat non reconnu ») et se trompe
  de plat dans 3 %. Pour les photos d'autres aliments, il propose à tort un plat
  dans 12 % des cas. Ces photos de test viennent des mêmes sources que les
  photos d'entraînement : l'exactitude sur des photos prises au quotidien avec un
  téléphone n'est pas encore mesurée. Détails : [carte du modèle](docs/model-card.md)
  (en anglais).
- C'est l'utilisateur qui choisit la portion. L'estimer à partir de la photo est
  un problème de recherche, hors de cette version.
- **Les valeurs de calories sont des estimations à faire valider par un
  nutritionniste. Ce n'est pas un conseil médical.**

## Installer (Android 8.0 ou plus récent)

Téléchargez `app-release.apk` dans la dernière
[version publiée](https://github.com/Backaad/african-food-calories/releases),
ouvrez-le sur le téléphone et autorisez l'installation depuis cette source.
C'est une version de test, pas une version du Play Store. Il n'y a pas encore
de version pour iPhone.

## Comment ça marche

**Reconnaissance.** Un modèle MobileNetV3-Large (apprentissage par transfert,
distillé à partir d'un modèle « professeur » EfficientNetV2-S), exporté en
TensorFlow Lite avec des poids en 16 bits (6 Mo). Il a aussi appris une classe
« autre » à partir de photos d'autres aliments : il peut donc dire qu'il ne sait
pas. Un plat n'est affiché que si sa probabilité atteint un seuil, choisi sur
des données de validation. L'entraînement se lance dans un carnet Jupyter sur
Kaggle ou Colab : [`training/`](training/README.md).

**Calories.** Chaque plat a une recette type (grammes de chaque ingrédient pour
100 g de plat), avec une quantité basse et haute pour les ingrédients qui
varient. Les valeurs des ingrédients viennent de la table de composition des
aliments d'Afrique de l'Ouest de la FAO et d'INFOODS (WAFCT 2019). Un script
calcule l'énergie et les nutriments pour 100 g et pour trois portions :
[méthode](docs/nutrition-method.md), [`nutrition/`](nutrition/README.md)
(en anglais).

**Données.** Uniquement des images dont la licence a été vérifiée une par une :
Wikimedia Commons (CC0, domaine public, CC BY, CC BY-SA), et CamerFood10 pour
l'entraînement seulement. Le dépôt ne contient aucune image, seulement les
scripts qui les téléchargent et la liste des sources :
[inventaire des données](docs/data-inventory.md),
[`data/sources.yaml`](data/sources.yaml).

Le modèle et la description des données sont aussi sur Hugging Face :
[backaad/african-food-calories](https://huggingface.co/backaad/african-food-calories)
et [backaad/african-food-calories-data](https://huggingface.co/datasets/backaad/african-food-calories-data).

## Le dépôt

| Dossier | Contenu |
|---|---|
| [`data/`](data/) | Sources et licences, liste des plats, scripts de téléchargement et d'inventaire |
| [`nutrition/`](nutrition/) | Recettes types, extrait de la WAFCT, calcul, `dishes.json` |
| [`training/`](training/) | Carnet et scripts : préparation des données, entraînement, évaluation, export TFLite ; résultats de chaque entraînement |
| [`app/`](app/) | Application Flutter et ses tests |
| [`docs/`](docs/) | Carte du modèle, méthode nutritionnelle, inventaire des données, captures d'écran, descriptif du projet |
| [`hub/`](hub/publish.py) | Publication sur Hugging Face |

Le README de chaque dossier explique comment s'en servir. GitHub Actions lance
les tests de chaque partie et construit l'application Android.

## Licences et crédits

- **Code** : [MIT](LICENSE).
- **Modèle** (`training/results/*/model.tflite`, `app/assets/model.tflite`) :
  **CC BY-NC 4.0**, usage non commercial. Il a en effet été entraîné en partie
  sur CamerFood10, dont les droits sur les images ne sont pas établis (utilisé
  pour l'entraînement seulement, jamais redistribué ; voir
  [`data/sources.yaml`](data/sources.yaml)). L'application, qui contient le
  modèle, ne peut donc être distribuée que pour un usage non commercial.
- **Valeurs nutritionnelles** : calculées à partir de la *FAO/INFOODS Food
  Composition Table for Western Africa (2019)*, © FAO 2020, utilisée pour un
  produit non commercial en citant la FAO comme source et détentrice des droits ;
  la FAO ne cautionne pas ce projet. Citation complète dans
  [`nutrition/dishes.json`](nutrition/dishes.json).
- **Images utilisées pour l'entraînement** : l'auteur et la licence de chaque
  photo de Wikimedia Commons sont listés dans
  `training/results/*/ATTRIBUTION.csv`. CamerFood10 : Baban A Erep & Chaari, 2024.
- **Captures d'écran** : `docs/screenshots/2-result-fr.png` contient une photo
  sous licence CC BY-SA 4.0 ; crédits dans
  [`docs/screenshots/CREDITS.md`](docs/screenshots/CREDITS.md).

## Contribuer

Des recettes vérifiées par des personnes qui cuisinent ces plats, des photos
sous licence ouverte des plats pas encore reconnus, la relecture d'un
nutritionniste, des traductions : voir [CONTRIBUTING.md](CONTRIBUTING.md)
(en anglais).
