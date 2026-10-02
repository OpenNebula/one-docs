# Technical Review Checks

Use only checks relevant to the document's content. Use documentation and code sources exclusively for accuracy and consistency checks. Never execute examples or run validation tools against them without explicit user instructions; a request to test or validate the review skill is not such an instruction.

## Reference or Procedure

For an unordered reference, check each entry's names, types, defaults, units, allowed values, scope, required/optional status, version availability, constraints, and cross-field relationships. Examples embedded in a reference may have their own sequencing dependencies. Do not flag alphabetical or topical order as an execution defect.

For a tutorial/how-to, trace the state required and produced by each step: files, variables, credentials, repositories, installed packages, networks, devices, services, resources, and current directory. Check that prerequisites precede use, commands execute on the correct machine as the correct user, asynchronous operations finish before dependent steps, and validation actually measures the intended result. Inspect linked prerequisites before declaring something missing. Check cleanup against created resources and any subsequent steps that still need them.

For mixed documents, apply both approaches at section level. Distinguish an invalid sequence from an alternative valid sequence; do not demand a particular ordering without a dependency or technical reason.

## Command Lines and Packages

- Correct executable and subcommand for the stated purpose, with correct spelling, argument position, option names, values, input/output formats, and exit-status handling.
- Shell compatibility, quoting, substitutions, redirects, pipelines, line continuations, working directory, environment variables, and placeholders. Does copy/paste preserve the intended command? Is a transcript being mistaken for executable input?
- OS/distribution release and architecture versus package manager, repository configuration, package/library names, version pinning, and package availability. Resolve mappings from upstream project names to distro package names; they need not be identical. Validate against matching official package metadata, not a guessed spelling correction.
- Privileges, permissions, execution Host, filesystem locations, connectivity, hardware, and dependencies needed in the proposed environment.
- Tool/client/server/library versions, supported combinations, and versions implied by downloaded artifacts. A `latest` URL is an unpinned input, not by itself proof of incompatibility. Establish the actual conflict before reporting a defect; otherwise record uncertainty or recommend reproducible pinning where relevant.
- Ordering within command blocks and across steps, including shell backgrounding, conditional execution, service readiness, and resources created elsewhere.
- Expected output must correspond to the command, version, and state. Distinguish illustrative values from assertions that every installation must reproduce exactly.

## Manifests, Templates, and Configuration

- Identify the actual format from its consumer and contents (JSON, YAML, OpenNebula template syntax, ERB, etc.), not only the Markdown fence label. A mislabeled fence alone is a style issue unless it causes a technical misunderstanding.
- Check syntax: indentation, nesting, delimiters, quoting, escapes, types, duplicate keys, interpolation, and meaningful whitespace. Distinguish intentional fragments or ellipses from complete runnable files. Do not report omitted surrounding context as invalid syntax when the excerpt is clearly labeled.
- Verify fields, parameters, options, required values, accepted enums, defaults, and dependencies against the matching schema, parser, implementation, or official reference. Valid YAML/JSON can still be invalid application configuration.
- Verify API/schema versions, deprecated or removed fields, consumer versions, and template rendering context. Mark version-specific syntax as clear, unstated, or ambiguous; explain which check cannot be completed if the version is unknown.
- For templates, reason about template syntax and generated configuration from source without rendering or parsing examples. If the user explicitly authorizes such validation, document any placeholder substitutions and preserve the semantics being checked.
- Inspect duplicate-key behavior and format rules in the relevant specification or parser source; do not run a parser or linter without explicit execution instructions. If separately authorized, record the validator version and scope. A generic YAML or JSON validator is not suitable for a different configuration language.

## Code Examples

- Establish language, runtime and library/SDK versions, imports, required objects, inputs, credentials, and prior setup.
- Check language syntax and version availability of APIs, methods, arguments, return types, and exception behavior against appropriate primary evidence.
- Trace the example against its intended outcome, including variable definitions, data shapes, response handling, error paths essential to the example, resource lifecycle, and asynchronous behavior.
- Distinguish complete programs from fragments, pseudocode, and illustrative output. Do not require production-grade abstractions or unrelated error handling in a focused example.
- Base conclusions on documentation and code inspection. Do not run isolated or mock tests unless the user explicitly requests execution. For separately authorized execution, record inputs, environment, results, and limitations; do not infer production correctness from a mock test.

## Evidence and Finding Decisions

For every finding capture the documented claim/example, location, applicable version/environment, expected behavior supported by evidence, observed mismatch, operational consequence, and minimal correction. Cite the conflicting prose and command together where language affects meaning. Use technical categories such as sequence, command, package, environment, version, configuration, code, or meaning conflict.

Unstated versions are not automatically errors. If the syntax is version-independent across the stated supported range, no finding is necessary. If different plausible versions change the result, record the ambiguity, evidence for the differing behavior, and the version information needed. If behavior is not established, use the unresolved table rather than a confirmed defect. Suggestions must have a technical benefit, such as making an otherwise valid example reproducible; avoid stylistic rewrites.

Inventory checked sections/blocks in a compact coverage table or bullet list. Include skipped/unavailable checks and evidence gaps. Do not count each failed manifestation of one root cause as a separate major finding. Use the shared priority criteria and distinguish severity from confidence.
