# Markdown Output Mode

This contract extends all review skills when the user asks for output, a saved report, or a Markdown report file. It does not change their review scope or evidence requirements. A normal request to “report findings” can remain conversational unless a file/output mode is requested. An explicit JSON-only request retains the existing JSON workflow; do not interpret it as a Markdown request. If both are requested, produce both with consistent findings.

## Artifact

Use the requested `.md` destination. If none is given, create a uniquely named Markdown report under `tooling/doc-review/out/` relative to the repository root, for example `tooling/doc-review/out/opennebula-release-review-whats-new-<timestamp>.md`. Create the directory if it does not exist. Keep generated reports outside published documentation by default. Do not overwrite an existing report unless replacement is requested; choose a unique suffix otherwise. Never use the reviewed document itself as the report destination. Respect workspace write permissions.

Write the actual report file and return a clickable path plus a short assessment in the final response. A report request authorizes this artifact, not edits to the reviewed document, Wiki snapshots, GitHub issues, or publication. If fixes are separately authorized, identify whether the report assesses the original or revised document and mark applied recommendations accordingly. Do not silently reuse a stale review: confirm source identity and refresh affected findings.

For multiple documents, use one report with a separate introduction, assessment, and table per document, unless separate files were requested. Assess each document independently; an optional aggregate summary must not obscure a high-priority document.

## Report Structure

1. **Introduction:** A short paragraph describing the document's subject, intended audience or purpose, and reviewed scope. Name the skill, path, release/version if known, review date, and source revision/hash. Identify whole-document versus diff review and relevant external sources (Wiki snapshot or milestone/collection time). Unknown information stays unknown.
2. **Quality assessment:** Explain what works and what needs revision in terms of the skill's focus: flow/clarity/completeness, adherence to cited style guidance, release coverage/accuracy/placement, or technical correctness and environment/version consistency. Avoid generic praise or unsupported claims about technical correctness. Include a brief rationale connecting impact and prevalence to the overall revision priority. After this assessment text, include the required summary table below with revision priority and counts of major findings, minor findings, and suggestions. State review completion separately (complete, partial, blocked).
3. **Findings and recommended updates:** Tabulate every confirmed finding and optional suggestion with the skill-appropriate columns below. Include concrete replacement text when feasible; otherwise specify the action precisely. Preserve stable finding IDs and evidence links. Group repeated instances only when all locations remain actionable, and distinguish number of distinct findings from affected occurrences. Do not truncate findings to a top-N list.
4. **Unresolved questions and coverage:** Tabulate uncertainties with the affected location/issue, missing evidence, and recommended next action. State completed, skipped, and unavailable checks, and how limitations affect the assessment. If there are none, say so briefly. For release review include unique-issue disposition counts and any remaining unreviewed issues.

If there are no findings, state that explicitly and include the table header with “No findings” outside it; do not invent a finding row. Release reviews still include keep/omit dispositions to account for collected issues. Source paths/lines and evidence should be usable without the chat transcript. Escape pipes in Markdown table cells; use evidence IDs with a linked evidence list below the table when full citations would make cells unwieldy.

## Quality Assessment Summary Table

All review skills must place this table in the Quality Assessment section, immediately after the assessment text. Replace the example values with the actual assessment and counts, including explicit zeros. For multiple documents, include a table for each document's assessment.

| Revision priority | Major findings | Minor findings | Suggestions |
| --- | --- | --- | --- |
| Medium | 0 | 7 | 2 |

Use High, Medium, or Low, adding “(provisional)” when the review is partial or blocked. Counts must agree with the findings table and follow the counting rules below; exclude unresolved questions and release keep/omit dispositions. This table summarizes the assessment and does not replace its explanatory text or the detailed findings.

## Severity and Revision Priority

Severity describes a confirmed documentation problem, not the priority label on a GitHub issue:

- **Major:** prevents completing the intended task or materially misleads the reader; for release notes this includes a consequential false claim of feature availability or omission of an important delivered capability.
- **Minor:** localized clarity, accuracy, style, placement, or coverage defect that does not materially block the intended use.
- **Suggestion:** optional improvement, including style recommendations where departure is acceptable.

