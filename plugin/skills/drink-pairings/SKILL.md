---
name: drink-pairings
description: Recommend wine, beer, cider, sake, cocktails and alcohol-free drinks to go with a dish or a menu. Use when the user asks what to drink or serve with a meal, which wine goes with a recipe, for an alcohol-free pairing, or how to pair a whole menu. Reasons from acidity, sweetness, body, tannin, intensity and the dish's dominant flavours, using references/pairing-guide.md, and never claims live stock or prices.
metadata:
  publisher: NeuralTake
  version: "0.17.1"
---

# Drink pairings

## Steps

1. Identify the dish's **dominant element**: the sauce or seasoning more than the protein (chicken in a cream sauce pairs differently from chicken in a tomato sauce). Note fat, acid, sweetness, spice heat, smoke and umami.
2. Apply the principles in [references/pairing-guide.md](references/pairing-guide.md): match weight to weight, acid to acid or fat, sweet to sweeter, tannin to protein and fat, keep alcohol and oak low against chilli heat.
3. Offer **one lead pairing and two alternatives**: a wine (grape and style, with a region as an example), a beer or cider or sake if it fits better, and always one alcohol-free option that is a real pairing rather than "water".
4. Give the **reason in one sentence** per drink. No tasting-note essays.
5. For a menu, pair course by course, moving from lighter to fuller, and suggest one bottle that covers most of it if the user wants a single choice.
6. Serving: temperature and whether to open early, in a line.

## Rules

- Respect a stated preference not to drink; then lead with the alcohol-free pairing and do not mention alcohol again.
- Name styles and grapes, not vintages or specific bottles, unless the user asks; prices and availability are unknown to ChefBot, so point the user to a tool or their local shop for a current bottle.
- Alcohol-free pairings should do the same job: acidity from citrus or a sharp soft drink, tannin and bitterness from tea or tonic, sweetness from a syrup or juice, weight from texture (a thicker juice, a milky drink) and body.
- Do not pair alcohol for anyone the conversation shows is under the legal drinking age, pregnant or asking for a children's meal; give alcohol-free options.
- Keep to pairing. Health claims about alcohol are out of scope.

## Output

Lead pairing, two alternatives (one alcohol-free), each with its one-line reason, and a serving line.
