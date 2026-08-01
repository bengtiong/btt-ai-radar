# tech-radar — source entries

Each markdown file in this folder (and its subfolders) is **one entry** on the
AI Tech Radar. The build script reads every `.md` file here, parses its
frontmatter, and generates the site in `../docs/`.

## Folder layout

Entries are organised into one subfolder per **quadrant**, but the folder is
only for your convenience — the actual quadrant comes from the `quadrant:`
field in the frontmatter, so a misplaced file still lands in the right place.

```
tech-radar/
├── _TEMPLATE.md        # copy this to start a new entry
├── trends/             # broad AI trends and directions
├── techniques/         # methods, patterns, practices
├── tools/              # libraries, frameworks, products
└── platforms/          # infrastructure, services, runtimes
```

Files whose name starts with `_` (like `_TEMPLATE.md`) are ignored by the build.

## Frontmatter fields

| Field      | Required | Values                                              |
|------------|----------|-----------------------------------------------------|
| `name`     | yes      | Display name of the technology or trend             |
| `quadrant` | yes      | `Trends` \| `Techniques` \| `Tools` \| `Platforms`  |
| `ring`     | yes      | `Adopt` \| `Trial` \| `Assess` \| `Watch`           |
| `status`   | no       | `new` \| `moved-in` \| `moved-out` \| `unchanged`   |
| `tags`     | no       | list of strings, e.g. `[llm, rag]`                  |
| `date`     | no       | last-reviewed date, `YYYY-MM-DD`                    |

## Rings — what they mean

- **Adopt** — proven; use by default where it fits.
- **Trial** — worth pursuing on real projects that can absorb the risk.
- **Assess** — promising; explore with a proof of concept.
- **Watch** — keep an eye on it; too early or too uncertain to invest.

## Adding an entry

1. Copy `_TEMPLATE.md` into the relevant quadrant subfolder and rename it
   (e.g. `techniques/retrieval-augmented-generation.md`).
2. Fill in the frontmatter and body.
3. From the repo root, run `python3 generate.py`.
4. Open `docs/index.html`.
