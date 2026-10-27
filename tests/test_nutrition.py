"""Tests for the nutrition-estimate script. Run: python3 -m unittest tests.test_nutrition"""
import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nutrition", ROOT / "plugin/skills/nutrition-estimate/scripts/nutrition.py")
nu = importlib.util.module_from_spec(SPEC)
sys.modules["nutrition"] = nu
SPEC.loader.exec_module(nu)
TABLE = nu.load_table()


def grams(line):
    ln = nu.parse_line(line)
    return nu.grams_for(ln)[0]


class ParseTests(unittest.TestCase):
    def test_basic_and_fractions(self):
        ln = nu.parse_line("250 g strong white bread flour")
        self.assertEqual((ln.quantity, ln.unit, ln.name), (250.0, "g", "strong white bread flour"))
        self.assertEqual(nu.parse_line("1½ tsp salt").quantity, 1.5)
        self.assertEqual(nu.parse_line("1 1/2 cups milk").quantity, 1.5)

    def test_range_uses_midpoint(self):
        self.assertEqual(nu.parse_line("1-2 cloves garlic").quantity, 1.5)

    def test_container_word_dropped(self):
        self.assertEqual(nu.parse_line("400 g tin chopped tomatoes").name, "chopped tomatoes")

    def test_skips_optional_and_handles_no_quantity(self):
        self.assertIsNone(nu.parse_line("Optional: parsley"))
        ln = nu.parse_line("salt and pepper")
        self.assertIsNone(ln.quantity)
        self.assertEqual(ln.name, "salt and pepper")


class GramsTests(unittest.TestCase):
    def test_weight_units(self):
        self.assertEqual(grams("250 g flour"), 250)
        self.assertEqual(grams("1 kg potatoes"), 1000)
        self.assertAlmostEqual(grams("8 oz cheddar"), 226.8, places=1)
        self.assertAlmostEqual(grams("1 lb beef mince"), 453.6, places=1)

    def test_volume_with_density(self):
        self.assertAlmostEqual(grams("1 tbsp olive oil"), 15 * 0.91, places=2)
        self.assertEqual(grams("250 ml milk"), 250)
        self.assertAlmostEqual(grams("1 cup plain flour"), 240 * 0.53, places=1)
        self.assertAlmostEqual(grams("1 tbsp honey"), 15 * 1.42, places=2)

    def test_counts(self):
        self.assertEqual(grams("2 eggs"), 100)
        self.assertEqual(grams("1 onion"), 150)
        self.assertEqual(grams("2 cloves garlic"), 10)
        self.assertEqual(grams("4 chicken thighs"), 480)
        self.assertEqual(grams("2 slices bread"), 80)
        self.assertEqual(grams("a pinch of salt"), 0.5)

    def test_unknown_count_assumes_100g(self):
        self.assertEqual(grams("1 dragonfruit"), 100)


class MatchTests(unittest.TestCase):
    def test_exact_and_prep_words(self):
        self.assertEqual(nu.match_name("onion, finely chopped", TABLE), "onion")
        self.assertEqual(nu.match_name("large free-range eggs", TABLE), "egg")

    def test_synonyms(self):
        self.assertEqual(nu.match_name("zucchini", TABLE), "courgette")
        self.assertEqual(nu.match_name("fresh cilantro", TABLE), "coriander")
        self.assertEqual(nu.match_name("eggplant", TABLE), "aubergine")
        self.assertEqual(nu.match_name("heavy cream", TABLE), "double cream")
        self.assertEqual(nu.match_name("all-purpose flour", TABLE), "plain flour")
        self.assertEqual(nu.match_name("ground beef", TABLE), "beef mince")
        self.assertEqual(nu.match_name("raw shrimp", TABLE), "prawns")
        self.assertEqual(nu.match_name("scallions", TABLE), "spring onion")

    def test_longest_match_wins(self):
        self.assertEqual(nu.match_name("sweet potato", TABLE), "sweet potato")
        self.assertEqual(nu.match_name("chicken thigh fillets", TABLE), "chicken thigh skinless")
        self.assertEqual(nu.match_name("tin of chopped tomatoes", TABLE), "chopped tomatoes")

    def test_no_match(self):
        self.assertIsNone(nu.match_name("unicorn horn", TABLE))
        self.assertIsNone(nu.match_name("", TABLE))


class EstimateTests(unittest.TestCase):
    def test_known_recipe_per_serving(self):
        # 200 g plain flour (682 kcal) + 2 eggs (143 kcal) + 100 g butter (717 kcal) = 1542 kcal, 2 servings
        r = nu.estimate(["200 g plain flour", "2 eggs", "100 g butter"], servings=2, table=TABLE)
        self.assertAlmostEqual(r["per_recipe"]["kcal"], 1542, places=0)
        self.assertAlmostEqual(r["per_serving"]["kcal"], 771, places=0)
        self.assertAlmostEqual(r["per_serving"]["protein_g"], (18.8 + 13 + 0.9) / 2, places=1)
        self.assertEqual(r["matched_share"], 1.0)
        self.assertTrue(any("assumed 50 g each" in a for a in r["assumptions"]))

    def test_unmatched_reported_and_share_drops(self):
        r = nu.estimate(["100 g plain flour", "100 g unicorn horn", "salt to taste"], servings=1, table=TABLE)
        self.assertEqual(r["matched_share"], 0.5)
        self.assertEqual(len(r["unmatched"]), 2)
        self.assertIn("Treat the figures as rough", nu.render(r))

    def test_render_has_table_and_estimate_label(self):
        text = nu.render(nu.estimate(["100 g oats", "250 ml whole milk"], servings=1, table=TABLE))
        self.assertTrue(text.startswith("**Estimate**"))
        self.assertIn("| Energy (kcal) |", text)
        self.assertIn("Matched 100% of the recipe weight", text)

    def test_odd_input_does_not_crash(self):
        r = nu.estimate(["", "???", "-", "1,5 l water", "½ cabbage", "1-2 tbsp", "0 g nothing", "Optional: love"], servings=3, table=TABLE)
        self.assertGreaterEqual(r["total_grams"], 1500)
        self.assertIsInstance(nu.render(r), str)
        r0 = nu.estimate([], servings=4, table=TABLE)
        self.assertEqual(r0["matched_share"], 0.0)
        self.assertIsInstance(nu.render(r0), str)

    def test_cli(self):
        import subprocess, tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("100 g oats\n250 ml whole milk\n1 banana\n")
        out = subprocess.run([sys.executable, str(ROOT / "plugin/skills/nutrition-estimate/scripts/nutrition.py"), f.name, "--servings", "1"],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("Estimate", out.stdout)
        self.assertIn("assumed 120 g each for '1 banana'", out.stdout)


if __name__ == "__main__":
    unittest.main()
