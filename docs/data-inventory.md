# Data inventory: summary and dish list

Step 1 of the [project brief](BRIEF.md). Full table:
[`data/inventory/inventory.md`](../data/inventory/inventory.md), produced by
`data/inventory.py` in the `data` CI workflow on 2026-10-12. Sources and licence
decisions: [`data/sources.yaml`](../data/sources.yaml).

## 1. Licences

None of the image datasets listed in the brief can be used as they are:

| Source | Decision | Why |
|---|---|---|
| African Foods Datasets (Mendeley) | pending | Declared CC BY 4.0, but images come mostly from Google Images, YouTube and Facebook (paper and Mendeley description). The owner is contacting the authors. |
| Nigerian Food Dataset (Mendeley) | excluded | Declared CC BY 4.0, but scraped from Bing Images. |
| CamerFood10 | **training only** (risk accepted) | "Non-commercial research purpose" only, and the paper says its images were scraped from Google Images and Bing. |
| KenyanFood13 | excluded | Instagram scrape, no licence. |
| Ethiopian dishes (Roboflow) | pending | Could not be found or opened. |
| devkyle/ghanaian-food-dataset | excluded | No licence (as the brief already said). |
| Wikimedia Commons | **used**, per file | Licence read per file; CC0 / PD / CC BY / CC BY-SA kept. |
| Openverse | **used**, per image | Same filter; counts are noisy keyword hits. |

A dataset's licence only covers what its authors own. Photos copied from search
engines or social networks stay the property of their photographers, whatever
licence the dataset declares.

**Decision (project owner, 2026-10-12):** accept that risk for training only.
Sources marked `approved_training_only` in `data/sources.yaml` (CamerFood10 now;
African Foods if its authors do not answer) are used to train and evaluate, are
never redistributed, and any model trained on them is released under
**CC BY-NC 4.0** with the sources named in the model card. Images are removed on
request. The code stays under MIT.

## 2. Images per dish

Counted from Wikimedia Commons categories (reliable dish label) on 44 dishes,
before any human review:

- **≥ 150 (model threshold)**: ugali 188, fufu 153.
- **20–149 (few-shot candidates)**: jollof rice 122, injera 117, chapati 86,
  suya 79, kenkey 75, banku 59, pilau 57, akara 56, alloco 56, egusi soup 54,
  mafé 51, palm nut soup 48, thieboudienne 42, amala 29, puff-puff 29,
  matoke 29, sukuma wiki 27, waakye 26, pounded yam 24, moi moi 22.
- **< 20**: everything else, including most Cameroonian dishes: ndolé 16,
  bobolo 18, koki 10, poulet DG 5, ekwang 1, and 0 for eru, achu, okok,
  mbongo tchobi, sanga, miondo.

Title searches on Commons find more candidates for some dishes without a
category (eru 103, attiéké 95, achu 25, ndolé +19), and Openverse finds many
keyword hits. Neither is a reliable label: they are listed as an upper bound
until someone checks the photos.

Caveats on the two dishes above 150:

- **ugali** includes the Commons sub-categories Nshima, Sadza, Pap, Tuo zaafi,
  Pâte de maïs, Couscous de maïs and Corn fufu: the same stiff maize porridge
  under other names. Merging them is visually sound but makes the class
  "maize porridge" rather than strictly Kenyan ugali.
- **fufu** includes Foutou (Côte d'Ivoire) and Akpu (cassava fufu, Nigeria).
- A few files appear under two dishes (e.g. fufu with eru on one plate); see
  the table. They need one label or none.

## 3. Proposed dish list for version 1

| Group | Dishes | How the app handles them |
|---|---|---|
| Recognised by the classifier (if review keeps ≥ 150) | ugali, fufu | Trained classes. |
| Few-shot test | the 20 dishes listed above | Nearest-neighbour on image embeddings (MobileCLIP / SigLIP family). Kept only if the measured accuracy is honestly good. |
| Manual entry | the 22 other dishes, and any dish that fails the few-shot test | Picked from the list, with calories. |

A classifier with two dishes is too thin to be useful on its own. Realistic
options to grow it, to be decided by the project owner:

1. Run the few-shot test on the ~22 dishes with 20+ Commons photos, and
   measure honestly (step 3).
2. Collect new photos under CC BY from contributors (people photographing
   their own meals), with a simple contribution form and consent. This is the
   only way to reach 150 photos for ndolé, eru, ekwang, koki or achu.
3. Ask the authors of the African Foods dataset whether they can release their
   own "Field" photos and the Creative Commons images with their original
   credits.
4. Review the Openverse and Commons-search candidates by hand: several dishes
   (injera, banku, suya, pilau, akara...) could pass 150 if enough of those
   hits are the right dish.
