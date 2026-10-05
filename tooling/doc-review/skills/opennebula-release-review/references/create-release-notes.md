# Create Release Notes

Explicit Create performs the existing review analysis, then writes supported changes to the requested release notes in the same run. It is an editorial operation using the existing collectors, not a new collector flag. Do not stop after proposing a plan or ask for a second authorization to make the already requested edits. Review remains report-only unless fixes are requested.

## Target and Evidence

Confirm the release, exact milestone, repository and destination using the selected major or maintenance workflow. Default to updating the explicitly named local document; respect a requested separate draft or no-edit constraint. Do not edit a fetched temporary copy and imply the repository document was updated. If the target does not exist, create it at the established release-note path when unambiguous, using adjacent notes for frontmatter conventions. Do not invent a publication date or overwrite another release's file.

For an existing document, collect against its unchanged source and record its hash before editing. For a new document, use an empty temporary Markdown input for the collector and record that no original document existed. Read all matching entries and outcomes, search for semantic coverage, and account for exclusions, out-of-milestone references and uncertain classifications exactly as in Review. A closed issue or Feature Type alone is not proof of delivery or a backport.

Build the applicable review table with concrete edits and evidence, then apply supported rows. Keep unresolved additions out of publishable prose and report conditional drafts separately. Preserve existing uncertain text pending resolution rather than silently replacing a potentially misattributed URL or deleting legitimate coverage. If collection is partial or fails, do not present the result as a complete release inventory; apply only independently supported changes and explain the remaining gap. Never manufacture release facts to fill a section.

## Major Release Creation

1. Run the major comparison on the existing `whats_new.md` before drafting its overview. Assess existing features and fixes for accurate wording and placement as well as finding missing entries.
2. Read the published 7.2 and 7.4 examples linked in [review-rules.md](review-rules.md), or equivalent available published snapshots. Record their branch/revision or content hash and retrieval time in the report. Use their tone, length, structure and audience as style references, not evidence of target-release functionality. If unavailable, disclose that limitation and follow the documented structure without claiming an example-based style check.
3. Draft or revise a concise introduction that identifies the target release and connects its most significant supported changes to user benefits. Avoid invented themes, performance figures, availability claims or marketing superlatives. Preserve suitable existing material rather than appending a second introduction.
4. Create approximately 8–10 feature-highlight bullets, selected for user impact using the review rules. Use fewer when the supported inventory does not justify that many. Distinguish the short benefit-oriented highlight from its detailed entry; intentional highlight/detail repetition is allowed. Do not treat routine fixes as new features to meet a quota.
5. Complete the categorized new-feature inventory using existing category names where suitable, adding a category only when needed. Include all relevant supported features, linking their issues and relevant documentation where verified. Merge related changes only when every issue and meaningful behavior remains covered. Rewrite existing entries that misstate or obscure the delivered behavior.
6. Preserve and complete the separate list of features already backported to the previous major version's maintenance releases. Identify the maintenance version when supported. Do not describe a previously available capability as newly available for the first time. Backport placement needs the evidence required by the review rules.
7. Complete **Other Issues Solved** with relevant fixes and stability improvements. Reword existing summaries to identify faulty behavior and affected conditions; preserve exact command/API identifiers and supported scope. Use fix-oriented wording for fixes, without recasting the major-release document as maintenance notes.

Retain frontmatter, suitable headings, anchors, Hugo shortcodes, links, upgrade notices and unrelated user edits. Do not create placeholder public bullets or empty categories merely to fill the outline. Explain any section left incomplete because evidence is missing.

## Maintenance Release Creation

Run the established maintenance collector and comparison, including every milestone state and every existing issue URL. Retain its four match/candidate tables and coverage summary.

- Add supported missing fixes under **Resolved Issues** and supported backports under **Backported Features**. Verify the backport origin and maintenance inclusion before treating a feature candidate as publishable.
- Reword existing entries when the comparison supports clearer or more accurate descriptions. Move entries only when their final classification is supported. For semantic-only matches, add the correct issue URL instead of duplicating the text.
- Do not add an introduction, feature highlights, or major-release categories to maintenance notes. Preserve existing section lead-ins and ancillary upgrade/configuration instructions. A new document uses the two principal sections and repository frontmatter conventions.
- For a possibly misattributed URL, retain the existing entry until the correct association is established; report the conflicting descriptions and proposed alternatives. Open, declined, duplicate and internal-only work must not become published additions simply because it is in the milestone.

## Check and Report

Re-read the target before writing and reconcile intervening edits. After editing, inspect the diff and source links, ensure no unrelated content was lost, and check additions for duplicate URL or semantic coverage. Reuse the collected inventory with a fresh source extraction when checking the final document; do not confuse the original collector line numbers/hash with the revised document. A rerun with the same evidence should not add duplicate introductions, highlights or detailed entries.

Follow AGENTS.md; do not run an unrequested site build. Never execute document commands, configuration or code examples. Source inspection and collector/report tooling remain permitted.

Report the applicable major table or four maintenance tables with stable IDs and an additional **Result** column: applied, retained, omitted or pending evidence. Include structural changes (introduction, highlights, categories) as document-wide rows. Give actual added/replacement text, destination sections, supporting evidence and unresolved conditional drafts; account for every collected identity. Coverage counts must state whether they describe the original or final document. Keep the original comparison counts and final dispositions distinct so applied additions remain traceable.

When output is requested, save the Markdown report under `tooling/doc-review/out/` unless another destination is supplied, using the shared output contract. Identify both original and final document hashes and assess the **final document** in the Quality Assessment text/table. Count remaining confirmed findings separately from resolved findings; unresolved evidence is not a confirmed defect. The report may have its own introduction even for maintenance creation. Without output, provide the tables and change summary conversationally.

Finish with the edited/draft path, report path if requested, applied changes, remaining evidence gaps and validation limits. Creating local notes does not authorize publishing, committing, opening PRs, posting comments or changing GitHub issues/milestones.
