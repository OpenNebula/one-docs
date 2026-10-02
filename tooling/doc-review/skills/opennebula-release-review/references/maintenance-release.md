# Maintenance Release Review

Review `resolved_issues_XYZ.md` for the requested maintenance version. Confirm the exact repository, milestone, file and release; do not silently review the major release's whats_new.md. The two principal content sections are **Backported Features** and **Resolved Issues**. Preserve ancillary upgrade instructions. Do not recommend a release introduction, major-release highlights, or feature categories for this document. The review report itself still needs its normal introduction and quality assessment.

Representative example: [7.4.1 notes](https://docs.opennebula.io/7.4/software/release_information/release_notes/resolved_issues_741/). It includes repeated issue URLs, unlinked feature text, and upgrade instructions; do not assume one bullet per issue.

## Collection

Run the maintenance collector, for example from the repository root:

```shell
python3 tooling/doc-review/skills/opennebula-release-review/scripts/collect_maintenance_release.py \
  --repo OpenNebula/one --milestone-number 94 \
  --notes content/software/release_information/release_notes/resolved_issues_741.md \
  > /tmp/opennebula-maintenance-review.json
```

Milestone 94 is the one linked by the 7.4.1 example; confirm the selected file/release before using it. `--milestone` accepts an exact title instead. Authentication uses GH_TOKEN/GITHUB_TOKEN as in the major collector. The collector reuses the shared Markdown parser, API pagination and milestone resolution. It reads **all open and closed milestone issues**, and additionally fetches all recognized issue URLs in the notes even if they belong to another milestone or repository. Pull requests returned by the issue API are excluded and recorded. Bodies, comments, labels, state/reason, milestone, actual GitHub Type metadata, source locations, and multiple matching entries are retained.

Exit 0 means collection completed, 1 means failure with no report, and 2 means a partial JSON report with inaccessible referenced issues (403/404/410). Never interpret inaccessible issues or absent Type metadata as clean matches. Other collection/comment failures abort. Do not expose credentials. Collection reads metadata, not the document's command examples.

`Feature` Type suggests a backported feature; `Bug` suggests a resolved issue. Types are not labels. Missing/other Types stay unknown until reviewed; never silently default them to Bug. Existing section placement provisionally routes URL matches; Type routes absent candidates. Type/section conflicts, cross-section repetitions, and unlinked paragraphs require review. Collector counts are provisional; semantic uncertainty counts are null until assessed by the skill, not zero.

## Review

1. Inspect every matched entry against the issue's resolved outcome, including comments and linked source/documentation as needed. Assess accuracy, meaningful clarity improvements and correct section. Cite the sentence and issue evidence, and include actual suggested replacement text. Keep correct entries with a no-change disposition.
2. Explicitly flag **possible misattributed issue URL** if text and issue describe materially different components/behaviors. Do not rewrite the text to fit an unrelated issue or guess a replacement URL. Record the competing descriptions and required confirmation. Count this as a matched entry with uncertainty, not as verified coverage.
3. Search the full document for semantic coverage of each URL-unmatched issue before proposing an addition. If already described, route to the appropriate matched table as a semantic match and recommend adding the correct URL. Preserve many-to-one entries and review every occurrence of repeated links.
4. For genuinely unmatched issues, propose concise summary text with the issue URL and the relevant section. State add, defer, omit or investigate. Open, not-planned, duplicate, internal-only, design-only or unsupported changes must not automatically become published entries. Keep them accounted for with a rationale; conditional drafts must be labeled conditional.
5. Classify from delivered behavior, using Type as evidence rather than a rule. A feature belongs under Backported Features only when its next-major/master origin and maintenance inclusion are supported. Record missing provenance as uncertain; the initial milestone-based scope does not require an automatic Git-history audit. Bug/stability work normally belongs under Resolved Issues. If classification cannot be resolved, retain an explicit unclassified row rather than forcing a category.
6. References outside the milestone are reviewable matches, not automatically errors or removal candidates. Check unlinked feature bullets and any ancillary issue references manually. An issue referenced only by unrelated upgrade text is not necessarily covered by a release summary.

## Report

Follow the shared output contract for introduction, quality assessment and severity/priority table. Immediately after the short report introduction, add this coverage summary:

| Classification | Matched | Matched with uncertainty (subset) | Unmatched |
| --- | --- | --- | --- |
| Resolved issues | count | count | count |
| Backported features | count | count | count |

Counts are **unique repository+issue identities**, not URLs or bullets. Matched includes explicit URL and confirmed semantic matches; uncertain URL attribution remains matched-with-uncertainty. Uncertainty includes unresolved attribution, classification, release inclusion, or material wording conflicts. Straightforward evidenced wording corrections need not be counted uncertain. Unmatched includes all not-covered milestone candidates, including deferred/omitted ones; break those dispositions out below the table. Show unclassified and inaccessible counts separately. Each identity has one final classification bucket; cross-section conflicts unresolved by the reviewer go to unclassified. Separately state milestone total, additional referenced identities, excluded PRs, and semantic-only match count so totals reconcile. Do not confuse these coverage counts with documentation finding severity counts.

Then provide **four separate tables**, even when a table is empty (state “None” rather than inventing a row):

### Matched Issues

| ID | Issue / state / milestone membership | Match / lines / current text | Assessment / uncertainty | Severity / confidence | Recommended action / suggested updated text | Evidence |
| --- | --- | --- | --- | --- | --- | --- |

### Matched Backported Features

Use the matched-issues columns plus **Backport evidence / classification rationale**. Call out possible misattributed URLs explicitly and preserve uncertainty when it cannot be resolved.

### Unmatched Issues

| ID | Issue / Type / state | Inclusion decision and rationale | Severity / confidence | Suggested summary with issue URL | Evidence / uncertainty |
| --- | --- | --- | --- | --- | --- |

### Unmatched Backported Features

Use the unmatched-issues columns plus **Backport evidence / classification rationale**. Do not label an addition release-ready without supporting inclusion evidence.

Use not-applicable severity for no-change and justified non-addition dispositions. Provide document-wide, unclassified and inaccessible-reference questions in an additional table when necessary. Include corrected section placement explicitly in actions. Finish with coverage, unique-issue disposition totals, and unresolved evidence. A partial collection or unresolved required checks must be identified; never claim shipped-change completeness. Reports are conversational unless Markdown output is requested; saved reports default to `tooling/doc-review/out/`. Apply suggestions only on subsequent explicit instruction.
