# QuantCodex

Quant problems, research notebooks and probability games — a static site built from plain Markdown and Jupyter files.

**Live site:** https://valerian-drmt.github.io/quantcodex/

| Section | What it is | Source |
|---|---|---|
| Problems | Brainteasers and quant problems with a hint, the answer and a worked explanation | `problems/<id>.json` |
| Notebooks | Research notes rendered from Jupyter: formulas, code and outputs | `notebooks/*.ipynb` |
| Games | Probability games and game theory, modelled end to end | `games/` (coming next) |

## Adding content

You only add files and push. The GitHub Actions workflow renders them and redeploys the site.

### A problem

Create `problems/<id>.json`, where `<id>` is the next free number (`2105.json` after `2104.json`); `problems/quant_problems.xlsx` is the source sheet, its `#` column is the file number:

```json
{
  "title": "Expected Flips to HH",
  "category": "Probability",
  "difficulty": "Medium",
  "statement": "A fair coin is flipped until two heads appear in a row. What is the expected number of flips?",
  "hint": "Condition on the last flip and set up a small system of equations.",
  "answer": "$$6$$",
  "explanation": "Let $E_0$ be the expected number of flips from scratch and $E_1$ after one head..."
}
```

- The file name is the number shown on the site, the page address (`/problems/10/`) and the Previous / Next order. Numbers never need to be contiguous.
- `title`, `category`, `difficulty` and `statement` are required. `hint`, `answer` and `explanation` may be empty (`""`): the page then hides that panel. `difficulty` is `Easy`, `Medium` or `Hard`.
- The four text fields accept Markdown or LaTeX text. Math: `$...$` or `\\(...\\)` inline, `$$...$$` or `\\[...\\]` as a block. Bold: `**...**` or `\\textbf{...}`.
- An `answer` without any `$` is treated as one formula (`\\frac{144\\pi}{7}` works as is).
- JSON escaping: every LaTeX backslash is doubled (`\\sigma`, `\\frac{1}{2}`), a line break is `\n`, a blank line `\n\n`. A literal dollar sign is `\\$10`.
- The build fails with the file name if a field is missing, or the JSON is invalid.

### A notebook

Copy `notebooks/example.ipynb` (the template shown on the site as "Example notebook"), rename it, replace the content and run it.

- **Run it before committing.** The site shows the outputs saved in the file; it never executes code.
- The first `# Title` becomes the page title; every `## Heading` becomes an entry of the contents sidebar.
- The file name becomes the page address (`notebooks/heston.ipynb` → `/notebooks/heston/`).
- Domain (used by the filter) and one-line summary go in the notebook metadata (Jupyter: *Edit → Notebook metadata*):
  ```json
  "quantcodex": { "domain": "pricing", "summary": "Characteristic-function pricing and least-squares fit to a smile" }
  ```
  Without a domain the notebook is filed under `general`; without a summary the first paragraph is used.

### A game

`games/` is the storage folder for the third section. Its file format is not defined yet.

## Running locally

Requires Python 3.10+ and Node 20+.

```bash
pip install -r requirements.txt
npm install
npm run content   # problems/*.json + notebooks/*.ipynb -> src/data/*.json
npm run dev       # http://localhost:4321/quantcodex/
```

`npm run build` produces the static site in `dist/`.

## How it works

```
problems/*.json ───┐
                   ├─ scripts/build_content.py ─→ src/data/*.json ─→ Astro pages ─→ dist/ ─→ GitHub Pages
notebooks/*.ipynb ─┘    (Markdown, LaTeX → MathML,                    (src/pages)
                         code highlighting, images)
```

- `scripts/build_content.py` — renders Markdown + LaTeX (MathML, no client-side math library), highlights code, extracts notebook images to `public/nb-assets/`, and dates each file from its last commit.
- `src/pages/` — home, problem list and pages, notebook list and pages.
- `src/scripts/table.ts` — client-side search, filters, sorting and pagination for the lists.
- `src/lib/site.ts` — name, author and social links.

## Deployment

Pushing to `main` runs `.github/workflows/deploy.yml`, which builds and publishes the site. One-time setup: in the repository **Settings → Pages**, set **Source** to **GitHub Actions**.
