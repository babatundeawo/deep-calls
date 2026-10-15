# Essays

**To publish an essay, put one `.md` file in this folder and commit it. That is all.** GitHub rebuilds and republishes the site by itself within about two minutes. No other file needs to change.

- The file name becomes the web address: `the-god-who-draws-in-curves.md` is published at `/writeups/the-god-who-draws-in-curves.html`. Capital letters, spaces and underscores in the name are tidied automatically.
- A details block at the top is **optional**. Without one, the title is taken from the first `# Heading`, the category is chosen from the wording, and the date is the day the file was added.
- To control the details yourself, start the file with a block between two `---` lines (title, subtitle, category, verse, verse_ref, featured, date, summary). The full list is in [docs/CUSTOMIZING.md](../docs/CUSTOMIZING.md).
- A file whose name starts with `_` (for example `_draft.md`) is ignored, so you can keep unfinished work here.
- If a file cannot be published (for example it is empty), the other essays still go live. The run in the **Actions** tab shows a yellow warning naming the file and the reason.
