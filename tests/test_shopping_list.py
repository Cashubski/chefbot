import importlib.util, json, pathlib, sys, tempfile, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("shopping_list", ROOT / "plugin/skills/meal-planning/scripts/shopping_list.py")
sl = importlib.util.module_from_spec(SPEC); sys.modules["shopping_list"] = sl; SPEC.loader.exec_module(sl)


class CanonicalNameTests(unittest.TestCase):
    def test_strips_prep_and_singularises(self):
        self.assertEqual(sl.canonical_name("onions, finely chopped"), "onion")
        self.assertEqual(sl.canonical_name("large ripe tomatoes"), "tomato")
        self.assertEqual(sl.canonical_name("cherries"), "cherry")

    def test_keeps_compounds(self):
        self.assertEqual(sl.canonical_name("spring onions, sliced"), "spring onion")
        self.assertEqual(sl.canonical_name("extra virgin olive oil"), "olive oil")
        self.assertEqual(sl.canonical_name("self-raising flour"), "self-raising flour")


class MergeTests(unittest.TestCase):
    def setUp(self):
        self.recipes = [
            {"name": "A", "ingredients": ["2 cloves garlic", "1 lemon", "150 g spinach", "1 tbsp olive oil", "2 eggs"]},
            {"name": "B", "ingredients": ["1 clove garlic, crushed", "2 lemons", "250 g spinach", "2 tsp olive oil", "4 eggs", "Optional: chilli"]},
        ]

    def test_sums_same_units_and_converts_spoons(self):
        by = sl.merge(self.recipes)
        veg = {i["name"]: i for i in by["Fruit and vegetables"]}
        self.assertEqual(veg["garlic"]["amounts"]["clove"], 3)
        self.assertEqual(veg["lemon"]["amounts"]["whole"], 3)
        self.assertEqual(veg["spinach"]["amounts"]["g"], 400)
        oil = {i["name"]: i for i in by["Tins, jars and sauces"]}["olive oil"]
        self.assertEqual(oil["amounts"]["ml"], 25)
        self.assertEqual(sorted(oil["used_in"]), ["A", "B"])

    def test_have_removes_items(self):
        by = sl.merge(self.recipes, have={"olive oil"})
        self.assertNotIn("Tins, jars and sauces", by)

    def test_optional_lines_skipped_and_render(self):
        text = sl.render(sl.merge(self.recipes))
        self.assertNotIn("chilli", text)
        self.assertIn("- eggs: 6", text)
        self.assertIn("- lemons: 3", text)
        self.assertIn("- garlic: 3 cloves", text)

    def test_text_loader(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("# Soup\n1 onion\n500 ml stock\n# Salad\n1 onion\n")
        recipes = sl.load(f.name)
        self.assertEqual([r["name"] for r in recipes], ["Soup", "Salad"])
        by = sl.merge(recipes)
        self.assertEqual({i["name"]: i for i in by["Fruit and vegetables"]}["onion"]["amounts"]["whole"], 2)

    def test_kg_and_litre_rendering(self):
        by = sl.merge([{"name": "X", "ingredients": ["1 kg potatoes", "500 g potatoes", "1 l milk", "250 ml milk"]}])
        text = sl.render(by)
        self.assertIn("potato: 1.5 kg", text)
        self.assertIn("milk: 1.25 l", text)


if __name__ == "__main__":
    unittest.main()
