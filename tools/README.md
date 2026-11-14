# Tools

`checkfile.py` checks one essay against the house rules: no dashes or hyphens in the body, banned phrases, spelling and structure checks, and frontmatter values. It calls `lint.py` in this folder.

```
python3 -I tools/checkfile.py content/two_rooms_one_shepherd.md
```

Fix every FAILED line and answer every REVIEW line before an essay is published. The site checks (`python3 scripts/check.py`) are separate and cover pages, links and metadata.
