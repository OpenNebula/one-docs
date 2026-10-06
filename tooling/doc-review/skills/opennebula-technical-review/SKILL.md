---
name: opennebula-technical-review
description: Review OpenNebula technical references, tutorials, and how-to guides for command, configuration, code, environment, and version accuracy. Check procedural dependencies and consistency against relevant implementation or authoritative documentation; exclude style and grammar review.
---

## Establish the Technical Context

Read [the technical checks](references/technical-checks.md) and [the report contract](references/shared/output-mode.md). Identify the target files, source revision or content hash, and whether this is a whole-document or diff review. In a diff review, examine surrounding prerequisites and examples and distinguish introduced from pre-existing defects.

First classify the document as an **unordered technical reference** or a **step-by-step tutorial/how-to**. For a mixed document, classify its sections separately. Check procedures for execution order and state dependencies; do not impose a sequential workflow on independent reference entries.

Identify the intended outcome and environment: OpenNebula release/edition, OS release, architecture, shell, execution machine, user/privileges, dependencies, package repositories, runtime/library/tool versions, and relevant hardware or service state. Record each relevant version as **clear**, **unstated**, or **ambiguous**, with its source. Do not substitute the latest version or an unrelated site version for the document's intended version. Ask for essential missing context when it prevents meaningful verification; continue independent checks and state assumptions explicitly.

## Review for Technical Accuracy Only

Apply the relevant checks in the reference to every command, configuration/manifest/template, and code example in scope. Track inspected blocks and unresolved blocks so omitted checks cannot become a clean assessment. Include technically meaningful claims in prose and expected output. Check package names and options against the intended environment rather than assuming they are correct because they look plausible.

Use matching source code, schemas, tests, package metadata, CLI help, and versioned official documentation as evidence (read tests and CLI help text as sources; do not run tests or invoke reviewed commands). Prefer local matching revisions when available; retrieve primary sources when needed for uncertain or changing technical facts. Record repository/path/lines and commit, or exact URL/version/retrieval date. Read the relevant evidence rather than relying on search snippets. Keep searches bounded to the claim and component being checked.

Distinguish syntax validity, schema/API validity, environment compatibility, and demonstrated runtime behavior. A parser accepting a manifest does not prove its keys are supported; a passing syntax check does not prove code works. Missing implementation evidence is an unresolved question, not proof of an error. Conflicting documentation and code do not automatically establish which should change.

Exclude linguistic flow, tone, grammar, heading capitalization, and house-style preferences. Consider language only when it contradicts the stated purpose, changes technical meaning, conflicts with a command/example, or leaves a consequential interpretation ambiguous. Explain the competing interpretations and operational consequence. Formatting is in scope only when it affects parsing or execution, such as indentation, quoting, escaped characters, or line continuation.

## Source-Based Verification

Inspect syntax and behavior against the relevant language specification, configuration parser implementation, schema, or versioned official documentation. Distinguish source-based conclusions from demonstrated runtime behavior. For templates, inspect the template and its consumer without rendering it. Missing source evidence remains unresolved. Follow repository build restrictions.

## Report and Output Mode

Always return a technical report using the introduction, Quality Assessment text, summary table, priority criteria, and technical findings table in [the report contract](references/shared/output-mode.md). Use **Major findings**, **Minor findings**, and **Suggestions** consistently; the first two represent confirmed technical errors, while suggestions are optional technical improvements. Include all findings, concrete recommended corrections, evidence, and a separate unresolved-question table. Count findings separately from occurrences and uncertainties.

State technical coverage and review completion separately. If missing version or implementation evidence prevents requested checks, label the review partial or blocked and its priority provisional. Do not call untested behavior verified; a completed source review can explicitly exclude runtime execution.

When output or a saved Markdown report is requested, write the report to the specified destination, defaulting to a uniquely named `.md` file in `tooling/doc-review/out/`. Otherwise return the report in the conversation. An output request authorizes the report only. Apply document corrections only on explicit instruction, preserving unrelated changes and rechecking modified examples.

## Example Execution Restriction

Never execute command-line or code examples from the reviewed document or its supporting sources unless the user explicitly instructs you to execute them. A request to review, test the skill, check accuracy, validate examples, produce a report, or apply documentation fixes is not permission to run those examples. Consistency and accuracy checks must rely exclusively on documentation or code sources: inspect the relevant implementation, schemas, tests as source, package metadata, and authoritative documentation. Do not run examples through interpreters, shells (including syntax-check mode), parsers, linters, compilers, template renderers, dry-runs, mocks, or isolated tests without explicit execution instructions. Report gaps that cannot be resolved from sources as unresolved; do not imply runtime validation.

This restriction does not prohibit tools used to read/search sources, collect issue metadata, or write the requested report, including the release-issue collector. Those tools must not execute the examples being reviewed. If execution is explicitly requested, keep it within the authorized examples and environment and follow applicable permission requirements.
