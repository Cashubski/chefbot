---
name: flavour-pairings
description: Suggest what goes with an ingredient and help the user improvise or invent a dish. Use when the user asks "what goes with X", wants to build a meal around one ingredient, needs seasoning or herb ideas, wants to make a plain or boring dish more interesting, is improvising without a recipe, or wants to create a new recipe. Draws classic pairings from references/pairings.md and explains the method (match or contrast; acid, salt, sweet, heat, crunch) so the user can keep improvising. For replacing an ingredient the user is missing see substitutions.
metadata:
  publisher: NeuralTake
  version: "0.17.1"
---

# Flavour pairings and improvising

## Steps

1. Pin down the **anchor**: the ingredient or the dish as it stands, how it is cooked (raw, roasted, braised), and what else is already in the pan. Pairings for raw tomato and for slow-roasted tomato differ.
2. Look the anchor up in [references/pairings.md](references/pairings.md) and pick **three to five partners** that fit what the user has and the cuisine they are leaning towards. Lead with the classic; add one less obvious.
3. Say **why** each partner works in a few words: match (sweet with sweet, earthy with earthy), contrast (fat with acid, rich with bitter), or shared aroma (basil and tomato, lamb and rosemary).
4. Turn the pairings into a **dish shape**, not just a list: "roast the squash, finish with brown butter and sage, sharpen with lemon, scatter toasted hazelnuts". One line for the method; a full recipe only on request (cooking-assistant layout).
5. For a **bland or flat dish**, run the five fixes in order and name the one that is missing: salt, acid, sweetness, heat, crunch or texture. Give the exact amount to add first ("½ tsp salt and a squeeze of lemon, then taste").
6. For a **new recipe**, build from the anchor outward: anchor, fat, aromatic, acid, herb or spice, texture, then check it against a classic combination in the cuisine table so it is coherent rather than everything at once.

## Rules

- Classics first. Novelty pairings are offered as an option, never as the only answer, and flagged as "less usual".
- Two or three dominant flavours per dish. If the user's dish already has five, the fix is to remove, not add.
- Respect what the user has; a pairing they must shop for is a second-choice suggestion.
- Keep diet and allergy constraints from the conversation (dietary-adaptation skill) when proposing partners.
- Explain the method briefly so the user learns to improvise, but do not lecture: one principle per answer.

## Output

Three to five partners with a few words on why each works, one line turning them into a dish, and for a flat dish the single fix to try first with its amount.
