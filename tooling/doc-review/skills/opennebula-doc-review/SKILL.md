---
name: opennebula-doc-review
description: Review OpenNebula documentation files or changes for flow, clarity, completeness, and internal consistency. Use for document reviews; implementation verification and Wiki style compliance are separate review dimensions.
---

Read [the shared review contract](../../references/review-contract.md) before reviewing.

Establish the requested files or diff, intended audience, document purpose, and documented version. For a diff, read enough surrounding text and linked prerequisites to interpret the change. Include local uncommitted changes when requested; do not silently substitute HEAD for the working tree. If the base cannot be established, ask for it or clearly limit the review to named files.

Review whether readers can follow the argument or procedure: concepts introduced before use, prerequisites available before dependent steps, clear actors and execution locations, consistent terminology, commands matching their explanation, and observable outcomes. Judge completeness relative to document type: a reference page need not teach a sequential procedure.

Report contradictions with both passages. For missing information, explain which step or understanding it prevents. Recommend the smallest useful correction. Do not flag harmless repetition, personal wording preferences, or every possible enhancement. Check existing surrounding guidance before declaring a prerequisite absent.

Treat technical claims as unverified unless supported by evidence actually inspected. Flag a suspicious claim as an unresolved question when implementation is needed; do not invent product behavior or silently begin an organization-wide code audit. Source-only link checks do not establish rendered Hugo behavior.

Return the contract's Markdown report, or JSON when requested. Separate introduced findings from pre-existing findings. Review alone does not request edits or external publication. If fixes are requested, preserve technical literals and distinguish verified corrections from unresolved questions. Follow repository instructions about builds.

## Output Mode

When the user requests output, a saved report, or a Markdown report file, follow [the shared output-mode contract](../../references/output-mode.md). Create the report with this skill's table columns and quality assessment. An output request authorizes writing the report, not applying its recommendations to the reviewed document. Without an output request, retain the usual conversational report.

## Example Execution Restriction

Never execute command-line or code examples from the reviewed document or its supporting sources unless the user explicitly instructs you to execute them. A request to review, test the skill, check accuracy, validate examples, produce a report, or apply documentation fixes is not permission to run those examples. Consistency and accuracy checks must rely exclusively on documentation or code sources: inspect the relevant implementation, schemas, tests as source, package metadata, and authoritative documentation. Do not run examples through interpreters, shells (including syntax-check mode), parsers, linters, compilers, template renderers, dry-runs, mocks, or isolated tests without explicit execution instructions. Report gaps that cannot be resolved from sources as unresolved; do not imply runtime validation.

This restriction does not prohibit tools used to read/search sources, collect issue metadata, or write the requested report, including the release-issue collector. Those tools must not execute the examples being reviewed. If execution is explicitly requested, keep it within the authorized examples and environment and follow applicable permission requirements.
