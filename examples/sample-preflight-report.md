# Faultline Preflight — payment-retry

- **Date:** 2026-11-10
- **Repository revision:** fixture
- **Working-tree state:** clean fixture
- **Mode:** brownfield-preflight
- **Analyst:** AI-assisted test fixture

## Executive summary

A representative duplicate-payment risk is recorded for validator testing.

## Scope and success conditions

### Intended outcome
One logical payment creates one charge and one order state.

### Affected actors
Customer, API service, payment provider, support operator.

### In scope / out of scope
In scope: retry after ambiguous provider response. Out of scope: provider implementation.

### Success conditions and invariants
One idempotency identity maps to one logical payment outcome.

## Reconnaissance and system map

### Repository structure and entry points
`POST /payments` is the assumed entry point in this fixture.

### Runtime/process model
HTTP request process.

### Components and dependencies
API, database and payment provider.

### Data stores, schemas and transactions
Orders and payment records.

### State machines and invariants
Pending → authorized → captured/failed.

### Trust boundaries and permissions
Authenticated customer to payment service.

### Build, tests, CI/CD and deployment
Fixture only.

### Observability, backup and recovery
Provider reconciliation is a proposed control.

### Unknown or uninspected areas
This is a validator fixture, not production evidence.

## Code-path and change-impact analysis

| Operation/entry point | Path traced | Side effects | Existing contract | Affected consumers | Test coverage |
|---|---|---|---|---|---|
| POST /payments | API → provider → DB | Charge and order update | One logical payment | Customer | Proposed |

## Evidence, assumptions, and unknowns

| ID | Statement | Type (Observed / Assumed / Hypothesis) | Evidence | Impact if wrong |
|---|---|---|---|---|
| E-001 | Provider may capture before local commit | Hypothesis | Distributed side effect | Duplicate charge |

## Coverage matrix

| Layer/domain | Status (covered / not-applicable / not-assessed) | Inspected evidence or reason |
|---|---|---|
| Runtime | covered | Fixture flow |
| Security | not-assessed | Outside fixture scope |

## Risk register

### FL-001 — Duplicate charge after ambiguous response

- **Status:** POSSIBLE
- **Evidence level:** HYPOTHESIS
- **Priority:** High
- **Severity:** High
- **Likelihood:** Possible
- **Confidence:** Medium
- **Disposition:** mitigate
- **Domain:** Dependency and network; recovery and reversibility
- **Components/paths:** `POST /payments` → provider capture → local persistence
- **Evidence:** Provider capture and local commit are separate side effects in the fixture assumption.
- **Preconditions:** Provider captures funds but response is lost before local state is committed.
- **Trigger:** Client retries the same logical payment after timeout.
- **Failure sequence:** Provider captures first request; response is lost; API state remains pending; retry causes another capture.
- **Expected behavior:** Repeated request resolves to the same logical payment and never creates a second charge.
- **Observed behavior:** not executed; scenario is hypothetical.
- **Impact:** Customer charged twice and reconciliation required.
- **Detection/recovery:** Provider event reconciliation and payment ledger alert.
- **Mitigation:** Durable idempotency key and provider-side idempotency where supported.
- **Reproduction/test:** Proposed integration test with simulated lost response; not executed.
- **Acceptance test:**
  - **Given** a provider capture succeeds but its response is lost before local confirmation
  - **When** the client retries the same logical payment operation with the same idempotency key
  - **Then** no second charge is created and the system converges to one auditable payment/order state

## Failure chains and pre-mortem

### Failure chain 1

- **Unwanted outcome:** Customer is charged twice.
- **Contributing events (AND/OR):** Provider success AND response loss AND non-idempotent retry.
- **Earliest preventable decision:** Define idempotency across provider and local persistence.
- **Warning signal:** Multiple provider captures for one logical order.
- **Mitigation:** Durable idempotency and reconciliation.

## Break attempts and test results

| Check/test | Command or method | Safety class | Executed? | Result | Finding IDs |
|---|---|---|---|---|---|
| Retry sequence analysis | Manual trace | Read-only | Yes | Hypothesis only | FL-001 |

## Specialist review provenance

| Role | Host subagent / sequential pass | Scope | Result | Limitations |
|---|---|---|---|---|
| runtime-breaker | Sequential pass | Payment retry | One hypothesis | Not independently reproduced |

## Proposed requirements and scenarios

| Requirement ID | Requirement / invariant | Source risk IDs | Given/When/Then | Verification method |
|---|---|---|---|---|
| PAY-001 | One logical payment must not capture twice | FL-001 | See acceptance test | Integration test |

## Decisions required before specification

| Decision | Options | Recommendation | Risk IDs | Owner / status |
|---|---|---|---|---|
| Idempotency ownership | Provider / local / both | Both where supported | FL-001 | Open |

## Limitations

- Files/subsystems not inspected: fixture only.
- Missing evidence: actual provider contract.
- Commands/tests not run and why: no test harness in fixture.
- Scenarios not validated: provider failure semantics.
- Subagent limitations: sequential pass only.
- Analysis limitations and next steps: use a provider sandbox integration test.
