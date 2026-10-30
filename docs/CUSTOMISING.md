# Customising guide

All edits can be made in the GitHub web editor (the pencil icon on any file).

## Essays

Each file in `content/` starts with a block between `---` lines:

```text
---
title: Your essay title
subtitle: One line shown under the title (optional)
category: Hard Questions
verse: For God so loved the world
verse_ref: John 3:16
featured: 2
date: 2026-10-01
summary: A one or two sentence description for search results (optional)
---

Your essay text in Markdown.
```

* Every line is optional. With no block at all, the first `# Heading` becomes the title, the category is guessed from the wording (`category_keywords` in `site.config.json`, falling back to `default_category`), and the date is the day the file was added (turn off with `"auto_date": false`).
* `category` should match a name in `site.config.json`. A new name is added automatically. Set it yourself when you want to be sure: the automatic guess is only a best effort.
* `featured` (1 to 6) places an essay in the home page's featured list. Leave it out otherwise.
* `date` is optional. Use `YYYY-MM-DD`; it helps search engines.
* Use `##` for section headings, and a line starting `— John 3:16` after a quote for a citation.

## Names, address and categories

Edit `site.config.json`: site name, tagline, address (`url`), contact email, GitHub link, and the category list (its order is the order shown). Set `author` to your name to include it in search engine data.

## Colours and fonts

Open `assets/css/01-tokens.css`. Colours, sizes and spacing are named values at the top; change them there and every page follows, in light and dark themes.

## Wording on pages

Home, About and Contact text is in `scripts/templates.py`, in plain sentences you can edit.

## Logo and images

The logo and social cards are drawn by `scripts/images.py` from the site name and colours. To change the look, edit the colours in `01-tokens.css` and the colour values near the top of `scripts/images.py`.
