import sys, re, pathlib, statistics

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8").replace("’", "'")
body, sep, refs = text.partition("\n## References")

DASHES = "-‐‑‒–—―−﹘﹣－"
FLAGS = "ẹẸọỌṣṢịỊụỤṇ̇"

BANNED = [
    "delve", "it is important to note", "it is important to understand",
    "it is worth noting", "in conclusion", "furthermore", "moreover",
    "additionally", "tapestry", "testament to", "in today's",
    "navigating the complexities", "at the end of the day", "as we can see",
    "game changer", "let's unpack", "let us unpack", "here's the thing",
    "in a world where", "since the dawn of", "throughout history",
    "in an age of", "in a very real sense", "at its core", "shed light",
    "let us be clear", "dive into",
]

REVIEW_WORDS = [
    "journey", "landscape", "navigate", "navigating", "profound", "nuanced",
    "ultimately", "resonate", "multifaceted", "a reminder that", "stunning",
    "devastating", "deeply",
]

CONTRAST = [
    r"\bnot (just|only|merely|simply)\b[^.?!]{0,80}\bbut\b",
    r"\b(it|this|that) (is|was|isn't|wasn't) not\b[^.?!]{0,80}[.;,:]\s*(it|this|that) (is|was)\b",
    r"\b(it|this|that)'s not\b[^.?!]{0,80}[.;,:]\s*(it|this|that)'s\b",
    r"\bisn't (just |only |merely )?(about|a|an)\b[^.?!]{0,80}[.;,:]\s*(it's|it is)\b",
]

issues, review = [], []

for n, line in enumerate(body.splitlines(), 1):
    if line.startswith("> — "):
        continue
    if any(c in DASHES for c in line):
        issues.append(f"DASH in body, line {n}: {line[:80]}")
    if any(c in FLAGS for c in line):
        issues.append(f"POSSIBLE INDIGENOUS LANGUAGE, line {n}: {line[:80]}")

low = body.lower()
for phrase in BANNED:
    if phrase in low:
        issues.append(f"BANNED PHRASE: {phrase}")

for n, line in enumerate(refs.splitlines(), 1):
    if "—" in line:
        issues.append(f"EM DASH in References, line {n}: {line[:80]}")

prose = [l.strip() for l in body.splitlines()
         if l.strip() and not l.lstrip().startswith(("#", ">", "*", "`"))]
joined = " ".join(prose)
plow = joined.lower()
word_re = r"[A-Za-z']+"
pw = max(len(re.findall(word_re, joined)), 1)
sentences = [s for p in prose for s in re.split(r"(?<=[.!?])\s+", p) if s]

HEADING_BANNED = [
    r"everyone (quotes|knows|cites)",
    r"(almost )?(nobody|no one) (finishes|reads|completes|quotes)",
    r"never (finish|complete|read)",
    r"(half|unfinished|incomplete) (verse|passage|quote)",
]
for n, line in enumerate(body.splitlines(), 1):
    if line.startswith("#"):
        h = line.lstrip("#").strip()
        if any(re.search(p, h.lower()) for p in HEADING_BANNED):
            issues.append(f"HEADING uses the banned half read passage device, line {n}: {h}")
        if len(h.split()) > 10:
            review.append(f"Heading too long, line {n}: {h}")
        if ":" in h or "?" in h:
            review.append(f"Heading has a colon or question mark; write it as a plain phrase, line {n}: {h}")
if re.search(r"(everyone|many|most)( of us)? (quote|quotes|know|cite)[^.?!]{0,60}(nobody|no one|few|rarely|hardly)[^.?!]{0,40}(finish|read|complete)", plow):
    review.append("Possible half read passage device in the prose: cut it or fold it into one sentence")

for w in REVIEW_WORDS:
    c = plow.count(w)
    if c:
        review.append(f"'{w}' appears {c} time(s): earn it or replace it")

hits = sum(len(re.findall(p, plow)) for p in CONTRAST)
if hits > 1:
    issues.append(f"CONTRAST FORMULA ('not X but Y' and cousins) used {hits} times; limit is one")

run = 0
for s in sentences:
    run = run + 1 if s.endswith("?") else 0
    if run >= 3:
        issues.append("THREE RHETORICAL QUESTIONS IN A ROW")
        break
if joined.count("?") > 5:
    review.append(f"{joined.count('?')} question marks in the prose: too many questions?")

lengths = [len(re.findall(word_re, s)) for s in sentences]
if len(lengths) >= 20 and statistics.pstdev(lengths) < 7:
    review.append("Sentence lengths are too even: mix long and short")
plen = [len(re.findall(word_re, p)) for p in prose]
if len(plen) >= 8 and statistics.pstdev(plen) / statistics.mean(plen) < 0.35:
    review.append("Paragraph lengths are too even: let some run long and some stand alone")

colons = sum(p.count(":") - len(re.findall(r"\d+:\d+", p)) for p in prose)
semis = joined.count(";")
if colons > max(5, pw / 300):
    review.append(f"{colons} colons in the prose: rebuild some sentences")
if semis > 4:
    review.append(f"{semis} semicolons in the prose: rebuild some sentences")

contractions = len(re.findall(
    r"\b\w+n't\b|\b\w+'(re|ve|ll|d|m)\b|\b(it|that|there|here|what|who|he|she|let)'s\b", plow))
if pw > 800 and contractions < pw / 400:
    review.append(f"Only {contractions} contractions in {pw} words: does it sound spoken?")

words = len(re.findall(word_re, body))
print(f"Body word count: {words}")
if review:
    print("REVIEW (fix each, or keep it knowingly):")
    print("\n".join(review))
if issues:
    print("FAILED:")
    print("\n".join(issues))
    sys.exit(1)
print("PASSED: no dashes, no banned phrases, no flagged characters.")
