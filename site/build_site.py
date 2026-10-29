#!/usr/bin/env python3
"""Build chefbot.neuraltake.com into /var/www/chefbot (or --out DIR) from the fragments in site/content.

Usage: python3 site/build_site.py [--out /var/www/chefbot]
No third-party scripts, fonts or trackers are emitted: the privacy policy promises none.
"""
from __future__ import annotations

import argparse
import html
import pathlib
import re
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
PLUGIN_URL = "https://chatgpt.com/plugins/plugin_65cf8e2b928081919e9c1544d32a79dc"
SITE = "https://chefbot.neuraltake.com"
TODAY = "2026-10-27"
VERSION = re.search(r"## (\d+\.\d+\.\d+)", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")).group(1)

CSS = """
:root{--ink:#1d2426;--muted:#5c6b70;--brand:#0f7c8a;--brand-dark:#0b5d68;--bg:#fbf8f3;--card:#ffffff;--line:#e6e0d6;--accent:#d97a2b;--bubble:#e9f4f6;--code:#f3efe8}
@media (prefers-color-scheme:dark){:root{--ink:#eef2f3;--muted:#a7b4b8;--brand:#4fc3d1;--brand-dark:#7ad6e1;--bg:#141a1c;--card:#1d2528;--line:#2c3639;--accent:#f0a05a;--bubble:#1f3338;--code:#182022}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--brand-dark)}a:hover{color:var(--brand)}
.wrap{max-width:900px;margin:0 auto;padding:0 20px}
header.site{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px 0;border-bottom:1px solid var(--line)}
header.site .logo{display:flex;align-items:center;gap:12px;text-decoration:none;color:var(--ink);font-weight:700;font-size:20px}
header.site .logo img{width:40px;height:40px;border-radius:10px}
header.site nav{display:flex;flex-wrap:wrap;gap:4px 18px}header.site nav a{text-decoration:none;color:var(--muted);font-size:15px}header.site nav a:hover{color:var(--brand)}
.hero{position:relative;padding:60px 0 36px;display:grid;grid-template-columns:1.15fr .85fr;gap:36px;align-items:center}
.hero::before{content:"";position:absolute;inset:-40px -40vw 0;background:radial-gradient(60% 70% at 70% 20%,rgba(15,124,138,.12),transparent 70%);pointer-events:none;z-index:-1}
.hero h1{font-size:44px;line-height:1.1;margin:0 0 16px;letter-spacing:-.015em}
.hero p.lead{font-size:19px;color:var(--muted);margin:0 0 24px;max-width:34em}
.hero img{width:100%;max-width:320px;border-radius:32px;box-shadow:0 24px 60px rgba(0,0,0,.2);justify-self:end}
.btn{display:inline-block;background:var(--brand);color:#fff !important;text-decoration:none;padding:13px 22px;border-radius:12px;font-weight:600}
.btn:hover{background:var(--brand-dark)}
.btn.ghost{background:transparent;color:var(--brand-dark) !important;border:1px solid var(--line);margin-left:10px}
.stats{display:flex;gap:28px;flex-wrap:wrap;margin:22px 0 0;padding:0;list-style:none;color:var(--muted);font-size:14px}
.stats b{display:block;color:var(--ink);font-size:24px;line-height:1.2}
section{padding:40px 0;border-top:1px solid var(--line)}
section h2{font-size:28px;margin:0 0 8px;letter-spacing:-.01em}section p.sub{color:var(--muted);margin:0 0 22px;max-width:40em}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px}
.card h3{margin:0 0 6px;font-size:17px}.card p{margin:0;color:var(--muted);font-size:15px}
.demo{display:grid;gap:22px}
.chat{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:18px 20px}
.chat .u{background:var(--bubble);border-radius:14px 14px 4px 14px;padding:10px 14px;margin:0 0 14px auto;max-width:85%;width:fit-content;font-size:15px}
.chat .b{font-size:15px}.chat .b p{margin:0 0 8px}.chat .b ol,.chat .b ul{margin:6px 0 8px;padding-left:22px}.chat .b li{margin:2px 0}
.chat .b table{border-collapse:collapse;font-size:14px;margin:6px 0 8px;width:100%}.chat .b td,.chat .b th{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left}
.chat .b .note{color:var(--muted);font-size:13px}
.chat .cap{color:var(--muted);font-size:13px;margin-top:10px;border-top:1px solid var(--line);padding-top:8px}
.prompts{display:grid;gap:10px}
.prompts div{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 16px;font-size:15px}
.prompts div::before{content:"→ ";color:var(--accent)}
figure{margin:18px 0 0}figure img{width:100%;border-radius:14px;border:1px solid var(--line)}
figcaption{color:var(--muted);font-size:14px;margin-top:8px}
details{border:1px solid var(--line);border-radius:12px;padding:10px 16px;margin:0 0 10px;background:var(--card)}
summary{cursor:pointer;font-weight:600}details p{margin:8px 0 4px;color:var(--muted);font-size:15px}
.legal h1{font-size:34px;margin:40px 0 6px}.legal .updated{color:var(--muted);margin:0 0 26px}
.legal h2{font-size:21px;margin:30px 0 10px}.legal h3{font-size:17px;margin:20px 0 6px}.legal p,.legal li{font-size:16px}
.legal table{border-collapse:collapse;width:100%;font-size:15px}.legal td,.legal th{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
footer{padding:30px 0 40px;border-top:1px solid var(--line);color:var(--muted);font-size:14px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px}
footer a{color:var(--muted);text-decoration:none;margin-right:16px}footer a:hover{color:var(--brand)}
@media (max-width:720px){.hero{grid-template-columns:1fr;padding-top:34px}.hero img{justify-self:start;max-width:160px;order:-1;border-radius:24px}.hero h1{font-size:33px}.btn.ghost{margin-left:0;margin-top:10px}.chat .u{max-width:100%}}
"""


def head(title: str, desc: str, path: str = "/") -> str:
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{SITE}{path}">
<link rel="icon" href="/assets/chefbot-icon.png">
<link rel="apple-touch-icon" href="/assets/chefbot-icon.png">
<link rel="stylesheet" href="/style.css">
<meta property="og:type" content="website"><meta property="og:site_name" content="ChefBot">
<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{SITE}{path}"><meta property="og:image" content="{SITE}/assets/og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0f7c8a">
</head>
<body>
<div class="wrap">
<header class="site">
  <a class="logo" href="/"><img src="/assets/chefbot-icon.png" alt="" width="40" height="40">ChefBot</a>
  <nav><a href="/#skills">What it does</a><a href="/#demo">See it work</a><a href="/changelog">Changelog</a><a href="/support">Support</a><a href="/privacy">Privacy</a><a href="/terms">Terms</a></nav>
</header>
'''


FOOT = f'''<footer>
  <div>© 2026 NeuralTake, London. ChefBot {VERSION}. ChefBot runs inside ChatGPT; ChatGPT is a product of OpenAI. ChefBot is not made or endorsed by OpenAI.</div>
  <div><a href="/support">Support</a><a href="/privacy">Privacy</a><a href="/terms">Terms</a><a href="/changelog">Changelog</a><a href="https://github.com/Cashubski/chefbot">Source</a><a href="https://neuraltake.com">NeuralTake</a></div>
</footer>
</div>
</body>
</html>
'''

SKILLS = [
    ("Fridge to meal", "List what you have, or take a photo of the fridge. ChefBot ranks more than 130 dishes by what you already have, tells you when you are one tin of tomatoes away from shakshuka, and writes the one it picks with exact quantities."),
    ("Recipe scaling", "Two to six, or six to two. Quantities round to amounts you can measure, seasoning scales sensibly, and ChefBot tells you what changes about the tin and the time."),
    ("Baking by formula", "Hydration and baker's percentages for bread and pizza, dough weights for your tin, and classic ratios for pastry, cakes, batters, custards and dressings."),
    ("Meal planning", "A week of dinners that reuse ingredients, with one shopping list merged by aisle and a separate \"check you have\" list for the cupboard."),
    ("Cook-along", "One step at a time while you cook, a roast timer with internal temperatures and resting, and a backwards timeline so everything is ready together."),
    ("Entertaining", "How much to buy for twelve, or forty. Quantities per head for every course, drinks and ice, and what to make three days, one day and one hour ahead."),
    ("Dietary adaptation", "Allergies, intolerances, vegan, coeliac, pregnancy, feeding children. Swaps are marked, hidden sources are flagged, and nothing is ever called \"allergen-free\"."),
    ("Nutrition estimates", "Calories, protein, fat, carbohydrate, fibre and salt per serving, computed from the quantities in the recipe and labelled as the estimate it is."),
    ("Substitutions and flavour pairings", "Out of buttermilk, eggs or self-raising flour? The swap, the ratio and what you will notice. Got beetroot and nothing else? What goes with it."),
    ("Drink pairings", "Wine, beer, cider, sake and a proper alcohol-free option for every dish, each with its reason in a sentence."),
    ("Food safety", "Safe internal temperatures, how long leftovers keep, defrosting and reheating, and when to throw food away. UK FSA figures with the US ones where they differ."),
    ("Any kitchen", "Air fryer, slow cooker, pressure cooker, microwave only, no oven at all: ChefBot converts the recipe and its times to what you have."),
    ("Recipe doctor", "Paste a recipe that failed, or one you found online. ChefBot checks the ratios, the order, the seasoning and the timings, then returns it fixed."),
    ("Recipe cards", "A clean one-page card to print or keep, made with the document tools in your ChatGPT conversation."),
    ("Techniques and cuisines", "Learn why a method works and what to practise it on. Explore a cuisine through its pantry, its techniques and three dishes, with traditional and adapted clearly separated."),
]

PROMPTS = [
    "Feeling adventurous in the kitchen today? Let's explore a recipe from a cuisine you've never tried before.",
    "Bored? Take a photo of your fridge and we'll make something!",
    "Have specific dietary needs? Share them with me, and I'll tailor a delicious and safe recipe just for you.",
    "Scale this lasagne from 6 to 10 and tell me what tin to use.",
    "Plan five dinners for two from one shop, nothing over 40 minutes.",
    "Roast chicken, potatoes, greens and gravy for 7.30: give me the timeline.",
    "I've got 500 g of flour: give me a 70 % hydration loaf and tell me what the 70 means.",
    "What goes with beetroot? I have goat's cheese and some walnuts.",
]

# Real outputs from the bundled scripts, lightly formatted.
DEMOS = [
    ("Half a cabbage, two carrots, six eggs, soy sauce, cold cooked rice, spring onions. What can I make?",
     """<p><strong>Egg fried rice</strong> is the obvious one, and it clears the rice, the eggs, the spring onions and a carrot. Fifteen minutes.</p>
<ol><li><strong>Egg fried rice</strong> · Chinese · 15 min · you have everything</li>
<li><strong>Congee</strong> · Chinese · 90 min · you have everything, slower</li>
<li><strong>Oyakodon</strong> · Japanese · 20 min · one chicken thigh away</li></ol>
<p class="note">Assuming oil, salt, garlic and black pepper in the cupboard. Want the fried rice written out for two, or the cabbage used first?</p>""",
     "The dish matcher ranks 132 dishes by how much of each one you already have, then ChefBot writes the recipe."),
    ("5.5 kg turkey, stuffed, we eat at 2 pm. When does it go in?",
     """<p>Into the oven at <strong>10:05</strong>. About 3 h 20 min at 180 °C / 160 °C fan, then 30 minutes' rest.</p>
<table><tr><td>09:05</td><td>Out of the fridge</td></tr><tr><td>09:45</td><td>Oven on</td></tr><tr><td>10:05</td><td>Into the oven, foil on</td></tr><tr><td>13:00</td><td>First probe check: 75 °C in the thickest part, away from the bone</td></tr><tr><td>13:25</td><td>Out to rest, loosely covered</td></tr><tr><td>13:55</td><td>Carve</td></tr><tr><td>14:00</td><td>Serve</td></tr></table>
<p class="note">Still frozen? It needs about 66 hours in the fridge. Cook the stuffing separately for a bird this size.</p>""",
     "The roast timer uses the standard per-kilogram rules, adds the resting time and counts back from when you want to eat."),
    ("Roast lamb, dauphinoise, green beans and a pavlova for twelve, three of them children. How much do I buy?",
     """<table><tr><th>Dish</th><th>Per person</th><th>Buy</th></tr>
<tr><td>Roast lamb, on the bone</td><td>300 g raw</td><td>3.15 kg</td></tr>
<tr><td>Dauphinoise potatoes</td><td>200 g raw</td><td>2.25 kg</td></tr>
<tr><td>Green beans</td><td>90 g trimmed</td><td>950 g</td></tr>
<tr><td>Pavlova</td><td>135 g finished</td><td>1.45 kg</td></tr></table>
<p class="note">Children counted at half portions. About 7 bottles of wine for nine adults over three hours, 6 litres of soft drinks and water, 6 kg of ice, and one planned alcohol-free drink. Shall I schedule the day?</p>""",
     "Quantities per head come from a fixed table, adjusted for children, teenagers and buffets, and rounded to pack sizes."),
]

FAQ = [
    ("Do I need an account with NeuralTake?", "No. ChefBot has no accounts and no server. It runs entirely inside your ChatGPT conversation, so nothing is kept between conversations by us."),
    ("What does ChatGPT need to run the scripts?", "The deterministic parts (scaling, shopping lists, schedules, roast timing, nutrition, baking formulas, dish matching) run when your conversation has a Python tool. When it does not, ChefBot follows the same rules by hand and shows its working."),
    ("Is it free?", "ChefBot itself costs nothing. Whether plugins are available on your ChatGPT plan, in your region or workspace is decided by OpenAI."),
    ("Can it see my fridge photo?", "ChatGPT reads the photo; ChefBot's instructions tell it to name only what it can see with reasonable confidence and to ask about anything unclear. NeuralTake never receives the photo."),
    ("How accurate are the nutrition numbers?", "They are computed from the quantities in your recipe against a reference table of typical values, and they are labelled estimates. ChefBot says what it assumed (an egg at 50 g, an onion at 150 g) and warns when it could not match much of the recipe."),
    ("Is it safe for allergies?", "ChefBot will adapt a recipe and flag the hidden sources of the regulated allergens, but it never calls a dish allergen-free. Read labels on packaged items and think about cross-contact in your own kitchen. For a diagnosed allergy, follow your clinician."),
    ("What happened to the ChefBot GPT?", "ChatGPT is retiring custom GPTs in favour of plugins. ChefBot continues as a plugin with the same conversation starters and a much wider set of skills. The GPT was used in more than 25,000 conversations and rated 4.7 from over 100 ratings."),
]


def index() -> str:
    jsonld = f'''<script type="application/ld+json">{{"@context":"https://schema.org","@type":"SoftwareApplication","name":"ChefBot","applicationCategory":"LifestyleApplication","operatingSystem":"ChatGPT","softwareVersion":"{VERSION}","url":"{SITE}/","installUrl":"{PLUGIN_URL}","author":{{"@type":"Organization","name":"NeuralTake","url":"https://neuraltake.com"}},"offers":{{"@type":"Offer","price":"0","priceCurrency":"GBP"}},"description":"A cooking assistant for ChatGPT: fridge photo to recipe, scaling, baking formulas, meal plans, cook-along timing, dietary adaptation, nutrition estimates, pairings and food safety."}}</script>'''
    out = [head("ChefBot: recipes from what you have", "ChefBot is a cooking assistant for ChatGPT by NeuralTake: fridge photo to recipe, scaling, baking formulas, meal plans, cook-along timing, dietary adaptation, nutrition estimates, pairings and food safety.")]
    out.append(f'''<div class="hero">
  <div>
    <h1>Turn what is in your fridge into a meal worth making.</h1>
    <p class="lead">ChefBot is a cooking assistant for ChatGPT. Show it what you have and it writes one practical recipe, then walks you through it. Eighteen skills, with real arithmetic where arithmetic matters.</p>
    <a class="btn" href="{PLUGIN_URL}">Open ChefBot in ChatGPT</a><a class="btn ghost" href="#demo">See it work</a>
    <ul class="stats"><li><b>25,000+</b>conversations as a GPT</li><li><b>4.7</b>from 100+ ratings</li><li><b>18</b>skills</li><li><b>Nothing stored</b>no accounts, no data kept</li></ul>
  </div>
  <img src="/assets/chefbot-icon.png" alt="ChefBot, a robot in a chef's hat holding a spatula" width="320" height="320">
</div>
<section id="demo">
  <h2>See it work</h2>
  <p class="sub">Three real answers, produced by the scripts bundled in the plugin. The numbers are computed, not guessed.</p>
  <div class="demo">
''')
    for q, a, cap in DEMOS:
        out.append(f'    <div class="chat"><div class="u">{html.escape(q)}</div><div class="b">{a}</div><div class="cap">{html.escape(cap)}</div></div>\n')
    out.append('  </div>\n</section>\n<section id="skills">\n  <h2>What it does</h2>\n  <p class="sub">Each skill is a focused set of instructions, with lookup tables and, where it matters, a small deterministic script.</p>\n  <div class="grid">\n')
    out += [f'    <div class="card"><h3>{html.escape(t)}</h3><p>{html.escape(d)}</p></div>\n' for t, d in SKILLS]
    out.append('  </div>\n</section>\n<section id="try">\n  <h2>Try saying</h2>\n  <div class="prompts">\n')
    out += [f'    <div>{html.escape(p)}</div>\n' for p in PROMPTS]
    out.append('''  </div>
  <figure><img src="/assets/conversation.png" alt="A ChefBot conversation: the user asks for a recipe from a cuisine they have never tried, and ChefBot answers with Adjarian khachapuri, Georgian cheese bread, with quantities and a numbered method" loading="lazy" width="2000" height="945"><figcaption>ChefBot answering the first conversation starter with a recipe in its house layout: servings, time, exact quantities, oven temperatures for fan and conventional ovens.</figcaption></figure>
</section>
<section id="how">
  <h2>How it works</h2>
  <p class="sub">And what it deliberately does not do.</p>
  <p>ChefBot is a set of eighteen skills for ChatGPT: written instructions, lookup tables (allergens and their hidden sources, substitutions with ratios, safe temperatures and storage times, pairings, techniques, equipment conversions) and seven small scripts for the parts of cooking that should not be left to a language model's arithmetic: scaling, baking formulas, nutrition estimates, shopping lists, roast timing, party quantities and serving-time schedules. Every script has unit tests.</p>
  <p>It has no server, no accounts and no database. Your conversation stays in ChatGPT and is handled under <a href="https://openai.com/policies/">OpenAI's policies</a>; NeuralTake never receives it. Details are in the <a href="/privacy">privacy policy</a>.</p>
</section>
<section id="faq">
  <h2>Questions</h2>
''')
    out += [f'  <details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>\n' for q, a in FAQ]
    out.append('</section>\n')
    out.append(jsonld + "\n" + FOOT)
    return "".join(out)


def changelog() -> str:
    md = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    body = []
    in_list = False
    for line in md.splitlines():
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            if in_list:
                body.append("</ul>"); in_list = False
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            if not in_list:
                body.append("<ul>"); in_list = True
            text = html.escape(line[2:])
            text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
            body.append(f"<li>{text}</li>")
        elif line.strip():
            if in_list:
                body.append("</ul>"); in_list = False
            body.append(f"<p>{html.escape(line)}</p>")
    if in_list:
        body.append("</ul>")
    return head("ChefBot changelog", "What changed in each ChefBot release.", "/changelog") + '<article class="legal"><h1>Changelog</h1><p class="updated">Current version ' + VERSION + '.</p>' + "\n".join(body) + "</article>\n" + FOOT


def wrap(name: str, title: str, desc: str) -> str:
    frag = (HERE / "content" / f"{name}.html").read_text(encoding="utf-8")
    frag = frag.replace("https://chatgpt.com/g/g-FJXCOCAri-chefbot-gpt", PLUGIN_URL)
    return head(title, desc, f"/{name}") + frag + FOOT


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="/var/www/chefbot")
    a = ap.parse_args(argv)
    out = pathlib.Path(a.out)
    (out / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "plugin/assets/chefbot-icon.png", out / "assets/chefbot-icon.png")
    shutil.copy(HERE / "assets/conversation.png", out / "assets/conversation.png")
    shutil.copy(HERE / "assets/og.png", out / "assets/og.png")
    (out / "style.css").write_text(CSS.strip() + "\n", encoding="utf-8")
    (out / "index.html").write_text(index(), encoding="utf-8")
    (out / "changelog.html").write_text(changelog(), encoding="utf-8")
    (out / "support.html").write_text(wrap("support", "ChefBot support", "Help with ChefBot, the cooking assistant for ChatGPT: how to open it, common questions, how to report a problem, and how to contact NeuralTake."), encoding="utf-8")
    (out / "privacy.html").write_text(wrap("privacy", "ChefBot privacy policy", "How ChefBot, the cooking assistant for ChatGPT by NeuralTake, handles personal data: no accounts, no storage, conversations processed by OpenAI, minimal website logs."), encoding="utf-8")
    (out / "terms.html").write_text(wrap("terms", "ChefBot terms of service", "Terms for using ChefBot, the cooking assistant for ChatGPT by NeuralTake: what it is, what it is not, food-safety and allergy responsibility, intellectual property and liability."), encoding="utf-8")
    (out / "404.html").write_text(head("Page not found", "ChefBot", "/404") + '<article class="legal"><h1>Page not found</h1><p>Try the <a href="/">ChefBot home page</a>, <a href="/support">support</a>, <a href="/privacy">privacy</a> or <a href="/terms">terms</a>.</p></article>' + FOOT, encoding="utf-8")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    pages = ("", "support", "privacy", "terms", "changelog")
    (out / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{SITE}/{p}</loc><lastmod>{TODAY}</lastmod></url>\n" for p in pages) + "</urlset>\n")
    print(f"built {out} (ChefBot {VERSION})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
