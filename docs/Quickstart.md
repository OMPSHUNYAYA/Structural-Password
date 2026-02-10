# ⭐ Shunyaya Structural Password (SSP)

## Quickstart

**Deterministic • Replay-Verifiable • Structurally Exact**  
No Secrets • No Tolerance • No Probability

---

## What You Need to Know First

**Shunyaya Structural Password (SSP)** is intentionally strict and conservative.

It does **not** store passwords.  
It does **not** compare hashes.  
It does **not** use tolerance, timing windows, or probabilistic acceptance.

SSP verifies identity by requiring **exact reproduction of a deterministic structural traversal**.

This is **structural identity verification** — not credential matching.

---

## Requirements

- Python 3.9+ (CPython)
- Standard library only (no external dependencies)

Everything is:

- deterministic
- offline
- replay-verifiable
- byte-identical across machines

No randomness.  
No training.  
No simulation.  
No probabilistic heuristics.  
No adaptive tuning.

---

## Public Repository Layout (Authoritative)

The SSP public repository uses the following structure:

```
/
├── demo/
│   └── ssp_browser_demo.html
│
├── docs/
│   ├── Concept-Flyer_SSP_v1.8.pdf
│   ├── SSP_v1.8.pdf
│   ├── Worked_Live_Run__SSP.txt
│   ├── Quickstart.md
│
├── scripts/
│   └── ssp_demo_v0_3_0.py
│
└── outputs/
    ├── REPLAY_A__SSP_DEMO__V03__V03_PHASE3_RUN1/
    └── REPLAY_B__SSP_DEMO__V03__V03_PHASE3_RUN1/
```

---

## Design Intent

- Exactly **one** reference implementation
- Exactly **two** independent replays (A and B)
- No legacy scripts
- No tuning runs
- No experimental outputs

SSP is a **primitive and an open structural standard**, not a framework or benchmark suite.

---

## Important Design Note

SSP is **not** a single “check”.

SSP is a **deterministic protocol** that produces inspectable evidence artifacts:

- a canonical structural trace
- a deterministic trace signature
- a decision summary
- a cryptographic manifest

Independent replays must produce **byte-identical artifacts**.

If they do not, SSP has failed.

---

## What SSP Does (One-Minute Mental Model)

Traditional authentication asks:

- “Does this value match?”
- “Is it close enough?”
- “Is it recent?”

SSP asks instead:

- “Does structure unfold **exactly** the same way?”

Identity is not proven by possession.  
Identity is proven by **reproducibility**.

---

## Core Structural Idea (One Line)

**Identity is the ability to reproduce an exact structural path — not the ability to present a value.**

---

## Fundamental Invariant (Unchanged)

SSP preserves a strict collapse invariant:

`phi((m, a, s)) = m`

Where:

- `m` is the human input
- `a` is admissibility
- `s` is structural evolution

The input is **never transformed**.  
Verification occurs **only through structure**.

---

## Structural Identity Definition

Let:

- `T(m)` be the deterministic structural traversal for input `m`
- `sig(T(m))` be the deterministic trace signature

Decision rule:

**ACCEPT iff `sig(T(m')) = sig(T(m))`**

No tolerance.  
No thresholds.  
No similarity scoring.

---

## Authentication Outcomes (Complete Set)

SSP produces **exactly three outcomes**:

**ACCEPT**  
Exact structural reproduction under admissible posture

**REJECT**  
Structural trace diverges under admissible traversal

**ABSTAIN**  
Traversal is structurally inadmissible  
(e.g., posture or structural time mismatch)

No other outcomes exist.

**ABSTAIN is a deliberate refusal**, not error or indecision.

---

## Phase I — Correctness / Honesty (Quick Run)

From the project root:

```
python scripts/ssp_demo_v0_3_0.py --verify_replay
```

This execution performs:

- ENROLL
- AUTH_OK (same input)
- ATTACK (near input)

Expected behavior:

- ENROLL → OK
- AUTH_OK → ACCEPT
- ATTACK → REJECT

Replay A and Replay B must produce **byte-identical artifacts**.

---

## Phase II — Structural Depth & Structural Distance

Phase II extends identity from a single path into a **multi-layer structural object**.

Conceptual layers include:

- L0 — admissibility gates
- L1 — bounded evolution
- L2 — refusal / reroute posture
- L3 — closure / quiescence

Identity is accepted only if the **entire composed trace reproduces exactly**.

Structural distance is recorded for **audit only**, never for acceptance.

---

## Phase III — Structural Time Binding (SSP-T)

Phase III introduces **structural time**, not clock time.

Structural time:

- does not measure seconds
- does not rely on synchronization
- does not permit tolerance windows

Structural time participates **only in admissibility**.

Decision semantics remain unchanged:

- ACCEPT if trace matches and posture admissible
- REJECT if trace diverges
- ABSTAIN if posture inadmissible

Invariant remains:

`phi((m, a, s)) = m`

---

## Worked Live Run (Reference)

A complete executed proof demonstrating **ACCEPT / REJECT / ABSTAIN** with real signatures, replay fingerprints, and evidence bundles is provided separately.

See:

```
docs/Worked_Live_Run__SSP.txt
```

This document records an **actual SSP execution** and should be treated as an **audit-grade reference**, not a tutorial.

---

## Evidence Artifacts (What You Will See)

Each SSP run produces:

- `ssp_trace.csv` — canonical event stream
- `ssp_summary.txt` — decision and statistics
- `SSP_CONFIG.txt` — protocol configuration
- `MANIFEST.sha256` — integrity proof

Artifacts are designed for **human inspection and third-party replay**.

---

## What To Expect (Sanity Checks)

- Near inputs diverge immediately
- No “almost matches” exist
- Cross-posture attempts ABSTAIN deterministically
- Replay runs are byte-identical

If any of the above is not true, SSP is mis-implemented.

---

## What SSP Is Not

SSP does **not**:

- claim new cryptography
- replace encryption
- prevent hardware compromise
- predict adversarial behavior

SSP eliminates entire classes of failure **by construction**, not by threat modeling.

---

## One-Line Summary

**Shunyaya Structural Password proves identity by exact structural reproduction — not by secrets, similarity, or probability — and produces replay-verifiable evidence every time.**
