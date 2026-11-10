# Faultline Methodology

Faultline combines several established techniques because each has a different blind spot:

- **Pre-mortem** helps surface hidden assumptions and plausible organizational, user, and operational failure causes.
- **FMEA/FMECA** makes failure modes explicit by tracing causes and effects through components and operations.
- **STRIDE** gives security review a structured vocabulary around trust boundaries and data flows.
- **State/invariant analysis** exposes illegal transitions, race conditions, duplicate effects, and recovery inconsistencies.
- **Fault-tree/failure-chain reasoning** exposes combinations of failures that produce a larger incident.
- **STPA-inspired analysis** is reserved for systems where control actions, feedback, timing, and unsafe coordination matter.
- **Boundary/property-based thinking** turns broad input spaces into equivalence classes, invariants, and generated-test candidates.

The workflow does not mechanically run every method on every feature. It records applicability and evidence. This is important: broad checklists improve coverage only when the analyst ties them to actual components, paths, state, and consequences.

## Why not use one numeric RPN as the answer?

A simple product of ordinal severity, occurrence, and detection scores can hide important differences and imply more numerical precision than the evidence supports. Faultline uses a qualitative severity/likelihood matrix, confidence, and separate notes for detection, reversibility, and blast radius. A team can add quantitative risk data when it has real incident or operational measurements.

## Analysis is not verification

The preflight is a hypothesis-generation and design-review process. A scenario becomes stronger when it is grounded in code, requirements, architecture, incident data, provider contracts, or a reproducible test. Property-based tests, mutation testing, integration tests, security testing, and controlled fault injection are later verification mechanisms—not things a prompt can substitute for.
