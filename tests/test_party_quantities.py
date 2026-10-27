import importlib.util, pathlib, sys, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("party_quantities", ROOT / "plugin/skills/entertaining/scripts/party_quantities.py")
pq = importlib.util.module_from_spec(SPEC); sys.modules["party_quantities"] = pq; SPEC.loader.exec_module(pq)


def row(result, dish):
    return next(r for r in result["rows"] if r["dish"] == dish)


class GuessTests(unittest.TestCase):
    def test_guesses(self):
        self.assertEqual(pq.guess_type("Roast chicken"), "whole-bird")
        self.assertEqual(pq.guess_type("Leg of lamb"), "main-bone-in")
        self.assertEqual(pq.guess_type("Beef wellington"), "main-boneless")
        self.assertEqual(pq.guess_type("Baked salmon"), "fish")
        self.assertEqual(pq.guess_type("Roast potatoes"), "potatoes")
        self.assertEqual(pq.guess_type("Green beans"), "green-veg")
        self.assertEqual(pq.guess_type("Apple pie"), "dessert")
        self.assertEqual(pq.guess_type("Chicken pie"), "main-boneless")
        self.assertEqual(pq.guess_type("Smoked salmon blinis"), "canape")
        self.assertEqual(pq.guess_type("Something unknown"), "main-boneless")

    def test_explicit_type_and_normalisation(self):
        dishes = pq.parse_menu("Lasagne | pasta_main\n- Gravy\n# comment\n\n")
        self.assertEqual([(d["type"], d["guessed"]) for d in dishes], [("pasta-main", False), ("sauce", True)])


class QuantityTests(unittest.TestCase):
    MENU = "Beef fillet | main-boneless\nRoast potatoes | potatoes\nGreen beans | green-veg\nPavlova | dessert"

    def test_adults_only_and_rounding(self):
        r = pq.compute(pq.parse_menu(self.MENU), people=10)
        self.assertEqual(row(r, "Beef fillet")["total"], 1800)          # 180 g × 10
        self.assertEqual(row(r, "Roast potatoes")["total"], 2000)       # 200 g × 10
        self.assertEqual(row(r, "Green beans")["total"], 900)
        self.assertEqual(row(r, "Pavlova")["total"], 1350)
        r7 = pq.compute(pq.parse_menu(self.MENU), people=7)
        self.assertEqual(row(r7, "Beef fillet")["total"], 1300)         # 1260 → up to 50 g
        self.assertEqual(row(r7, "Roast potatoes")["total"], 1500)      # 1400 → up to 250 g

    def test_kids_and_teens(self):
        base = pq.compute(pq.parse_menu(self.MENU), people=10)
        kids = pq.compute(pq.parse_menu(self.MENU), people=10, kids=4)
        teens = pq.compute(pq.parse_menu(self.MENU), people=10, teens=4)
        self.assertEqual(row(kids, "Beef fillet")["total"], 1450)       # 180 × (6 + 2) = 1440 → 1450
        self.assertEqual(row(teens, "Beef fillet")["total"], 2000)  # 180 × (6 + 5) = 1980 → 2000
        self.assertEqual(row(teens, "Pavlova")["total"], row(base, "Pavlova")["total"])  # dessert not boosted
        self.assertEqual(kids["adults"], 6)

    def test_buffet_reduction(self):
        small = pq.compute(pq.parse_menu(self.MENU), people=8, buffet=True)
        mid = pq.compute(pq.parse_menu(self.MENU), people=15, buffet=True)
        big = pq.compute(pq.parse_menu(self.MENU), people=30, buffet=True)
        self.assertEqual(row(small, "Beef fillet")["per_person"], 180)
        self.assertEqual(row(mid, "Beef fillet")["per_person"], 162)
        self.assertEqual(row(big, "Beef fillet")["per_person"], 144)
        self.assertIn("buffet reduction", row(big, "Beef fillet")["notes"])

    def test_shared_mains_and_starches(self):
        r = pq.compute(pq.parse_menu("Chicken curry\nDal\nRice\nNaan"), people=10)
        self.assertEqual(row(r, "Chicken curry")["per_person"], 90)     # two mains share
        self.assertEqual(row(r, "Rice")["per_person"], 75)              # single starch
        self.assertIn("shared with 1 other main dish", row(r, "Dal")["notes"])

    def test_canapes_use_hours(self):
        r = pq.compute(pq.parse_menu("Blinis | canape"), people=20, hours=2)
        self.assertEqual(row(r, "Blinis")["total"], 200)

    def test_drinks(self):
        r = pq.compute([], people=12, kids=2, teens=2)
        self.assertEqual(r["drinks"]["wine_bottles"], 6)                 # 8 adults × ½ bottle × 3h/2h → ceil(6)
        self.assertEqual(r["drinks"]["ice_kg"], 6.0)
        self.assertEqual(r["drinks"]["soft_drinks_litres"], 6.0)

    def test_empty_menu_and_clamping(self):
        r = pq.compute(pq.parse_menu(""), people=5, kids=9, teens=9)
        self.assertEqual(r["rows"], [])
        self.assertEqual((r["adults"], r["kids"], r["teens"]), (0, 5, 0))
        self.assertIn("No dishes given", pq.render(r))

    def test_render_table(self):
        text = pq.render(pq.compute(pq.parse_menu(self.MENU), people=10, kids=2))
        self.assertIn("| Beef fillet |", text)
        self.assertIn("Total to buy", text)
        self.assertIn("8 adults", text)


class CliTests(unittest.TestCase):
    def test_bad_people(self):
        with self.assertRaises(SystemExit):
            pq.main(["--people", "0"])

    def test_missing_file(self):
        self.assertEqual(pq.main(["/nonexistent/menu.txt", "--people", "4"]), 1)


if __name__ == "__main__":
    unittest.main()
