# Calories des plats africains — descriptif du projet

Je veux créer une application qui reconnaît un plat africain sur une photo et donne
une estimation de ses calories. Les applications connues (MyFitnessPal et les
autres) ne connaissent ni le ndolé, ni l'eru, ni le waakye. Ceux qui veulent suivre
leur alimentation en Afrique doivent donc deviner.

Le projet est open source : le code, le modèle et la méthode de calcul des calories
seront publics. L'application fonctionne **sans connexion** : le modèle tourne sur
le téléphone.

Le dépôt s'appelle `african-food-calories` : utilise ce nom partout.

## Les données : on part de ce qui existe

Je ne peux pas photographier les plats moi-même. On construit donc la première
version **uniquement avec des images sous licence ouverte**, téléchargées par
script. Aucune image n'est copiée depuis Google, Facebook, Instagram ou YouTube.

Sources déjà repérées :

| Source | Plats | Licence |
|---|---|---|
| [African Foods Datasets](https://data.mendeley.com/datasets/rrzhwbg3kw) (Mendeley, *Data in Brief* 2024) | Cameroun : ekwang, eru, ndolé (≈ 200 photos chacun). Ghana : jollof, soupe de noix de palme, waakye | CC BY 4.0 |
| [Nigerian Food Dataset](https://data.mendeley.com/datasets/2vktdxfxv7) (Mendeley, 2024) | 10 plats nigérians | CC BY 4.0 |
| [CamerFood10](https://pmc.ncbi.nlm.nih.gov/articles/PMC10781344) (2024) | 10 aliments très consommés au Cameroun, avec contours dessinés (segmentation) | à vérifier |
| [Plats kényans](https://www.cs.bu.edu/fac/betke/papers/Jalal-etal-KenyanFood-2019.pdf) (2019) | 13 plats | à vérifier |
| [Plats éthiopiens](https://universe.roboflow.com/ethiopian-dishes) (Roboflow) | injera, doro wat, tibs… | à vérifier |
| [Plats ghanéens](https://huggingface.co/datasets/devkyle/ghanaian-food-dataset) (Hugging Face) | 30 plats | **aucune licence affichée : ne pas utiliser** sauf clarification |
| Wikimedia Commons, Openverse | quelques photos libres par plat | CC0, CC BY, CC BY-SA, selon la photo |

Avant d'utiliser une source, vérifie sa licence. Note-la, avec les auteurs à citer,
dans `data/sources.yaml`.

Le dépôt **ne contient pas les images**. Il contient les scripts qui les
téléchargent depuis leur source d'origine, et un fichier qui liste chaque source et
ses crédits. Ainsi, on respecte les licences et le dépôt reste léger.

Les plats sont en deux catégories :
- **Reconnus par le modèle** : ceux qui ont assez d'images (repère : au moins
  150 photos utilisables).
- **Disponibles en saisie manuelle** : les autres plats africains (koki, achu, okok,
  poulet DG, mbongo tchobi, sanga, bobolo, attiéké, alloco, ugali, injera…). On les
  choisit dans une liste, avec leurs calories. Ils passeront dans le modèle quand on
  aura des images.

Pour les plats qui n'ont que quelques photos libres, tu peux tester une approche
« peu d'exemples » :
- un petit modèle vision-langage léger (de la famille MobileCLIP ou SigLIP) calcule
  une empreinte de chaque image ;
- on reconnaît le plat par ses plus proches voisins parmi les images connues.

Ne l'intègre que si les mesures sont honnêtement bonnes.

## Les calories : une méthode transparente

Une photo ne donne pas les calories : il faut une méthode, et elle doit être
publique et vérifiable.

- Chaque plat a une **recette type** : ses ingrédients, en grammes pour 100 g de plat.
- Les valeurs de chaque ingrédient viennent de la **table de composition des
  aliments d'Afrique de l'Ouest** de la FAO et d'INFOODS
  ([WAFCT 2019](https://openknowledge.fao.org/items/61350ad9-7afe-4842-9713-e18a4f61aa1a)),
  avec le code de chaque aliment.
- Un script calcule pour chaque plat : les kcal pour 100 g, les protéines, les
  glucides et les lipides.
- On donne une **fourchette**, pas un chiffre unique. L'huile varie énormément d'une
  cuisinière à l'autre : c'est la principale source d'incertitude.
- Chaque plat propose trois portions (petite, moyenne, grande), en grammes, et
  l'utilisateur choisit. Estimer une portion à partir de la photo reste un problème
  de recherche : ce n'est pas pour cette version.
- Tout est rangé dans `nutrition/dishes.json`, avec les sources, et une page
  `docs/nutrition-method.md` explique la méthode.
- Les valeurs sont marquées « estimation à faire valider par un nutritionniste ».
  L'application rappelle qu'elle ne donne pas de conseil médical.

## Le modèle

- Il est entraîné par apprentissage par transfert, sur une base légère faite pour le
  téléphone (MobileNetV3 ou EfficientNet-Lite).
- Une classe « plat non reconnu » est apprise avec des images d'autres aliments, eux
  aussi sous licence ouverte. Le modèle peut ainsi dire qu'il ne sait pas.
- Si les mesures le justifient :
  - on entraîne d'abord un gros modèle « professeur » sur GPU ;
  - celui-ci transmet ce qu'il sait au petit modèle (distillation).
  - J'ai des crédits GPU gratuits pour ça.
- Le modèle final est exporté en TensorFlow Lite (flottants 16 bits). On vérifie que
  sa version téléphone donne les mêmes réponses que l'original.
- **Les mesures publiées sont honnêtes** :
  - exactitude par plat, matrice de confusion, taux de refus ;
  - sur un jeu de test jamais vu, en séparant les images de laboratoire des photos
    prises dans la vie réelle quand on en a.
- L'entraînement tient dans des **carnets Jupyter** prêts à lancer sur Kaggle ou
  Colab. C'est moi qui les exécute avec mes crédits. Tu me dis exactement quoi
  cliquer, et comment récupérer le modèle produit.

## L'application Flutter

Une première version simple :
1. prendre une photo ou en choisir une dans la galerie ;
2. le plat le plus probable s'affiche, avec deux autres propositions, ou « plat non
   reconnu » ; on peut aussi choisir le plat dans la liste complète ;
3. choisir la portion ;
4. voir les calories (en fourchette) et les nutriments ;
5. un journal du jour, enregistré sur le téléphone, avec le total.

Elle fonctionne sans connexion, en français et en anglais, en thème clair et sombre.
Si tu as une idée qui dépasse ça, propose-la avant de la coder.

## Le dépôt

```
data/            # sources.yaml, scripts de téléchargement et de préparation
nutrition/       # recettes types, dishes.json, script de calcul
training/        # carnets et scripts d'entraînement, d'évaluation, d'export
app/             # application Flutter
docs/            # méthode nutritionnelle, carte du modèle, carte des données
README.md, README.fr.md, LICENSE (MIT pour le code), CONTRIBUTING.md
```

Le modèle et la description des données seront aussi publiés sur Hugging Face, avec
une page qui liste toutes les sources et leurs licences.

## Le déroulé

Chaque étape a sa branche et sa pull request :

1. **Inventaire des données** :
   - vérifier les licences ;
   - écrire `sources.yaml` et les scripts de téléchargement ;
   - faire un tableau du nombre d'images par plat ;
   - en déduire la liste des plats reconnus par le modèle.
2. **Calories** :
   - les recettes types et le calcul depuis la WAFCT 2019 ;
   - `dishes.json` pour tous les plats, y compris ceux en saisie manuelle ;
   - la page de méthode.
3. **Modèle** :
   - le carnet d'entraînement, l'évaluation et l'export TensorFlow Lite ;
   - la carte du modèle.
4. **Application** : la version simple décrite plus haut, avec ses tests.
5. **Publication** :
   - les README en anglais et en français, avec captures d'écran ;
   - la publication sur Hugging Face et la première version.

À la fin de chaque étape, fais-moi un court bilan en français :
- ce qui est fait ;
- ce qui est vérifié, et comment ;
- ce qui reste incertain ;
- ce que je dois faire de mon côté.

## Ce que je fais moi-même

- Créer les comptes Kaggle et Hugging Face, et ajouter les jetons dans les secrets
  GitHub si besoin.
- Lancer les carnets d'entraînement avec mes crédits GPU.
- Tester l'application sur mon téléphone.
- Relire la liste des plats et les recettes types. Si possible, faire valider les
  calories par un nutritionniste.

## Comment on travaille ensemble

- Écris-moi en français. Le code, les commentaires, la documentation et les commits
  sont en anglais, sauf `README.fr.md`.
- Avant chaque étape importante, dis-moi en une phrase ce que tu vas faire.
- Aucune image dont la licence n'est pas vérifiée.
- Aucune clé ni aucun jeton dans le dépôt.
- Aucun chiffre présenté comme vérifié s'il ne l'est pas.

## Hors périmètre pour l'instant

- Estimer la portion d'après la photo.
- Reconnaître plusieurs plats dans la même assiette (CamerFood10 pourrait servir
  plus tard).
- Les comptes en ligne et la synchronisation.
- Les fonctions sociales.
- Les conseils nutritionnels personnalisés.
