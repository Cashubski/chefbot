#!/usr/bin/env python3
"""Validate the ChefBot plugin package and build the upload ZIP.

    python3 package.py            # validate, run tests, build dist/chefbot-plugin-<version>.zip
    python3 package.py --check    # validate only

Checks follow the public submission requirements (developers.openai.com/plugins/deploy/submission)
and the Agent Skills specification (agentskills.io/specification). Python 3.10+, stdlib only.
"""
from __future__ import annotations

import json
import re
import struct
import subprocess
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
PLUGIN = ROOT / "plugin"
SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
LIMITS = {"displayName": 30, "shortDescription": 30, "longDescription": 4000, "developerName": 80}
URL_FIELDS = ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL")
errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def png_size(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", data[16:24])


def check_manifests() -> dict:
    root = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
    compat = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    if root.get("$schema") != SCHEMA:
        err("plugin.json: $schema must be the Agent Plugins 1.0.0 schema URL")
    name = root.get("name", "")
    if not re.fullmatch(r"[a-z0-9]+(?:[-.][a-z0-9]+)*", name) or len(name) > 64:
        err(f"plugin.json: invalid name {name!r}")
    if not re.fullmatch(r"\d+\.\d+\.\d+", root.get("version", "")):
        err("plugin.json: version must be an explicit semantic version")
    for key in ("name", "version", "description", "author", "homepage", "keywords"):
        if root.get(key) != compat.get(key):
            err(f"manifests differ on {key!r}; keep plugin.json and .codex-plugin/plugin.json in sync")
    if len(root.get("description", "")) > 4000 or not root.get("description"):
        err("description must be 1-4000 characters")
    if len(root.get("author", {}).get("name", "")) > 120 or not root.get("author", {}).get("name"):
        err("author.name must be 1-120 characters")
    iface = root.get("extensions", {}).get("com.openai", {}).get("interface")
    if iface is None:
        err("plugin.json: extensions.com.openai.interface missing")
        return root
    if iface != compat.get("interface"):
        err("interface differs between plugin.json and .codex-plugin/plugin.json")
    for key, limit in LIMITS.items():
        value = iface.get(key, "")
        if not value or len(value) > limit:
            err(f"interface.{key}: required, at most {limit} characters (got {len(value)})")
    if not iface.get("category"):
        err("interface.category is required")
    caps = iface.get("capabilities")
    if not isinstance(caps, list) or len(caps) > 20 or any(len(c) > 120 for c in caps):
        err("interface.capabilities must be a list of at most 20 items of at most 120 characters")
    prompts = iface.get("defaultPrompt", [])
    if len(prompts) > 3 or len(set(prompts)) != len(prompts) or any(len(p) > 128 or "@" in p for p in prompts):
        err("interface.defaultPrompt: up to 3 unique prompts of at most 128 characters, no @mentions")
    for key in ("brandColor", "brandColorDark"):
        if key in iface and not re.fullmatch(r"#[0-9A-Fa-f]{6}", iface[key]):
            err(f"interface.{key} must be #RRGGBB")
    if "brandColor" in iface:
        r, g, b = (int(iface["brandColor"][i:i + 2], 16) / 255 for i in (1, 3, 5))
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
        lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
        if (1.05 / (lum + 0.05)) < 2.0:
            err("interface.brandColor needs at least 2:1 contrast against white")
    for key in URL_FIELDS:
        url = iface.get(key, "")
        if not url.startswith("https://") or len(url) > 1024 or "@" in url:
            err(f"interface.{key} must be an https URL without credentials (got {url!r})")
    for key in ("logo", "composerIcon", "logoDark", "composerIconDark"):
        if key not in iface:
            if key in ("logo", "composerIcon"):
                err(f"interface.{key} is required")
            continue
        rel = iface[key]
        if not rel.startswith("./"):
            err(f"interface.{key} path must start with ./")
        path = (PLUGIN / rel).resolve()
        if not path.is_file() or not path.is_relative_to(PLUGIN.resolve()):
            err(f"interface.{key}: file {rel} missing or outside the plugin")
            continue
        if path.stat().st_size > 5 * 1024 * 1024:
            err(f"interface.{key}: file over 5 MiB")
        size = png_size(path)
        if size is None:
            err(f"interface.{key}: {rel} is not a PNG (SVG, JPEG and WebP are also allowed but not checked here)")
        elif size[0] != size[1] or size[0] < 48 or size[0] > 4096:
            err(f"interface.{key}: icon must be square, 48 to 4096 px (got {size[0]}x{size[1]})")
    onboarding = root.get("extensions", {}).get("com.openai", {}).get("onboardingSkill")
    if onboarding and not (onboarding.startswith("./") and (PLUGIN / onboarding).is_file()):
        err(f"extensions.com.openai.onboardingSkill: {onboarding} must be a ./ path to an existing SKILL.md")
    for key in ("review", "mcpServers"):
        if key in root or key in root.get("extensions", {}).get("com.openai", {}):
            err(f"skills-only plugin must not declare {key}")
    return root


def check_skills() -> list[str]:
    skills_dir = PLUGIN / "skills"
    names = []
    for d in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        skill = d / "SKILL.md"
        if not skill.is_file():
            err(f"skills/{d.name}: SKILL.md missing")
            continue
        text = skill.read_text(encoding="utf-8")
        m = re.match(r"---\n(.*?)\n---\n", text, re.S)
        if not m:
            err(f"skills/{d.name}: SKILL.md must start with YAML frontmatter")
            continue
        fm = m.group(1)
        name = re.search(r"^name:\s*(.+)$", fm, re.M)
        desc = re.search(r"^description:\s*(.+)$", fm, re.M)
        if not name or name.group(1).strip() != d.name:
            err(f"skills/{d.name}: frontmatter name must equal the directory name")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", d.name) or len(d.name) > 64:
            err(f"skills/{d.name}: directory name must be lowercase letters, digits and single hyphens")
        if not desc or not (1 <= len(desc.group(1).strip()) <= 1024):
            err(f"skills/{d.name}: description must be 1-1024 characters")
        body_lines = text[m.end():].count("\n")
        if body_lines > 500:
            err(f"skills/{d.name}: SKILL.md body is {body_lines} lines; keep under 500")
        for ref in re.findall(r"\]\(((?:references|assets|scripts)/[^)]+)\)", text) + re.findall(r"\b(scripts/[\w./-]+\.py)\b", text):
            if not (d / ref).is_file():
                err(f"skills/{d.name}: referenced file {ref} not found")
        for script in (d / "scripts").glob("*.py") if (d / "scripts").is_dir() else []:
            r = subprocess.run([sys.executable, "-m", "py_compile", str(script)], capture_output=True, text=True)
            if r.returncode:
                err(f"{script.relative_to(PLUGIN)}: does not compile: {r.stderr.strip()}")
        names.append(d.name)
    if not names:
        err("no skills found")
    return names


def run_tests() -> None:
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests")], capture_output=True, text=True)
    if r.returncode:
        err("tests failed:\n" + r.stderr[-2000:])


def build(version: str) -> Path:
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    out = dist / f"chefbot-plugin-{version}.zip"
    with ZipFile(out, "w", ZIP_DEFLATED, strict_timestamps=False) as zf:
        for path in sorted(PLUGIN.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and not path.name.startswith("."):
                if path.is_symlink():
                    raise SystemExit(f"symlink in package: {path}")
                zf.write(path, path.relative_to(PLUGIN))
            elif path.is_file() and path.parts[-2] == ".codex-plugin":
                zf.write(path, path.relative_to(PLUGIN))
    return out


def main() -> int:
    root = check_manifests()
    skills = check_skills()
    if "--check" not in sys.argv:
        run_tests()
    if errors:
        print("Validation failed:")
        for e in errors:
            print(" -", e)
        return 1
    print(f"OK: {root['name']} {root['version']}, {len(skills)} skills: {', '.join(skills)}")
    if "--check" in sys.argv:
        return 0
    out = build(root["version"])
    with ZipFile(out) as zf:
        n = len(zf.namelist())
    print(f"Built {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KiB, {n} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
