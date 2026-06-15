#!/usr/bin/env python3
#
# Copyright (c) 2026 Steve Bertrand
# This file is free software; you can redistribute it and/or modify it
# under the terms of the Artistic License 2.0:
# https://www.perlfoundation.org/artistic-license-20.html
#
"""Build a redacted, self-contained **GitHub-flavored Markdown** bundle from the
canonical AI/README.md in the config repo.

This is the Markdown sibling of config/AI/tools/build-readme-bundle-redacted.py
(which targets HTML/PDF). The difference that matters for GitHub:

  * The HTML build anchors its appendix with raw <a id="..."> tags. GitHub's
    Markdown renderer STRIPS id attributes, so those anchors are dead on GitHub.
  * Here, every relative link is rewired to the appendix heading's *natural*
    GitHub slug (computed exactly like GitHub does), and the appendix headings
    carry no manual anchors — so every TOC and cross-reference link resolves
    when rendered on GitHub.

The source repo is READ-ONLY here. Nothing is written outside this docs repo.

Run:    python3 AI/tools/build-standalone-md.py
Source: ~/repos/config/AI/README.md  (+ the files it links)
Output: AI/README-standalone-redacted.md
"""
import re
import sys
from pathlib import Path

# Canonical source (read-only) and our output (in this docs repo).
SRC_AI = Path.home() / "repos" / "config" / "AI"
README = SRC_AI / "README.md"
OUT = Path(__file__).resolve().parent.parent / "README-standalone-redacted.md"

# Relative paths exactly as written in README.md, in curated reading order,
# each with the fenced-code language used to embed it verbatim.
FILES = [
    ("settings.json", "json"),
    ("rules/git.md", "markdown"),
    ("rules/perl.md", "markdown"),
    ("rules/dev-guardrail.md", "markdown"),
    ("skills/create-plan.md", "markdown"),
    ("skills/implement-from-instruction-file.md", "markdown"),
    ("skills/remote-code-sync.md", "markdown"),
    ("skills/debate.md", "markdown"),
    ("hooks/inject-perl-rules.sh", "bash"),
    ("hooks/inject-on-phrase.sh", "bash"),
    ("hooks/guard-dev-env.sh", "bash"),
    ("context/recommend.md", "markdown"),
]

# Identifier masking — copied verbatim from the HTML build so the two bundles
# redact identically. Ordered most-specific (and longest) first.
REDACTIONS = [
    ("$Teamr::Config::GRENV", "$<COMPANY>::Config::<COMPANY_ENV>"),
    ("Teamr::Config::GRENV", "<COMPANY>::Config::<COMPANY_ENV>"),
    ("Teamr::powerconnect", "<COMPANY>::powerconnect"),
    ("use Teamr;", "use <COMPANY>;"),
    ("GreenRope/STGI/Teamr", "<COMPANY>"),
    ("`greenrope.com`, `stgi.net`, `stgi.cc`, or `teamr.com`", "`<company-host>`"),
    ("`greenrope.com`, `stgi.net`, `stgi.cc`, `teamr.com`", "`<company-host>`"),
    ("greenrope.com / stgi.net / stgi.cc / teamr.com", "<company-host>"),
    ("greenrope.com", "<company-host>"),
    ("stgi.net", "<company-host>"),
    ("stgi.cc", "<company-host>"),
    ("teamr.com", "<company-host>"),
    ("GRENV", "<COMPANY_ENV>"),
    ("devsql", "<dev-db>"),
    ("DEV_ENV", "<DEV_FLAG>"),
    ("GreenRope", "<COMPANY>"),
    ("Teamr", "<COMPANY>"),
    ("STGI", "<COMPANY>"),
]

LEAK_RE = re.compile(r"(?i)greenrope|stgi|teamr|devsql|grenv|DEV_ENV")
PROTECTED = ["stevieb9", "steveb"]


