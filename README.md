# btt-ai-radar

An AI Tech Radar — tracking trends, techniques, tools, and platforms and where
they sit on the adoption curve. Entries are authored as markdown; a Python
script builds a static, interactive site.

## How it works

```
tech-radar/*.md   →   python3 generate.py   →   docs/  (static site)
```

- **`tech-radar/`** — one markdown file per entry, organised into quadrant
  subfolders. This is what you edit. See `tech-radar/README.md` for the format.
- **`generate.py`** — reads the entries and builds the site. No third-party
  dependencies (Python 3.8+).
- **`docs/`** — the generated site (`index.html` plus a page per entry). Do not
  edit by hand; it is overwritten on each build. `docs/` is also the folder
  GitHub Pages serves from if you enable it.

## Quadrants

- **Trends** — broad AI directions and shifts.
- **Techniques** — methods, patterns, and practices.
- **Tools** — libraries, frameworks, and products.
- **Platforms** — infrastructure, services, and runtimes.

## Rings

- **Adopt** — proven; use by default where it fits.
- **Trial** — worth pursuing on projects that can absorb the risk.
- **Assess** — promising; explore with a proof of concept.
- **Watch** — keep an eye on it; too early or uncertain to invest.

## Add an entry

1. Copy `tech-radar/_TEMPLATE.md` into the right quadrant subfolder and rename
   it, e.g. `tech-radar/techniques/prompt-caching.md`.
2. Fill in the frontmatter (`name`, `quadrant`, `ring`, and optionally
   `status`, `tags`, `date`) and write the body.
3. Rebuild:

   ```bash
   python3 generate.py
   ```

4. Open `docs/index.html`.

Entries with a missing or invalid `quadrant`/`ring` are skipped with a warning,
and files whose name starts with `_` are ignored.
