"""Tests for the recipe-scaling script. Run: python3 -m unittest discover -s tests"""
import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("scale_recipe", ROOT / "plugin/skills/recipe-scaling/scripts/scale_recipe.py")
sr = importlib.util.module_from_spec(SPEC)
sys.modules["scale_recipe"] = sr
SPEC.loader.exec_module(sr)


def scaled(line, factor, units=None):
    ing = sr.parse_line(line)
    sr.scale([ing], factor, units)
    return ing


class ParseTests(unittest.TestCase):
    def test_metric_weight(self):
        i = sr.parse_line("250 g strong white bread flour")
        self.assertEqual((i.quantity, i.unit, i.name), (250.0, "g", "strong white bread flour"))

    def test_unicode_and_mixed_fractions(self):
        self.assertEqual(sr.parse_line("1½ tsp fine salt").quantity, 1.5)
        self.assertEqual(sr.parse_line("1 ½ tsp fine salt").quantity, 1.5)
        self.assertEqual(sr.parse_line("1 1/2 cups milk").quantity, 1.5)
        self.assertEqual(sr.parse_line("¾ cup sugar").quantity, 0.75)
        self.assertEqual(sr.parse_line("0.5 kg potatoes").quantity, 0.5)

    def test_range(self):
        i = sr.parse_line("1-2 cloves garlic")
        self.assertEqual((i.quantity, i.quantity_high, i.unit), (1.0, 2.0, "clove"))

    def test_note_split(self):
        i = sr.parse_line("150 g mozzarella, grated")
        self.assertEqual((i.name, i.note), ("mozzarella", "grated"))
        i = sr.parse_line("2 onions (finely chopped)")
        self.assertEqual((i.name, i.note), ("onions", "finely chopped"))

    def test_vague(self):
        i = sr.parse_line("a pinch of nutmeg")
        self.assertEqual((i.quantity, i.unit, i.name), (1.0, "pinch", "nutmeg"))

    def test_unparsed_passthrough(self):
        i = sr.parse_line("Optional: parsley or chilli flakes")
        self.assertFalse(i.parsed)
        self.assertEqual(i.display(), "Optional: parsley or chilli flakes")


class ScaleTests(unittest.TestCase):
    def test_linear_and_rounding(self):
        self.assertEqual(scaled("250 g flour", 1.5).display(), "375 g flour")
        self.assertEqual(scaled("250 g flour", 0.25).display(), "63 g flour")   # 62.5 rounds half-up
        self.assertEqual(scaled("150 ml water", 1.5).display(), "225 ml water")
        self.assertEqual(scaled("1 tbsp oil", 1.5).display(), "1½ tbsp oil")

    def test_eggs_round_to_half_and_flag(self):
        i = scaled("2 eggs", 1.25)
        self.assertEqual(i.display(), "2½ eggs")
        self.assertTrue(any("half an egg" in f for f in i.flags))
        self.assertEqual(scaled("2 eggs", 0.5).display(), "1 egg")
        self.assertEqual(scaled("1 egg", 3).display(), "3 eggs")

    def test_seasoning_sublinear_for_large_factor(self):
        i = scaled("1 tsp fine salt", 3)
        self.assertLess(i.scaled_quantity, 3)
        self.assertTrue(any("adjust to taste" in f for f in i.flags))
        self.assertEqual(scaled("1 tsp fine salt", 2).display(), "2 tsp fine salt")

    def test_leavening_flag(self):
        self.assertTrue(any("leavening" in f for f in scaled("7 g instant yeast", 2).flags))

    def test_pinch_rounds_to_whole(self):
        self.assertEqual(scaled("a pinch of nutmeg", 1.5).display(), "2 pinches nutmeg")
        self.assertEqual(scaled("a pinch of nutmeg", 0.5).display(), "1 pinch nutmeg")

    def test_plural_units(self):
        self.assertEqual(scaled("1 clove garlic", 3).display(), "3 cloves garlic")
        self.assertEqual(scaled("1-2 cloves garlic", 2).display(), "2-4 cloves garlic")

    def test_never_rounds_to_zero(self):
        i = scaled("1 g saffron", 0.1)
        self.assertGreater(i.scaled_quantity, 0)


class ConvertTests(unittest.TestCase):
    def test_weight_exact(self):
        self.assertEqual(scaled("2 lb chicken thighs", 1, "metric").display(), "905 g chicken thighs")
        self.assertEqual(scaled("8 oz cheddar", 1, "metric").display(), "225 g cheddar")

    def test_liquid_cups_to_ml(self):
        self.assertEqual(scaled("1 cup milk", 1, "metric").display(), "240 ml milk")

    def test_dry_cups_by_density(self):
        i = scaled("1 cup all-purpose flour", 1, "metric")
        self.assertEqual(i.display(), "125 g all-purpose flour")
        self.assertTrue(any("density" in f for f in i.flags))

    def test_grams_to_cups_or_oz(self):
        self.assertEqual(scaled("200 g caster sugar", 1, "us").display(), "1 cup caster sugar")
        self.assertEqual(scaled("150 g mozzarella", 1, "us").display(), "5¼ oz mozzarella")

    def test_small_volumes_to_spoons(self):
        self.assertEqual(scaled("10 ml vanilla extract", 1, "us").display(), "2 tsp vanilla extract")
        self.assertEqual(scaled("30 ml olive oil", 1, "us").display(), "2 tbsp olive oil")


class MethodNotesTests(unittest.TestCase):
    def test_notes(self):
        self.assertEqual(sr.method_notes(1.0), [])
        notes = " ".join(sr.method_notes(2.0))
        self.assertIn("28 cm", notes)
        self.assertIn("batches", notes)
        self.assertIn("taste", " ".join(sr.method_notes(3.0)))


if __name__ == "__main__":
    unittest.main()
