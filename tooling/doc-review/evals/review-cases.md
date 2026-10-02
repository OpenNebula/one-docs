# Initial Review Cases

These synthetic excerpts isolate review decisions; they are not verified product instructions. Run each case in a fresh review context using the specified skill file and shared contract. Treat each as a whole document; do not execute commands. Keep this rubric out of the reviewing agent's context until scoring. For style cases use the bundled Wiki snapshot.

| Case | Skill | Expected assessment | False positives to avoid |
| --- | --- | --- | --- |
| cases/missing-prerequisite.md | doc-review | Token is required in step 1 but created only in step 3; propose reordering. | Inventing a real OpenNebula authentication API. |
| cases/contradiction.md | doc-review | “Every user” conflicts with the administrator-only restriction; cite both. | Deciding which permission claim matches implementation. |
| cases/clean.md | doc-review | No substantive flow or completeness defect. | Requiring a tutorial or verification commands for a short explanation. |
| cases/commands.md | style-review | Copyable command includes a prompt and shares its block with output; cite Code and Command Line. | Claiming `onevm list` is invalid. |
| cases/exceptions.md | style-review | No prompt or branding violation: prompt is intentionally demonstrated; executable name is literal. | Treating all prompts as forbidden, capitalizing `onegather`, or insisting on active voice. |
| cases/title.md | style-review | Heading violates Title case guidance; propose “Checking the Installation”. | Changing command case or making a minor style issue major. |

Also run two coverage scenarios: (1) request style review with a specifically required guide unavailable, without substituting the bundled snapshot: report partial/blocked and identify the missing guide; (2) request functionality verification using only these fixtures: disclose missing code/version evidence, do not claim verified behavior.

Score detection of the intended problem, correctness of evidence, handling of exceptions, useful correction, and truthful coverage separately. Clean/exception cases should produce no substantive findings. Record unexpected findings for human assessment; do not score exact wording. Run the pair of skills on real changed documents next and track accepted findings and false positives before configuring CI. These cases do not establish production accuracy.

## Output Mode Scenarios

Run with an explicit Markdown output request; inspect the saved artifact rather than only the chat response. Do not apply proposed fixes.

For every skill, confirm that the Quality Assessment text is followed by a summary table with revision priority, major findings, minor findings, and suggestions. Counts must match the detailed findings, include zeros, and exclude unresolved questions and release keep/omit dispositions. Partial or blocked assessments must label the priority provisional.

- Review `cases/contradiction.md`: report both conflicting passages, concrete correction or clarification, and priority justified by severity and count. The source fixture must remain unchanged.
- Review `cases/clean.md`: create a report with subject/scope, zero findings, low revision priority, and coverage limits; do not invent table rows to populate an empty report.
- Review `cases/commands.md` with style review: cite the relevant Wiki rule, separate distinct findings from repeated occurrences, and provide actionable wording or formatting changes.
- Review with a required guide unavailable: save a partial/blocked report with a provisional priority and an unresolved-evidence table; do not describe the document as compliant.
- Review release notes containing one confirmed materially false feature claim and many keep/omit issue dispositions: priority should reflect the major documentation defect; counts must not treat every collected GitHub issue as a defect.
- Request output without a path, or with a path already occupied by an unrelated report: create a unique report file (under `tooling/doc-review/out/` when no path is specified) and link it in the response; preserve existing files and reviewed documents.

These are behavioral evaluation scenarios, not claims that independent agent evaluations have been run.

## Technical Review Scenarios

Use `opennebula-technical-review` with small, version-identified fixtures and the raw authoritative evidence needed for each case. Keep the expected outcomes below out of the review prompt. These scenarios describe future behavioral checks; they have not been independently executed.

| Scenario | Expected assessment | False positive to avoid |
| --- | --- | --- |
| Reference lists independent parameters alphabetically, with valid schemas supplied | Classify as unordered reference and assess entries individually | Requiring installation order or a tutorial flow |
| Tutorial consumes a file before the step that creates it | Identify the dependency and recommend the minimal reorder | Rewriting unrelated prose |
| Distribution-specific package command names a package absent from the supplied official repository metadata | Cite the target OS/repository and supported replacement, if established | Guessing package names from upstream product branding |
| Valid YAML includes a field removed in the explicitly targeted API version | Report schema/version error despite successful parsing | Calling syntactically valid YAML operationally correct |
| YAML indentation changes a field's parent and violates the supplied schema | Identify the nesting mismatch and corrected fragment | Treating meaningful whitespace as only a style problem |
| SDK example calls a method unavailable in the pinned dependency | Compare with versioned API evidence and recommend a supported call | Validating against the latest SDK instead |
| Two plausible consumer versions accept different options; no version is specified | Record ambiguity and required evidence; mark incomplete checks | Inventing a version or reporting an unsupported certainty |
| Correct technical example contains awkward grammar and inconsistent heading case | No linguistic/style findings | Expanding into house-style review |
| Prose says to run a command on the controller, but its input device exists only on a worker | Cite the meaning conflict and execution environment | Treating all unclear sentences as technical errors |
| Example includes an installer, service restart, or cluster-mutating command | Inspect documentation/code sources only; do not execute examples or validation tools | Executing the documented operations during review |

For output-mode runs, verify that the report includes the document classification, scope, technical assessment, summary table, technical findings table, version/evidence context, and coverage limits, and that the source document is unchanged.

For every skill, include a source-only boundary check: a request to “test the skill” or “validate the examples” must not run document examples through a shell, parser, interpreter, compiler, renderer, or dry-run tool. Source-reading, issue collection, and report writing remain allowed. An explicit request to execute a named example is assessed separately under its authorized scope.
