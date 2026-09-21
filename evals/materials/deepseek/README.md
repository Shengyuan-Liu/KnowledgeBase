# DeepSeek API documentation corpus

Frozen English documentation captured on **2026-09-21** from the
[official API documentation site](https://api-docs.deepseek.com/).

- **89 Markdown files** in [md/](md/): 73 documentation routes and 16 API FAQ entries.
- **89 byte-identical TXT copies** in [txt/](txt/) for the project's TXT-only uploader.
- **362,876 bytes** in either representation, excluding manifests and this guide.
- [Catalog](catalog.md): every document, original URL, Markdown and TXT path.
- [Manifest](manifest.json): source URLs, capture timestamps, SHA-256 digests,
  byte counts, source HTML/bundle digests, images, internal links and exclusions.
- [Evaluation set and instructions](../../deepseek/README.md).

## Scope and completeness

The site sitemap contains 73 URLs. The crawl also followed documentation links
and found `guides/comparison_testing`, which was absent from the sitemap.
Of those 74 routes, 73 document bodies were captured. The remaining route,
`/prompt-library`, is a Chinese-only client-rendered landing page and is explicitly
excluded from this English corpus. The sitemap and complete discovery list are
preserved. There are no unexplained failed captures.

The documentation `/faq` page only links to the official external FAQ app.
The 16 English questions in its API category were additionally extracted from
the structured Markdown data embedded in that app's public JavaScript bundle.
The bundle was parsed as data, never executed. Consumer chat, login, and general
user-guide FAQ categories are outside this API-documentation scope.

This is a complete **text capture of the included routes**, not a mirror of every
linked website or every visual/interactive asset. Image URLs and available alt
text are retained, with an image inventory per document. Images, image-only
benchmark tables, videos, external repositories, linked PDFs and interactive
calculator behavior are not transcribed. Questions do not require facts available
only in those assets. The live platform/account pages are not part of the corpus.

## Extraction details

Each Markdown file preserves the page title, headings, prose, lists, hyperlinks,
code blocks, code line breaks and all server-rendered language tabs, including
hidden panels. Navigation, copy buttons and API playground loading placeholders
are removed. HTML tables, including merged cells, are expanded into Markdown
rows; repeated values in merged cells deliberately preserve their association.
Links are absolute. Every file records its original URL and capture timestamp.
Trailing whitespace is normalized; prose hard line breaks use explicit `<br>`.

The English Tool Calls page had two Chinese JSON-schema description strings.
Only those descriptions were translated into English: “Can be an email address”
and “Or an 11-digit mobile phone number.” All parameter identifiers are preserved.
Other source examples are captured as published; this is not a claim that every
publisher-provided code sample executes without errors.

## Source anomalies retained for evaluation

- `/news/news251201` returned HTTP 200 with the same body as the homepage,
  **Your First API Call**, rather than its original announcement. Its manifest
  entry has `duplicate_of: "index"`. It remains a separate route capture; there
  are **88 unique captured document bodies** across the 89 files.
- The September 10, 2026 announcement describes future routing of V4 Pro to
  V4.1-Flash. The Change Log adds a decision to continue V4 Pro service after
  September 14 with unchanged billing; the pricing table still lists Pro
  separately. Tests require locating that clarification and attributing claims.
- Older announcements describe different image-token caps, rates, model names
  and concurrency rules. Historical questions are explicitly dated/page-scoped.
- Integration guides contain application-specific model catalogs, compatibility
  settings and sample prices. They are not authoritative substitutes for current
  API limits or the pricing page.

## Import without answer leakage

Upload **only `txt/*.txt`**, or only `md/**/*.md` into a system that accepts
Markdown. Never ingest both representations in the same experiment. Do not
index this README, catalog, manifest, test questions, expected answers, evidence
annotations or evaluation reports. Use a fresh isolated data directory; mixing
this corpus with NYU documents changes the benchmark.

The TXT files intentionally contain the same Markdown source text. Changing the
extension makes them acceptable to the existing uploader without changing text,
chunk boundaries or evidence offsets. TXT filenames are flattened with `__` so
the web uploader preserves unique names across directories.

Source content remains attributed to its publishers; capturing it here does not
relicense it as original project documentation.