def redact(s):
    before = {p: s.count(p) for p in PROTECTED}
    for old, new in REDACTIONS:
        s = s.replace(old, new)
    after = {p: s.count(p) for p in PROTECTED}
    clobbered = sorted(p for p in PROTECTED if after[p] < before[p])
    if clobbered:
        sys.exit("REDACTION clobbered protected identifiers: " + ", ".join(clobbered))
    return s


def gh_slug(text):
    """GitHub's heading-anchor algorithm: lowercase, drop everything that is not
    a letter, number, underscore, space or hyphen, then spaces -> hyphens."""
    s = text.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    return s.replace(" ", "-")


def tilde_fence(content):
    """A tilde fence longer than any tilde run inside content, so embedded
    ```-fenced blocks can't break out (GitHub supports ~~~ fences)."""
    runs = [len(m.group(0)) for m in re.finditer(r"~+", content)]
    return "~" * max([4] + [r + 1 for r in runs])


text = README.read_text()

# 1. Rewire relative links -> the appendix heading's natural GitHub slug.
#    The appendix heading for each file is "### {relpath}", whose slug is
#    gh_slug(relpath). This is what makes links work on GitHub.
missing = []
for relpath, _ in FILES:
    token = f"]({relpath})"
    if token not in text:
        missing.append(relpath)
    text = text.replace(token, f"](#{gh_slug(relpath)})")

leftover = re.findall(r"\]\((?!#|https?:)[^)]+\)", text)

# 2. Add the Appendix entry to the existing (nested) Contents list.
toc_tail = "- [Backing up Claude](#backing-up-claude)"
if toc_tail in text:
    text = text.replace(
        toc_tail,
        toc_tail + "\n- [Appendix: bundled resource files](#appendix-bundled-resource-files)",
        1,
    )

# 3. Visible redaction note under the title.
note = (
    "> **Redacted for public sharing.** Employer-specific identifiers have been "
    "masked: production-adjacent hostnames as `<company-host>`, the internal Perl "
    "package as `<COMPANY>`, its env symbol as `<COMPANY_ENV>`, the dev-DB hostname "
    "prefix as `<dev-db>`, and the dev-env flag as `<DEV_FLAG>`. Everything else is "
    "verbatim.\n"
)
text = text.replace("# AI Configuration\n", "# AI Configuration\n\n" + note, 1)

# 4. Build the appendix — each linked file embedded verbatim. No <a id> tags;
#    the "### {relpath}" heading's own slug is the anchor target.
parts = [
    text.rstrip(),
    "\n\n## Appendix: bundled resource files\n\n",
    "Every relative link above resolves here. Each rules / skills / hooks / "
    "context file and `settings.json` is embedded verbatim so this document is "
    "fully self-contained — no access to the source repo required.\n\n",
]
for relpath, lang in FILES:
    content = (SRC_AI / relpath).read_text().rstrip("\n")
    fence = tilde_fence(content)
    parts.append(f"### {relpath}\n\n")
    parts.append(f"{fence}{lang}\n{content}\n{fence}\n\n")

merged = redact("".join(parts))

# 5. Fail loud on any identifier that slipped past the redaction map.
leaks = sorted(set(LEAK_RE.findall(merged)))
if leaks:
    sys.exit("REDACTION LEAK — these tokens survived: " + ", ".join(leaks))

OUT.write_text(merged.rstrip() + "\n")

# 6. Validate: every in-page (#...) link resolves to a heading slug; report dups.
headings = re.findall(r"^#{1,6}\s+(.*)$", merged, flags=re.M)
seen, slugs = {}, set()
for h in headings:
    base = gh_slug(h)
    n = seen.get(base, 0)
    slugs.add(base if n == 0 else f"{base}-{n}")
    seen[base] = n + 1
links = set(re.findall(r"\]\(#([^)]+)\)", merged))
broken = sorted(links - slugs)

print("missing link tokens in README:", missing or "none")
print("leftover relative links:", leftover or "none")
print("redaction leaks:", leaks or "none")
print("broken in-page anchors:", broken or "none")
print(f"output: {OUT} ({OUT.stat().st_size:,} bytes)")
