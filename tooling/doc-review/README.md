# Documentation Review Pilot

The document and style review drafts share a report contract and a small evaluation set. The release review skill has a dedicated milestone collector and tabular reporting contract. They live outside the published `content/` tree. This is a repository-local pilot, not an installed skill package or GitHub automation.

Invoke explicitly, for example:

> Read `tooling/doc-review/skills/opennebula-doc-review/SKILL.md` and use it to review my uncommitted documentation changes. Report findings without editing files.

> Read `tooling/doc-review/skills/opennebula-style-review/SKILL.md` and use it to review `content/path/to/document.md` against the bundled Wiki snapshot.

For branch review, specify the comparison base. For document/style JSON output, request the shared schema at `references/report.schema.json`.

The style snapshot and its provenance are under the style skill's `references/` directory. Review cases and scoring guidance are in `evals/review-cases.md`. Keep this directory together: the skills reference shared reporting contracts using relative paths. Copying one skill alone is not a supported installation.

Next: exercise these drafts on real documents, refine findings and exceptions, then choose installation and GitHub report publication. No build is needed to inspect these drafts; follow the repository's build restriction.

## Major Release Notes Review

> Read `tooling/doc-review/skills/opennebula-release-review/SKILL.md` and review `content/software/release_information/release_notes/whats_new.md` against the closed issues in the exact OpenNebula/one milestone I specify. Report the proposed changes in a table; do not edit the notes.

The release skill includes a Python standard-library collector; no GitHub CLI is required. See its instructions for milestone selection, optional authentication, and collection limits. Run collector tests with:

```shell
python3 -B -m unittest discover -s tooling/doc-review/skills/opennebula-release-review/scripts -p "test_*.py" -v
```

## Saved Markdown Reports

All four skills support an optional output mode. For example:

> Use `tooling/doc-review/skills/opennebula-release-review/SKILL.md` to review `content/software/release_information/release_notes/whats_new.md` for 7.6. Output a Markdown report to `tooling/doc-review/out/opennebula-7.6-release-review.md`. Do not edit the release notes.

> Use `tooling/doc-review/skills/opennebula-doc-review/SKILL.md` to review `content/getting_started/overview.md` with output.

Specify a destination or let the skill create a uniquely named report under `tooling/doc-review/out/` (created if needed). Each report includes a short subject/scope introduction, an assessment focused on the skill, high/medium/low revision priority supported by issue counts and severity, and a table of findings with recommended changes. Unresolved questions and coverage limitations remain explicit. Requesting output does not request fixes. See [the output contract](references/output-mode.md) for details.

## Technical Accuracy Review

> Read `tooling/doc-review/skills/opennebula-technical-review/SKILL.md` and review `content/path/to/document.md` for technical accuracy with an output report. Do not edit the document.

This skill distinguishes unordered references from sequential guides, verifies commands, packages, manifests, configuration, and code against the intended versions, and excludes stylistic/grammatical review. It reports unverified behavior separately from confirmed technical errors. Its Markdown output uses the common assessment table and defaults to `tooling/doc-review/out/`.

## Maintenance Release Notes Review

> Read `tooling/doc-review/skills/opennebula-release-review/SKILL.md` and review `resolved_issues_741.md` for maintenance release 7.4.1 with Markdown output. Report suggestions without editing the notes.

Maintenance mode uses `collect_maintenance_release.py` to collect all milestone issues and referenced issue URLs. Its report contains coverage counts and four separate match/candidate tables for fixes and backported features. GitHub Type is a hint; unresolved attribution or inclusion remains explicit.
