---
name: equipment-adaptation
description: Convert a recipe to the equipment the user actually has. Use when the user mentions an air fryer, slow cooker, pressure cooker or Instant Pot, microwave only, no oven, hob only, induction, a barbecue, a halogen or combi oven, a tiny or student kitchen, camping, a caravan or a single hotplate, or asks "can I make this in the …", or how to convert times and temperatures between appliances. Gives the converted method with the numbers from references/conversions.md and says what will differ in the result.
metadata:
  publisher: NeuralTake
  version: "0.17.0"
---

# Equipment adaptation

## Steps

1. Establish the **source method** (what the recipe assumes: oven at 200 °C, a hob simmer, a grill) and the **target** (what the user has, including its size: a 3.5 litre air fryer drawer or a 6 litre pressure cooker changes the batch).
2. Classify the cooking that is going on: dry heat and browning (roast, bake, grill), wet heat (braise, stew, boil, steam), or set-and-rise (cakes, bread, custards). The class decides whether a conversion is faithful, approximate or not sensible.
3. Apply the conversion rules in [references/conversions.md](references/conversions.md): the temperature and time adjustments, liquid changes, batch limits, release method for pressure cooking, what to add at the end.
4. Rewrite the **method only where it changes**. Keep the user's ingredient list and step order; mark each changed step so they can see what moved.
5. Give the **doneness cue and internal temperature** for the new method, because the old timing no longer applies (food-safety skill for the figures).
6. State in one line **what will differ**: no crust from a slow cooker, less browning in a microwave, a drier surface from an air fryer, a stronger smoke taste from a barbecue.
7. If the conversion is a poor fit (soufflé in a slow cooker, a large joint in a small air fryer), say so and offer the nearest dish that works in that appliance.

## Rules

- Times in the reference are starting points. Appliances vary by hundreds of watts; always pair a time with a cue and say "check at the earlier end".
- Air fryer: single layer, oil lightly, shake or turn halfway, no wet batter, no loose parchment. Reduce the stated oven temperature by 15 to 20 °C and the time by about 20 percent.
- Slow cooker: brown first where the recipe browns; reduce liquid by about a third; dairy, pasta, rice and tender vegetables go in for the last 30 to 60 minutes; do not lift the lid.
- Pressure cooker: never fill above two thirds (half for pulses and grains that foam); at least 250 ml liquid; natural release for meat, beans and anything that foams, quick release for vegetables and fish; account for the 10 to 15 minutes to reach pressure.
- Microwave: covered, vented, stirred or turned halfway, standing time counted in; metal, sealed shells and eggs in shells are out.
- Induction and small kitchens: stress heavy flat-based pans, one-pot and sheet-pan structures, and staggering rather than simultaneous cooking.
- Camping and single hotplate: one pan, no oven; say what to prepare at home.

## Output

The converted method with changed steps marked, the appliance settings (temperature, time, pressure, release), the doneness cue, the one-line "what will differ", and the batch note if the appliance is small.
