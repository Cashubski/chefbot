import importlib.util, pathlib, sys, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("serving_schedule", ROOT / "plugin/skills/cook-along/scripts/serving_schedule.py")
ss = importlib.util.module_from_spec(SPEC); sys.modules["serving_schedule"] = ss; SPEC.loader.exec_module(ss)

MENU = {"serve_at": "19:30", "tasks": [
    {"name": "Roast chicken", "minutes": 90, "hands_on": 10, "finish_before": 15, "oven": True},
    {"name": "Roast potatoes", "minutes": 55, "hands_on": 10, "oven": True},
    {"name": "Gravy", "minutes": 10, "after": "Roast chicken"},
    {"name": "Green beans", "minutes": 6},
]}


def t(result, name, key="start"):
    return next(r for r in result["rows"] if r["name"] == name)[key].strftime("%H:%M")


class ScheduleTests(unittest.TestCase):
    def test_backwards_from_serving_time(self):
        r = ss.schedule({**MENU, "tasks": [dict(x) for x in MENU["tasks"]]})
        self.assertEqual(t(r, "Roast chicken"), "17:45")      # ends 19:15, 15 min rest
        self.assertEqual(t(r, "Roast chicken", "end"), "19:15")
        self.assertEqual(t(r, "Roast potatoes"), "18:35")
        self.assertEqual(t(r, "Green beans"), "19:24")

    def test_after_chains_from_predecessor_end(self):
        r = ss.schedule({**MENU, "tasks": [dict(x) for x in MENU["tasks"]]})
        self.assertEqual(t(r, "Gravy"), "19:15")
        self.assertEqual(t(r, "Gravy", "end"), "19:25")

    def test_predecessor_shifted_when_follower_would_overrun(self):
        menu = {"serve_at": "19:00", "tasks": [
            {"name": "Stew", "minutes": 120, "finish_before": 0},
            {"name": "Dumplings", "minutes": 20, "after": "Stew"}]}
        r = ss.schedule(menu)
        self.assertEqual(t(r, "Stew", "end"), "18:40")
        self.assertEqual(t(r, "Dumplings", "end"), "19:00")
        self.assertTrue(any(x["shifted"] == 20 for x in r["rows"]))

    def test_oven_on_before_first_oven_task(self):
        r = ss.schedule({**MENU, "tasks": [dict(x) for x in MENU["tasks"]]})
        self.assertEqual(r["oven_on"].strftime("%H:%M"), "17:30")
        r2 = ss.schedule({"serve_at": "12:00", "tasks": [{"name": "Salad", "minutes": 10}]})
        self.assertIsNone(r2["oven_on"])

    def test_overlap_warning(self):
        r = ss.schedule({"serve_at": "20:00", "tasks": [
            {"name": "A", "minutes": 10, "hands_on": 10}, {"name": "B", "minutes": 10, "hands_on": 10}]})
        self.assertTrue(r["warnings"] and "A and B" in r["warnings"][0])

    def test_errors(self):
        with self.assertRaises(SystemExit):
            ss.schedule({"serve_at": "noon", "tasks": [{"name": "A", "minutes": 1}]})
        with self.assertRaises(SystemExit):
            ss.schedule({"serve_at": "19:00", "tasks": [{"name": "A", "minutes": 1, "after": "Nope"}]})
        with self.assertRaises(SystemExit):
            ss.schedule({"serve_at": "19:00", "tasks": []})

    def test_render_has_timeline(self):
        text = ss.render(ss.schedule({**MENU, "tasks": [dict(x) for x in MENU["tasks"]]}))
        self.assertIn("**17:30** Oven on", text)
        self.assertIn("**19:30** Serve.", text)


if __name__ == "__main__":
    unittest.main()