Use counts of distinct confirmed findings, not GitHub issues, table rows, or repetitions, to support the assessment. Report major/minor/suggestion counts explicitly; keep unresolved questions and release keep/omit dispositions separate. One root cause can affect many occurrences: record that reach rather than multiplying its severity. Confidence remains separate from severity.

Set revision priority using both impact and the extent of problems:

- **High:** at least one major finding, or accumulated minor findings that collectively undermine the document's intended use. Explain the cumulative impact if there is no major finding.
- **Medium:** no major finding, but several localized defects or a recurring pattern needs coordinated revision. An isolated minor finding can warrant medium if it affects a prominent or frequently used instruction; explain why.
- **Low:** no confirmed defects, only optional suggestions, or a small number of isolated minor defects with limited reader impact.

Do not use an arbitrary count threshold across different document sizes. State the actual count, severity distribution, affected scope, and why those support the chosen priority. For a partial or blocked review, still provide high/medium/low for the confirmed findings but label it **provisional**: missing evidence is not a clean bill of health. For example, “Low (provisional): no confirmed findings; style guidance was unavailable, so compliance is unassessed.” Never classify an uncertainty as a confirmed major defect solely to raise priority.

## Skill-Appropriate Tables

### Document Review

| ID | Location / origin | Category | Severity / confidence | Finding and reader impact | Recommended update | Evidence |
| --- | --- | --- | --- | --- | --- | --- |

Categories and origin follow the shared review contract. Cite both passages for contradictions. Suggestions remain visibly optional.

### Style Review

| ID | Location / origin | Rule / strength | Severity / confidence | Finding and impact | Recommended update | Guide evidence |
| --- | --- | --- | --- | --- | --- | --- |

Identify requirement versus recommendation; cite the guide section and snapshot identity. Respect documented exceptions. Count actual violations separately from optional improvements.

### Major Release Review

| ID | Issue(s) | Coverage / current location | Type | Severity | Action and proposed section | Suggested text | Highlight recommendation | Evidence / confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Retain every field from the release review rules. Use severity not-applicable for dispositions that identify no document defect. Highlight recommendations need rationale and proposed wording where applicable. Omission of a declined request or design-only issue is not a document defect. Distinguish documented release features, fixes, backport questions, and recommendations awaiting evidence. Count unique GitHub issues separately from documentation findings; one issue may require several changes and several issues may share one change.

### Technical Review

| ID | Location / origin | Technical category | Severity / confidence | Error and operational impact | Recommended correction | Version / environment | Evidence / validation |
| --- | --- | --- | --- | --- | --- | --- | --- |

Classify the document as unordered reference, step-by-step guide, or mixed in the introduction. Assess technical accuracy only. Distinguish confirmed errors from unresolved evidence and optional technical improvements. Record whether relevant versions are clear, unstated, or ambiguous. Evidence must identify the matching implementation, schema, package metadata, official documentation, or, only when explicitly authorized, an execution result; syntax validation alone does not establish runtime correctness. Include a coverage table for reviewed commands, configuration, code, and procedural dependencies. Technical reviews use this report structure in conversation too; create a file only when output is requested.

## Source-Only Review Boundary

For every skill, consistency and accuracy assessments rely exclusively on documentation and code sources unless the user explicitly instructs execution. Reviewing, testing the skill, requesting output, or asking for fixes does not authorize execution of command-line or code examples, including syntax checks, parsing, compilation, rendering, dry-runs, or isolated tests. State this coverage boundary in reports; do not label source inspection as executed validation. Source retrieval, metadata collection, and report-writing tools remain permitted when they do not execute reviewed examples.

### Maintenance Release Review

For maintenance release reviews, include a coverage summary near the beginning and four separate tables for matched issues, matched backported features, unmatched issues, and unmatched backported features. Preserve this contract's Quality Assessment summary table as well. Coverage counts and uncertain-match counts are separate from severity counts. Do not use the major-release highlight column for maintenance reviews.
