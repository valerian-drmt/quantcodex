"""Turn the content folders into JSON that the Astro pages read.

    problems/<id>.json    ->  src/data/problems.json
    notebooks/*.ipynb     ->  src/data/notebooks.json  (+ images in public/nb-assets/)

Run it before `astro build` (the GitHub Actions workflow does this for you):

    python3 scripts/build_content.py
"""
from __future__ import annotations

import base64
import datetime as dt
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown
from latex2mathml.converter import convert as tex_to_mathml
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

ROOT = Path(__file__).resolve().parent.parent
PROBLEMS_DIR = ROOT / "problems"
NOTEBOOKS_DIR = ROOT / "notebooks"
DATA_DIR = ROOT / "src" / "data"
ASSETS_DIR = ROOT / "public" / "nb-assets"

LEVELS = ("Easy", "Medium", "Hard")
ESCAPED_DOLLAR = "QCESCDOLLAR"
CODE_FORMATTER = HtmlFormatter(noclasses=True, nowrap=True, style="github-dark")


class ContentError(Exception):
    pass


# --------------------------------------------------------------------------- helpers

def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def strip_tags(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def render_markdown(src: str) -> str:
    """Markdown with $inline$ and $$block$$ LaTeX, rendered to HTML + MathML."""
    store: list[tuple[str, str]] = []
    src = src.replace("\\$", ESCAPED_DOLLAR)

    def keep(mode):
        def inner(m):
            store.append((m.group(1), mode))
            token = f"QCMATH{len(store) - 1}X"
            return f"\n\n{token}\n\n" if mode == "block" else token
        return inner

    src = re.sub(r"\\\[(.+?)\\\]", keep("block"), src, flags=re.S)
    src = re.sub(r"\\\((.+?)\\\)", keep("inline"), src, flags=re.S)
    src = re.sub(r"\$\$(.+?)\$\$", keep("block"), src, flags=re.S)
    # $...$ may span lines but not a blank line; a multi-line environment is shown as a block
    src = re.sub(
        r"\$((?:[^$\n]|\n(?!\s*\n))+?)\$",
        lambda m: keep("block" if "\\begin{" in m.group(1) else "inline")(m),
        src,
    )
    # LaTeX text commands outside math -> Markdown
    src = re.sub(r"(?<!`)``(?!`)([^`\n]+?)''", r"“\1”", src)  # LaTeX quotes, not ``` fences
    src = re.sub(r"\\l?dots\\?", "…", src)
    src = re.sub(r"\\textbf\{([^{}]*)\}", r"**\1**", src)
    src = re.sub(r"\\(?:emph|textit)\{([^{}]*)\}", r"*\1*", src)
    src = re.sub(r"\\texttt\{([^{}]*)\}", r"`\1`", src)
    out = markdown.markdown(src, extensions=["tables", "fenced_code", "sane_lists"])

    def math(index: int) -> str:
        tex, mode = store[index]
        tex = tex.replace(ESCAPED_DOLLAR, "\\$").strip()
        # commands latex2mathml does not know
        tex = re.sub(r"\\stackrel(?![a-zA-Z])", r"\\overset", tex)
        tex = re.sub(r"\\arg(?![a-zA-Z])", r"\\operatorname{arg}", tex)
        tex = re.sub(r"\\hline(?![a-zA-Z])", "", tex)
        tex = re.sub(r"``([^`]+?)''", r"“\1”", tex)
        tex = re.sub(r"\\xrightarrow\s*\{([^{}]*)\}", r"\\overset{\1}{\\longrightarrow}", tex)
        tex = re.sub(r"\\begin\{alignedat\}\{\d+\}", r"\\begin{align*}", tex)
        tex = re.sub(r"\\(begin|end)\{(?:aligned|alignedat|align|gathered)\}", r"\\\1{align*}", tex)
        try:
            mml = tex_to_mathml(tex, display=mode)
            for name, char in (("lfloor", "&#x230A;"), ("rfloor", "&#x230B;"), ("lceil", "&#x2308;"), ("rceil", "&#x2309;")):
                mml = mml.replace(f">\\{name}<", f">{char}<")
        except Exception as exc:  # keep the build going, show the source instead
            print(f"  ! could not render LaTeX: {tex!r} ({exc})", file=sys.stderr)
            return f"<code>{html.escape(tex)}</code>"
        mml = mml.replace(' xmlns="http://www.w3.org/1998/Math/MathML"', "")
        return f'<div class="math-block">{mml}</div>' if mode == "block" else mml

    out = re.sub(r"<p>\s*QCMATH(\d+)X\s*</p>", lambda m: math(int(m.group(1))), out)
    out = re.sub(r"QCMATH(\d+)X", lambda m: math(int(m.group(1))), out)
    return out.replace(ESCAPED_DOLLAR, "$")


def render_answer(src: str) -> str:
    """An answer written as bare LaTeX (no $ or \\[ delimiters) is shown as one display formula."""
    bare = "$" not in src.replace("\\$", "") and "\\[" not in src and "\\(" not in src
    return render_markdown(f"$${src}$$" if bare else src)


def git_date(path: Path) -> str:
    """Date of the last commit touching the file (falls back to the file's mtime)."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(path)],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        if out:
            return out
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return dt.date.fromtimestamp(path.stat().st_mtime).isoformat()


# --------------------------------------------------------------------------- problems

def build_problem(path: Path) -> dict:
    """problems/<id>.json: the file name is the id shown on the site."""
    if not path.stem.isdigit():
        raise ContentError(f"{path.name}: problem files are named <number>.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContentError(f"{path.name}: invalid JSON ({exc})") from exc
    for key in ("title", "category", "difficulty", "statement"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ContentError(f"{path.name}: needs a non-empty '{key}'")
    for key in ("hint", "answer", "explanation"):  # optional: an empty one is not shown on the page
        if not isinstance(data.setdefault(key, ""), str):
            raise ContentError(f"{path.name}: '{key}' must be text")
    if data["difficulty"] not in LEVELS:
        raise ContentError(f"{path.name}: difficulty must be one of {LEVELS}")

    statement = render_markdown(data["statement"])
    return {
        "id": int(path.stem),
        "slug": path.stem,
        "title": data["title"],
        "category": data["category"],
        "difficulty": data["difficulty"],
        "excerpt": strip_tags(statement)[:200],
        "statement": statement,
        "hint": render_markdown(data["hint"]) if data["hint"].strip() else "",
        "answer": render_answer(data["answer"]) if data["answer"].strip() else "",
        "explanation": render_markdown(data["explanation"]) if data["explanation"].strip() else "",
        "updated": git_date(path),
    }


def build_problems() -> list[dict]:
    problems = [build_problem(p) for p in PROBLEMS_DIR.glob("*.json")]
    return sorted(problems, key=lambda p: p["id"])


# --------------------------------------------------------------------------- notebooks

def render_output(output: dict, asset_dir: Path, asset_url: str, name: str) -> str | None:
    kind = output.get("output_type")
    data = output.get("data", {})
    if kind == "stream":
        return f"<pre>{html.escape(''.join(output.get('text', '')).rstrip())}</pre>"
    if kind == "error":
        return f"<pre>{html.escape(output.get('ename', '') + ': ' + output.get('evalue', ''))}</pre>"
    if "image/png" in data:
        raw = data["image/png"]
        raw = "".join(raw) if isinstance(raw, list) else raw
        asset_dir.mkdir(parents=True, exist_ok=True)
        (asset_dir / f"{name}.png").write_bytes(base64.b64decode(raw))
        return f'<img src="{asset_url}/{name}.png" alt="Output of the cell above" loading="lazy">'
    if "text/html" in data:
        frag = "".join(data["text/html"])
        frag = re.sub(r"<style.*?</style>|<script.*?</script>", "", frag, flags=re.S)
        frag = re.sub(r'\s(border|class|style)="[^"]*"', "", frag)
        return f'<div class="html">{frag}</div>'
    if "text/plain" in data:
        return f"<pre>{html.escape(''.join(data['text/plain']))}</pre>"
    return None


def build_notebook(path: Path, base_url: str) -> dict:
    nb = json.loads(path.read_text(encoding="utf-8"))
    rel = path.relative_to(NOTEBOOKS_DIR).with_suffix("")
    meta = nb.get("metadata", {}).get("quantcodex", {}) or {}
    domain = meta.get("domain") or (rel.parts[0] if len(rel.parts) > 1 else "general")
    slug = "/".join(slugify(part) for part in rel.parts)
    asset_dir = ASSETS_DIR / slug
    asset_url = f"{base_url}/nb-assets/{slug}"

    title, intro_text = rel.name.replace("_", " ").capitalize(), ""
    sections = [{"id": "introduction", "title": "Introduction", "html": []}]
    first_markdown = True

    for index, cell in enumerate(nb.get("cells", [])):
        src = "".join(cell.get("source", ""))
        if cell.get("cell_type") == "markdown":
            if first_markdown:
                first_markdown = False
                m = re.match(r"#\s+(.+)\n?", src)
                if m:
                    title, src = m.group(1).strip(), src[m.end():]
                intro_text = strip_tags(markdown.markdown(src.split("\n\n")[0])) if src.strip() else ""
            rendered = render_markdown(src)
            for piece in re.split(r"(?=<h2>)", rendered):
                head = re.match(r"<h2>(.*?)</h2>", piece, flags=re.S)
                if head:
                    name = strip_tags(head.group(1))
                    sections.append({"id": slugify(name) or f"s{len(sections)}", "title": name, "html": []})
                if piece.strip():
                    sections[-1]["html"].append(piece)
        elif cell.get("cell_type") == "code":
            number = cell.get("execution_count") or ""
            code = highlight(src, PythonLexer(), CODE_FORMATTER).rstrip("\n")
            block = [f'<div class="cell-code"><div class="bar"><span>In [{number}]</span><span>python</span></div><pre>{code}</pre></div>']
            outputs = [render_output(o, asset_dir, asset_url, f"cell{index:02d}_{k}") for k, o in enumerate(cell.get("outputs", []))]
            outputs = [o for o in outputs if o]
            block.append(f'<div class="cell-out">{"".join(outputs)}</div>')
            sections[-1]["html"].append("".join(block))

    sections = [s for s in sections if s["html"] or s["id"] != "introduction"]
    seen = set()
    for s in sections:
        while s["id"] in seen:
            s["id"] += "-2"
        seen.add(s["id"])
        s["html"] = "\n".join(s["html"])

    summary = meta.get("summary") or intro_text[:200]
    return {
        "slug": slug,
        "path": f"notebooks/{path.relative_to(NOTEBOOKS_DIR).as_posix()}",
        "title": title,
        "summary": summary,
        "domain": domain,
        "cells": len(nb.get("cells", [])),
        "updated": git_date(path),
        "sections": sections,
    }


def build_notebooks(base_url: str) -> list[dict]:
    if ASSETS_DIR.exists():
        shutil.rmtree(ASSETS_DIR)
    notebooks = [build_notebook(p, base_url) for p in sorted(NOTEBOOKS_DIR.rglob("*.ipynb")) if ".ipynb_checkpoints" not in p.parts]
    return sorted(notebooks, key=lambda n: (n["updated"], n["title"]), reverse=True)


# --------------------------------------------------------------------------- main

def main() -> int:
    base_url = "/quantcodex"  # must match `base` in astro.config.mjs
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        problems = build_problems()
        notebooks = build_notebooks(base_url)
    except ContentError as exc:
        print(f"Content error: {exc}", file=sys.stderr)
        return 1
    (DATA_DIR / "problems.json").write_text(json.dumps(problems, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA_DIR / "notebooks.json").write_text(json.dumps(notebooks, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Built {len(problems)} problems and {len(notebooks)} notebooks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
