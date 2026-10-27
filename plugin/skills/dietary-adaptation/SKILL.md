---
name: dietary-adaptation
description: Adapt any recipe for allergies, intolerances and diets. Use when the user mentions an allergy (nuts, peanuts, milk, eggs, gluten, soya, fish, shellfish, sesame and the other regulated allergens), coeliac disease, lactose intolerance, vegetarian, vegan, halal, kosher, low-FODMAP, diabetic-friendly, low-salt, low-fat, high-protein or calorie targets, pregnancy, feeding children, or asks whether a dish is "safe" for someone. Rewrites the recipe with the swaps and the checks that matter, and never promises a dish is allergen-free.
metadata:
  publisher: NeuralTake
  version: "0.17.0"
---

# Dietary adaptation

## Input

- The recipe (or a request for one) and the requirement: an allergen to exclude, a diet to follow, or a nutritional goal. If the requirement is medical (coeliac disease, a diagnosed allergy, diabetes, pregnancy) treat it as strict.

## Steps

1. **Classify the requirement**: allergy or intolerance (strict exclusion), religious or ethical diet (strict), health goal (best effort with estimates), preference (flexible). Ask one question only if the strictness is unclear ("is this a diagnosed allergy or a preference?").
2. **Scan every ingredient**, including hidden sources, using [references/allergens.md](references/allergens.md). Hidden sources are where most mistakes happen: soy sauce and most stock cubes contain wheat; Worcestershire sauce contains fish; many curry pastes contain shrimp; pesto contains nuts and cheese; oats are often cross-contaminated with gluten.
3. **Rewrite the recipe** in the house layout with each swap marked (for example "tamari instead of soy sauce (gluten-free)") and the method changed where the swap changes behaviour: gluten-free flour needs more liquid and a binder; aquafaba whips but does not set like egg; coconut milk splits if boiled hard.
4. **Add the checks** in a short "Check" block: which packaged items to read the label on, cross-contact risks in the user's kitchen (shared toaster, chopping board, fryer oil), and anything to confirm with the person who will eat it.
5. For **nutrition goals**, give estimated figures per serving from the stated quantities, labelled as estimates, and say which single change moves the number most.

## Rules

- Never write "allergen-free", "safe for coeliacs" or "nut-free". Write "contains no [allergen] in the ingredients listed; check labels on [items]".
- For a diagnosed allergy, recommend against swaps that share a risk (almond flour for a tree-nut allergy, even if the allergy named was walnut, unless the user confirms).
- Pregnancy: no raw or lightly cooked eggs unless the user's country has a safe-egg scheme they confirm (the UK Lion mark), no unpasteurised cheese, no raw or cured meat, cooked fish only; keep it to the ingredients at hand, not a lecture.
- Children under one: no honey, no added salt or sugar, no whole nuts; under five: no whole nuts, cut grapes and cherry tomatoes lengthways.
- Do not diagnose or prescribe. Apply requirements the user has from a professional and suggest they confirm anything medical with that professional.
- Vegan and vegetarian swaps must keep the dish working as food: say what changes in taste and texture and what to do about it.

## Output

The adapted recipe in the house layout with swaps marked, the "Check" block, and for goals the estimate line. Keep the original step numbers so the user can compare.
