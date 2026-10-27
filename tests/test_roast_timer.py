import importlib.util, pathlib, sys, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("roast_timer", ROOT / "plugin/skills/cook-along/scripts/roast_timer.py")
rt = importlib.util.module_from_spec(SPEC); sys.modules["roast_timer"] = rt; SPEC.loader.exec_module(rt)


class ArithmeticTests(unittest.TestCase):
    def test_chicken(self):
        r = rt.cooking_minutes("chicken", 1.8)
        self.assertEqual(r["minutes"], 90)          # 20×3.6 + 20 = 92 → 90
        self.assertEqual((r["target_c"], r["rest_minutes"], r["fan_c"]), (75, 15, 190))
        self.assertEqual(r["defrost_hours"], 20)

    def test_turkey_bands(self):
        self.assertEqual(rt.cooking_minutes("turkey", 5)["minutes"], 170)    # 20×5 + 70
        self.assertEqual(rt.cooking_minutes("turkey", 3)["minutes"], 150)    # 20×3 + 90
        self.assertEqual(rt.cooking_minutes("turkey", 7)["minutes"], 230)    # 20×7 + 90
        self.assertEqual(rt.cooking_minutes("turkey", 6)["defrost_hours"], 72)

    def test_beef_doneness(self):
        self.assertEqual(rt.cooking_minutes("beef", 2, "rare")["minutes"], 100)     # 20×4 + 20
        self.assertEqual(rt.cooking_minutes("beef", 2, "medium")["minutes"], 125)   # 25×4 + 25
        self.assertEqual(rt.cooking_minutes("beef", 2, "well")["minutes"], 150)
        self.assertEqual(rt.cooking_minutes("beef", 2, "rare")["target_c"], 52)
        self.assertEqual(rt.cooking_minutes("beef", 2, "well")["target_c"], 70)

    def test_pork_duck_goose(self):
        self.assertEqual(rt.cooking_minutes("pork", 1.5)["minutes"], 140)   # 35×3 + 35
        self.assertEqual(rt.cooking_minutes("duck", 2)["minutes"], 90)
        self.assertEqual(rt.cooking_minutes("goose", 5)["minutes"], 180)    # 15×10 + 30

    def test_stuffed_adds_time(self):
        plain = rt.cooking_minutes("chicken", 2)["minutes"]
        stuffed = rt.cooking_minutes("chicken", 2, stuffed=True)["minutes"]
        self.assertEqual(stuffed - plain, 20)
        self.assertIn("stuffing", rt.cooking_minutes("chicken", 2, stuffed=True)["rule"])

    def test_bad_input(self):
        with self.assertRaises(ValueError):
            rt.cooking_minutes("venison", 2)
        with self.assertRaises(ValueError):
            rt.cooking_minutes("beef", 40)
        with self.assertRaises(ValueError):
            rt.parse_time("half seven")


class TimelineTests(unittest.TestCase):
    def test_serve_at(self):
        r = rt.cooking_minutes("chicken", 1.8)          # 90 min, rest 15
        tl = rt.timeline(r, "19:30")
        self.assertEqual(tl["carve"], "19:25")
        self.assertEqual(tl["out_of_oven"], "19:10")
        self.assertEqual(tl["in_oven"], "17:40")
        self.assertEqual(tl["oven_on"], "17:20")
        self.assertEqual(tl["fridge_out"], "16:40")

    def test_render_and_cli(self):
        text = rt.render(rt.cooking_minutes("lamb", 2, "medium-rare"), rt.timeline(rt.cooking_minutes("lamb", 2, "medium-rare"), "13:00"))
        self.assertIn("Lamb, 2 kg, medium-rare", text)
        self.assertIn("**13:00** Serve.", text)
        self.assertEqual(rt.main(["--meat", "pork", "--weight-kg", "1.5", "--json"]), 0)
        self.assertEqual(rt.main(["--meat", "pork", "--weight-kg", "99"]), 2)


if __name__ == "__main__":
    unittest.main()
