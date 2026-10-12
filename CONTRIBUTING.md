# Contributing

Thank you for helping. Contributions are welcome in English or French.

## Most useful right now

1. **Recipes.** If you cook one of the dishes, check its standard recipe in
   [`nutrition/recipes.yaml`](nutrition/recipes.yaml): ingredients, grams per
   100 g of finished dish, and the low/high range of oil. Open an issue with
   your recipe and, if possible, a published source.
2. **Photos under an open licence.** Most dishes are not recognised yet
   because there are too few openly licensed photos (see the
   [data inventory](docs/data-inventory.md)). The simplest way to help is to
   upload your own photos of these dishes to
   [Wikimedia Commons](https://commons.wikimedia.org) under CC BY or CC BY-SA,
   in the dish's category. The download scripts will pick them up.
   Do not send photos copied from the web or social networks.
3. **Nutritionists.** A review of the method and the values is needed before
   the "to be validated" warning can go: see
   [`docs/nutrition-method.md`](docs/nutrition-method.md).
4. **Testing the app** on your phone with your own meals, and reporting what it
   gets wrong.

## Rules

- No image whose licence has not been checked; every source goes into
  [`data/sources.yaml`](data/sources.yaml) with its licence and credits.
- The repository contains no images: scripts download them from their source.
- No key or token in the repository; use GitHub secrets.
- No number presented as verified if it is not.
- Code, comments, documentation and commit messages in English (except
  `README.fr.md`).

## Running the checks

Each part has its own tests, also run by GitHub Actions on every pull request:

```bash
python -m pytest -q data/tests                       # data
python -m pytest -q nutrition/tests                  # nutrition
python nutrition/compute.py --check                  # dishes.json is up to date
python -m pytest -q training/tests                   # training (needs TensorFlow)
cd app && flutter analyze && flutter test            # app
```

See the README of each folder for details.
