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

Two reliable sources of dish labels, before any human review of the photos:

- **Wikimedia Commons categories** (open licences, 44 dishes);
- **CamerFood10** (training only): images where the dish covers the largest
  area of the segmentation mask, train + test. Its 10 classes map to 6
  catalogue dishes: taro + yellow soup → achu, fried plantain → alloco,
  water fufu → fufu, plus koki, bobolo and puff-puff. White rice, beans and
  tomato sauce are not catalogue dishes.

| Dish | Commons | CamerFood10 † | Total |
|---|---:|---:|---:|
| alloco (fried plantain) | 56 | 235 | 291 |
| fufu | 153 | 81 | 234 |
| bobolo | 18 | 196 | 214 |
| ugali | 188 | – | 188 |
| puff-puff | 29 | 133 | 162 |
| koki | 10 | 100 | 110 |
| achu | 0 | 104 | 104 |

† training only: never redistributed; models trained on it are CC BY-NC 4.0.

- **≥ 150 (model threshold)**: alloco, fufu, bobolo, ugali, puff-puff.
- **20–149 (few-shot candidates)**: jollof rice 122, injera 117, koki 110,
  achu 104, chapati 86, suya 79, kenkey 75, banku 59, pilau 57, akara 56,
  egusi soup 54, mafé 51, palm nut soup 48, thieboudienne 42, amala 29,
  matoke 29, sukuma wiki 27, waakye 26, pounded yam 24, moi moi 22.
- **< 20**: the 19 others, including ndolé 16, poulet DG 5, ekwang 1, and 0
  for eru, okok, mbongo tchobi, sanga, miondo.

Title searches on Commons find more candidates for some dishes without a
category (eru 103, attiéké 95, achu 25, ndolé +19), and Openverse finds many
keyword hits. Neither is a reliable label: they are listed as an upper bound
until someone checks the photos.

Caveats:

- **ugali** includes the Commons sub-categories Nshima, Sadza, Pap, Tuo zaafi,
  Pâte de maïs, Couscous de maïs and Corn fufu: the same stiff maize porridge
  under other names. Merging them is visually sound but makes the class
  "maize porridge" rather than strictly Kenyan ugali.
- **fufu** mixes Commons fufu (with Foutou and Akpu) and CamerFood10 water
  fufu (fermented cassava, Cameroon).
- **alloco** is fried ripe plantain: Ivorian alloco, Cameroonian plantain frit
  and Nigerian dodo look alike and are one class here.
- CamerFood10 images often show several foods; the dominant-dish rule keeps
  one label per image, and training should crop or weight by mask area.
- A few Commons files appear under two dishes (e.g. fufu with eru on one
  plate); see the table. They need one label or none.

## 3. Proposed dish list for version 1

| Group | Dishes | How the app handles them |
|---|---|---|
| Recognised by the classifier (if review keeps ≥ 150) | alloco, fufu, bobolo, ugali, puff-puff | Trained classes. |
| Few-shot test | the 20 dishes listed above | Nearest-neighbour on image embeddings (MobileCLIP / SigLIP family). Kept only if the measured accuracy is honestly good. |
| Manual entry | the 19 other dishes, and any dish that fails the few-shot test | Picked from the list, with calories. |

Options to grow the classifier, to be decided by the project owner:

1. Run the few-shot test on the 20 dishes with 20 to 149 photos, and measure
   honestly (step 3).
2. African Foods (Mendeley): the owner is contacting the authors; if they do
   not answer, it becomes training only like CamerFood10, which would add about
   200 photos each for ndolé, eru and ekwang, and 300 to 400 for jollof rice,
   palm nut soup and waakye (counts reported by the authors).
3. Collect new photos under CC BY from contributors (people photographing
   their own meals), with a simple contribution form and consent.
4. Review the Openverse and Commons-search candidates by hand: several dishes
   (injera, banku, suya, pilau, akara...) could pass 150 if enough of those
   hits are the right dish.
