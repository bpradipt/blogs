# blog

A minimal blog on GitHub Pages, styled after the [Tale](https://github.com/chesterhow/tale/) Jekyll theme. Write posts in Markdown; push to `main` and GitHub republishes automatically.

## Add a post

1. Create `_posts/YYYY-MM-DD-slug.md` (the date in the filename is the post date).
2. Add front matter:

   ```markdown
   ---
   title: "My post title"
   tags: [life, code]
   ---
   ```

3. The first paragraph becomes the excerpt shown on the home page.
4. Commit and push.

## Pages

- `/` — posts, newest first
- `/tags/` — posts grouped by tag
- `About` in the nav — links to `author.url` in `_config.yml`

## Configure

- Site title, description, and author (name + GitHub URL): `_config.yml`
- `baseurl` is `/blogs` because this is a project page (`bpradipt.github.io/blogs`)
- Look and feel: `assets/main.css`
- Layouts: `_layouts/`

## Diagrams

Mermaid diagrams are rendered to SVG locally and committed as images (so the
site stays JavaScript-free).

1. Save the mermaid source as `assets/diagrams/<name>.mmd`.
2. Run `./scripts/render-mermaid.sh assets/diagrams/<name>.mmd` — this writes
   `<name>.png` (pass a `.svg` path as the second argument if you prefer SVG).
3. Reference it in a post:

   ```markdown
   ![Caption]({{ '/assets/diagrams/<name>.png' | relative_url }})
   ```

Requires Node/npx; the first run downloads mermaid-cli and a headless Chromium.

## One-time setup

GitHub repo → **Settings → Pages** → Source = *Deploy from a branch* → `main` / `/ (root)`.

## Credits

Design and CSS from the [Tale](https://github.com/chesterhow/tale/) theme by Chester How (MIT — see `NOTICE`).
