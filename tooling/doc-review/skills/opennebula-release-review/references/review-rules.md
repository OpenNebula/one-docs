# Release Notes Review Rules

## Document Structure

The major release's `whats_new.md` normally contains:

1. Introduction with hand-picked highlights and release context.
2. Approximately 8–10 feature highlight bullets.
3. Categorized relevant new features (Core, Sunstone, API and CLI, etc.).
4. Features backported to the preceding major version's maintenance releases.
5. Other Issues Solved: fixes and stability improvements.

Preserve existing headings and category vocabulary where suitable. Highlight count is an editorial target, not a quota: do not invent significance or delete valid highlights just to meet it. Introduction/highlight bullets may precede the first heading. A new draft can lack sections; propose their creation explicitly.

Finished structural examples (consult when needed; not evidence that a change shipped in the target release):

- [7.2](https://github.com/OpenNebula/one-docs/blob/one-7.2/content/software/release_information/release_notes/whats_new.md)
- [7.4](https://github.com/OpenNebula/one-docs/blob/one-7.4/content/software/release_information/release_notes/whats_new.md)

These branch URLs can change; record retrieval time and commit or content hash if used as review evidence. The examples include unlinked feature descriptions, multiple issues in one bullet, and repeated issue links. Do not assume a one-to-one mapping.

## Classification and Placement

A feature introduces or materially extends a user-visible capability. A fix restores intended behavior, resolves a defect, or improves stability. Classify from the delivered outcome; labels and titles are hints. Split mixed work into distinct proposals if necessary, retaining a shared issue reference. Internal-only changes may not merit a public entry: explain exclusions.

Recommend a highlight for broad user impact, a significant new capability, major platform support, or an important operational improvement. Explain the audience and benefit. A feature can have both a short highlight and categorized detail; those serve different purposes. Do not promote ordinary fixes into features by changing wording. Significant fixes can be called out in the introduction if justified, while remaining fixes in the detailed list.

Backport placement requires evidence that a feature reached a maintenance release of the previous major version after its initial release. Cite maintenance notes or verified backport/release evidence. Milestone membership, a backport label, and closure dates alone do not establish this. Distinguish new-to-this-major features from capabilities already delivered in that maintenance series. If evidence is missing, mark placement unresolved rather than guessing.

For fixes, describe the faulty behavior and when it occurred; for features, describe the added capability and relevant limitation. Preserve exact API names and options. Do not invent performance guarantees, edition availability, support status, versions, or security claims. Issue text may describe a request rather than the final implementation: seek resolution evidence when these differ.

## Required Report

These analysis and accounting rules also apply to explicit Create. Follow [create-release-notes.md](create-release-notes.md) for authorized editing and applied/pending dispositions; the table is not an additional approval gate in that operation.

Start with a short scope statement: release, repository, milestone title/number, document path/hash and Git revision when available, collection time, issue count, and collection/review status (complete, partial, or blocked). Collection completeness is separate from semantic review completeness. Account for every issue; if context limits require batches, track reviewed and remaining issue numbers and finish them before claiming completion.

For a saved output report, also follow [the shared output-mode contract](../../../references/output-mode.md), including its assessment and revision priority. In that mode, add Severity to the table below; use not-applicable for keep/omit rows that do not identify a document defect.

Then report suggestions in this table:

| ID | Issue(s) | Coverage / current location | Type | Action and proposed section | Suggested text | Highlight recommendation | Evidence / confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |

Use stable row IDs, linked issue identities, and source line numbers. Coverage is URL match, semantic match, absent, or unresolved. Type is feature, fix, mixed, or not release-note material. Actions include keep, reword, add link, move, add, omit, or investigate. A keep row can say “No change”; every proposed addition or rewrite must contain the actual proposed wording and issue URL. For moves, name both sections. For highlights, provide suggested highlight text and rationale, or “No” with a brief reason. Escape pipes in Markdown cells.

Evidence must explain the relevant issue body/comment/PR outcome, not merely repeat a link. Give confidence high/medium/low separately from importance. Semantic matches must cite the existing sentence. Group related issues only if each is accounted for. Place document-wide structural proposals and out-of-set references in additional rows, without assigning fictitious issue numbers.

After the table, summarize disposition counts (count unique issues, not rows), unresolved evidence, and coverage limits. Missing evidence is not a confirmed error. A report that has not checked implementation or release history must not claim shipped-change completeness.

## Collector Boundaries

The collector reads REST repository milestones (`state=all`), repository issues filtered by milestone and `state=closed`, and issue comments. It does not use GitHub search and its search-result cap. Pagination continues until a page contains fewer than 100 records; API/rate-limit failures abort instead of producing a partial success. GitHub can change during collection; the timestamp is not an atomic historical snapshot.

The parser provides source blocks, not a complete Markdown/Hugo AST. Inspect unusual nested lists, HTML, reference definitions, conditional content, and bare issue numbers manually. URLs from another repository remain separate identities. PR URLs are not issue matches. Out-of-set links can refer to open issues, other milestones, other repositories, or legitimate historical entries.

API references: [repository issues](https://docs.github.com/en/rest/issues/issues#list-repository-issues), [milestones](https://docs.github.com/en/rest/issues/milestones#list-milestones).
