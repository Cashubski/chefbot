---
name: entertaining
description: Plan the menu, quantities and make-ahead schedule for a group. Use when the user is hosting a dinner party, feeding a crowd, cooking Christmas, Thanksgiving, Eid, Diwali, Passover or another festive dinner, planning a buffet, a BBQ for 20, a kids' party, a picnic or canapés, asks how much food or drink to buy for N people, what to serve for a special occasion, or what can be made ahead. Works out per-head quantities and totals with scripts/party_quantities.py where a Python tool exists, from references/portions.md. For the minute-by-minute timing of the cooking itself see cook-along.
metadata:
  publisher: NeuralTake
  version: "0.17.1"
---

# Entertaining: menus, quantities and make-ahead

## Input

- Occasion, date and time of day, number of adults, teenagers and children, whether it is a seated meal or a buffet, dietary needs across the group, budget, kitchen and oven space, how much time the host has on the day.
- Ask only for the head count and any allergies if missing; assume a seated main with two sides and a dessert otherwise, and say so.

## Steps

1. **Shape the menu around the kitchen, not the cookbook.** One oven means one roast; the rest comes from the hob, the fridge or the table at room temperature. Aim for one dish that is made days ahead, one made the day before, one that is quick on the day, and at most one that needs attention at the last minute.
2. **Balance the plate**: one rich dish, one sharp or fresh one, one starchy one; colours and textures that differ; nothing that must be eaten the second it leaves the pan unless the host wants to stand at the stove.
3. **Cover the group**: every allergy and diet gets at least one main-sized option that is clearly labelled, not just a side. Children get something plain; teenagers get more of everything.
4. **Work out the quantities.** If a Python tool is available, write the menu to a file (one dish per line, optionally `dish | type`) and run `python3 scripts/party_quantities.py menu.txt --people 12 --kids 3 --teens 2` (add `--buffet` for a buffet, `--courses starter,main,side,dessert` to change the shape, `--json` for data). Present its table. Without a Python tool, use the per-head figures in [references/portions.md](references/portions.md) and show the multiplication.
5. **Add drinks and ice** from the same table: half a bottle of wine per adult per two hours, 500 ml of soft drinks per person, 500 g of ice per person, and always one good alcohol-free option (drink-pairings skill).
6. **Write the make-ahead plan** from the table in the reference: three days ahead, the day before, the morning, the last hour. Then hand over to the cook-along skill for the serving-time schedule.

## Rules

- Quantities are raw weights before cooking unless the table says otherwise. Round up to what a shop sells.
- Buffets with many dishes need less of each: the script already applies the reduction; do not apply it twice.
- Say what each guest will actually be able to eat, by name, when there are dietary needs. "Vegetarian option available" is not enough.
- Food safety for a crowd: hot food above 63 °C or out for under two hours, cold food out for under four, and nothing reheated twice (food-safety skill).
- Never give currency totals for the shop unless the user gives prices.

## Output

The menu with one line per dish (name, ahead or on the day, who it suits), the quantities table with totals to buy, the drinks and ice line, the make-ahead plan by day, and an offer to write any recipe in full or build the serving timeline.
