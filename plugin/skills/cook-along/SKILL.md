---
name: cook-along
description: Guide the user step by step while they cook, and time several dishes so they are ready together. Use when the user says they are starting to cook, asks "what's next", wants to be walked through a recipe one step at a time, asks how long something needs or whether it is done, or wants a schedule so the roast, the vegetables and the gravy land on the table at the same time. Builds the backwards timeline with scripts/serving_schedule.py when a Python tool is available.
metadata:
  publisher: NeuralTake
  version: "0.17.0"
---

# Cook-along mode and serving-time schedules

## Step-by-step mode

1. Confirm the recipe being cooked (from the conversation or pasted) and the serving time if one matters.
2. Give **one step at a time**: the action, the heat, the time, and the sign of doneness, in two or three sentences. End with "Say *next* when you're ready" or the equivalent in the user's language.
3. Before any step with waiting time, say what can be prepared meanwhile ("while the onions soften, 8 to 10 minutes, zest the lemon and chop the parsley").
4. When the user reports a problem, answer with the rescue first (see the troubleshooting table below), then the next step.
5. On "how long" or "is it done": give the doneness cue first, the time second, and the internal temperature when safety depends on it (food-safety skill).
6. Keep the user's place: if they ask an unrelated question mid-recipe, answer it and then say which step they are on.

## Serving-time schedule

When two or more dishes must be ready together:

1. List each component with its total time, how much of that is hands-on, and anything that must finish early (resting meat, cooling a sauce) or at the last minute (dressing a salad).
2. If a Python tool is available, write the components to a JSON file and run `python3 scripts/serving_schedule.py menu.json`. Input shape:
   `{"serve_at": "19:30", "tasks": [{"name": "Roast chicken 1.8 kg", "minutes": 90, "hands_on": 10, "finish_before": 15, "note": "rest, loosely covered"}, {"name": "Roast potatoes", "minutes": 55, "hands_on": 10}, {"name": "Gravy", "minutes": 10, "hands_on": 10, "after": "Roast chicken 1.8 kg"}]}`
   The script prints a start-time timeline counted back from `serve_at`, warns where hands-on work overlaps, and adds "put the oven on" at the right moment. Present it as a numbered timeline.
3. Without a Python tool, count back from the serving time by hand and show the arithmetic for the longest item.
4. Add the oven plan: which shelf, which temperature, and what to do when two dishes need different temperatures (compromise, or stagger and keep one warm, covered, at 70°C / 60°C fan).

## Roast timer

For a single joint or bird, run `python3 scripts/roast_timer.py --meat chicken --weight-kg 1.8` (meats: chicken, turkey, beef, lamb, pork, ham, duck, goose; add `--doneness medium-rare` for beef or lamb, `--stuffed`, `--boneless`, and `--serve-at 19:30` for an oven-on to carving timeline). It gives the roasting time from the standard minutes-per-weight rules, the oven temperature for conventional and fan, the internal temperature that means done, the resting time and the fridge defrosting time. Use it when the user asks "how long for a 2 kg leg of lamb", is planning a roast dinner, or needs to know when to start a turkey. Without a Python tool, state the rule you are applying and show the arithmetic. The time is an estimate: always finish with the probe reading.

## Troubleshooting (answer with the rescue first)

| Problem | Rescue |
| --- | --- |
| Sauce split (hollandaise, mayonnaise, butter sauce) | Off the heat; whisk a spoon of warm water in a clean bowl and add the split sauce a little at a time. |
| Too salty | Dilute with unsalted liquid or more of the main ingredient; add acid or a little sugar; a raw potato does little. |
| Too spicy | Dairy, fat or sugar; add bulk; serve with rice or bread. |
| Lumpy gravy or sauce | Whisk hard, then sieve; next time slake the flour or cornflour in cold liquid first. |
| Rice burnt or stuck | Stop stirring; take off the heat, lid on, 10 minutes; serve from the top, leave the base. |
| Pasta overcooked | Drain now, rinse to stop it, dress with oil; in a bake it will be fine. |
| Meat tough | Long braise: it needs longer, not shorter. Quick cook: slice thinly across the grain; rest. |
| Cake sinking or underbaked | Return to the oven at a lower temperature; test the centre with a skewer; do not open the door for 10 minutes. |
| Caramel seized or crystallised | Add a splash of water and remelt gently without stirring; brush down the sides. |
| Dough not rising | Warmer spot, more time; check the yeast is alive in warm water with sugar; it may be too cold, not dead. |

## Output

In step mode: one step, the "meanwhile" line, the prompt for the next step. In schedule mode: the timeline from oven-on to serving, oven plan, and the last-10-minutes checklist.
