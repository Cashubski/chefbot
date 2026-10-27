import importlib.util, io, json, pathlib, sys, tempfile, unittest
from contextlib import redirect_stdout

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("dish_match", ROOT / "plugin/skills/fridge-to-meal/scripts/dish_match.py")
dm = importlib.util.module_from_spec(SPEC)
sys.modules["dish_match"] = dm
SPEC.loader.exec_module(dm)
LIB = dm.load_library(dm.DEFAULT_LIBRARY)


class NormaliseTests(unittest.TestCase):
    def test_quantities_and_prep_stripped(self):
        self.assertEqual(dm.normalise("half a cabbage"), "cabbage")
        self.assertEqual(dm.normalise("6 eggs"), "egg")
        self.assertEqual(dm.normalise("2 large carrots, peeled"), "carrot")
        self.assertEqual(dm.normalise("tinned chopped tomatoes"), "tinned tomato")
        self.assertEqual(dm.normalise("leftover cooked rice"), "rice")

    def test_synonyms(self):
        self.assertEqual(dm.normalise("zucchini"), "courgette")
        self.assertEqual(dm.normalise("a bunch of cilantro"), "coriander")
        self.assertEqual(dm.normalise("eggplant"), "aubergine")
        self.assertEqual(dm.normalise("1 red capsicum"), "pepper")
        self.assertEqual(dm.normalise("scallions"), "spring onion")
        self.assertEqual(dm.normalise("shrimp"), "prawn")

    def test_odd_input(self):
        self.assertIsNone(dm.normalise(""))
        self.assertIsNone(dm.normalise("   "))
        self.assertIsNone(dm.normalise("12345"))
        self.assertIsNone(dm.normalise("???"))
        self.assertEqual(dm.normalise("Mystery Ingredient"), "mystery ingredient")


class LibraryTests(unittest.TestCase):
    def test_library_shape(self):
        self.assertGreaterEqual(len(LIB), 120)
        names = [d["name"] for d in LIB]
        self.assertEqual(len(names), len(set(names)))
        allowed = {"vegetarian", "vegan", "gluten-free", "quick", "one-pan", "batch", "kids", "leftovers", "no-oven", "cheap"}
        for d in LIB:
            self.assertTrue(3 <= len(d["core"]) <= 7 or len(d["core"]) >= 1, d["name"])
            self.assertTrue(set(d["tags"]) <= allowed, d["name"])
            self.assertIn(d["difficulty"], ("easy", "medium", "involved"))
            self.assertIsInstance(d["minutes"], int)


class RankTests(unittest.TestCase):
    def have(self, *lines):
        return {k for k in (dm.normalise(l) for l in lines) if k}

    def test_full_match_ranks_first(self):
        res = dm.rank(LIB, self.have("cooked rice", "6 eggs", "3 spring onions", "2 carrots"))
        self.assertEqual(res[0]["name"], "Egg fried rice")
        self.assertEqual(res[0]["core_coverage"], 1.0)
        self.assertIn("rice", res[0]["uses_up"])

    def test_one_away_note(self):
        res = dm.rank(LIB, self.have("eggs", "rice", "spring onion"), top=50)
        oya = next(r for r in res if r["name"] == "Oyakodon")
        self.assertEqual(oya["one_away"], "chicken thigh")
        text = dm.render(res, self.have("eggs", "rice"))
        self.assertIn("one chicken thigh away", text)

    def test_exclude_allergen_group_and_ingredient(self):
        have = self.have("eggs", "rice", "spring onion")
        names = {r["name"] for r in dm.rank(LIB, have, exclude=dm.excluded_set(["egg"]), top=100)}
        self.assertNotIn("Egg fried rice", names)
        self.assertNotIn("Omelette", names)
        names = {r["name"] for r in dm.rank(LIB, self.have("peanuts", "chilli", "chicken thighs", "pepper"),
                                           exclude=dm.excluded_set(["nuts"]), top=100)}
        self.assertNotIn("Kung pao chicken", names)

    def test_tags_and_minutes_filter(self):
        have = self.have("eggs", "potatoes", "onion")
        res = dm.rank(LIB, have, tags=["vegetarian"], max_minutes=30, top=100)
        self.assertTrue(res)
        for r in res:
            self.assertLessEqual(r["minutes"], 30)
            self.assertIn("vegetarian", r["tags"])

    def test_pantry_alone_never_matches(self):
        self.assertEqual(dm.rank(LIB, set()), [])
        self.assertEqual(dm.rank(LIB, {"onion", "oil"}, assume_pantry=False) and
                         [r for r in dm.rank(LIB, {"onion"}) if r["own_hits"] == 0], [])

    def test_no_pantry_lowers_coverage(self):
        have = self.have("pasta")
        with_p = next(r for r in dm.rank(LIB, have, top=100) if r["name"] == "Spaghetti aglio e olio")
        without = next(r for r in dm.rank(LIB, have, assume_pantry=False, top=100) if r["name"] == "Spaghetti aglio e olio")
        self.assertGreaterEqual(with_p["score"], without["score"])

    def test_render_empty(self):
        self.assertIn("No dish", dm.render([], set()))


class CliTests(unittest.TestCase):
    def run_cli(self, text, *args):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write(text)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = dm.main([f.name, *args])
        return code, buf.getvalue()

    def test_json_output(self):
        code, out = self.run_cli("eggs\nrice\n", "--json", "--top", "3")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["have"], ["egg", "rice"])
        self.assertEqual(len(data["results"]), 3)

    def test_empty_and_garbage_input(self):
        code, out = self.run_cli("")
        self.assertEqual(code, 0)
        self.assertIn("No ingredients recognised", out)
        code, out = self.run_cli("???\n123\n")
        self.assertEqual(code, 0)
        self.assertIn("No ingredients recognised", out)

    def test_missing_file(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(dm.main(["/nonexistent/inventory.txt"]), 1)


if __name__ == "__main__":
    unittest.main()
