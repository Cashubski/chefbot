import importlib.util, pathlib, sys, tempfile, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("bakers_percent", ROOT / "plugin/skills/baking-formulas/scripts/bakers_percent.py")
bp = importlib.util.module_from_spec(SPEC); sys.modules["bakers_percent"] = bp; SPEC.loader.exec_module(bp)


class FormulaTests(unittest.TestCase):
    def test_weights_from_flour(self):
        f = bp.formula(500, 70, 2, 1, 0, {})
        rows = {r["ingredient"]: r["grams"] for r in f["rows"]}
        self.assertEqual(rows["flour (added)"], 500)
        self.assertEqual(rows["water (added)"], 350)
        self.assertEqual(rows["salt"], 10)
        self.assertEqual(rows["instant yeast"], 5)
        self.assertAlmostEqual(f["total"], 865)

    def test_starter_splits_into_flour_and_water(self):
        f = bp.formula(500, 75, 2, 0, 20, {})
        rows = {r["ingredient"]: r["grams"] for r in f["rows"]}
        self.assertEqual(rows["starter, 100 % hydration"], 100)
        self.assertEqual(rows["flour (added)"], 450)
        self.assertEqual(rows["water (added)"], 325)   # 375 total water minus 50 in the starter
        self.assertAlmostEqual(f["total"], 450 + 325 + 100 + 10)

    def test_solve_flour_from_dough_weight(self):
        flour = bp.solve_flour(900, 65, 2, 1, 0, {})
        f = bp.formula(flour, 65, 2, 1, 0, {})
        self.assertAlmostEqual(f["total"], 900, places=6)

    def test_extras_and_notes(self):
        f = bp.formula(400, 90, 3, 3, 0, {"oil": 5})
        self.assertIn("oil", [r["ingredient"] for r in f["rows"]])
        notes = " ".join(f["notes"])
        self.assertIn("hydration 90", notes)
        self.assertIn("salt 3", notes)
        self.assertIn("yeasty", notes)


class AnalyseTests(unittest.TestCase):
    def test_hydration_and_salt(self):
        a = bp.analyse("500 g strong white flour\n350 ml water\n10 g salt\n5 g yeast\n")
        self.assertAlmostEqual(a["hydration"], 70)
        self.assertAlmostEqual(a["salt_percent"], 2)
        self.assertIn("soft", a["verdict"])

    def test_starter_counted_half_half(self):
        a = bp.analyse("450 g flour\n325 g water\n100 g sourdough starter\n10 g salt")
        self.assertAlmostEqual(a["flour_total"], 500)
        self.assertAlmostEqual(a["hydration"], 75)

    def test_no_flour_errors(self):
        with self.assertRaises(SystemExit):
            bp.analyse("2 eggs\n100 g sugar")


class RatioTests(unittest.TestCase):
    def test_pie_dough(self):
        t = bp.ratio_table("pie-dough", 600)
        grams = [r["grams"] for r in t["rows"]]
        self.assertEqual(grams, [300, 200, 100])

    def test_eggs_get_a_count(self):
        t = bp.ratio_table("pound-cake", 880)
        egg = next(r for r in t["rows"] if r["ingredient"] == "eggs")
        self.assertEqual(egg["grams"], 220)
        self.assertEqual(egg["count"], 4)

    def test_cli_errors(self):
        with self.assertRaises(SystemExit):
            bp.main(["--ratio", "pie-dough"])
        with self.assertRaises(SystemExit):
            bp.main(["--flour", "-5"])
        with self.assertRaises(SystemExit):
            bp.main(["--flour", "500", "--extra", "oil"])


if __name__ == "__main__":
    unittest.main()
