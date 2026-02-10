## Reference vs Demo Input Representation

The **Python SSP demo** uses **numeric input** (`m` as an integer) to support:

- strict offline execution
- deterministic replay
- byte-identical artifacts
- audit-grade verification

The **browser SSP demo** accepts **string input** for **conceptual clarity** and
interactive demonstration.

This difference is **intentional** and does **not** affect SSP semantics.

---

### Structural Consistency (Unchanged)

In all cases:

- the invariant `phi((m, a, s)) = m` is preserved
- acceptance remains `ACCEPT iff sig(T(m')) = sig(T(m))`
- no tolerance, probability, or approximation is introduced

---

### Why This Distinction Exists

Numeric input in the Python demo ensures:

- stable canonical serialization
- deterministic traversal across machines
- reproducible cryptographic manifests

String input in the browser demo ensures:

- human-readable interaction
- conceptual accessibility
- illustrative walkthrough of SSP behavior

---

### Important Note

Both demos **faithfully implement the same SSP structural rules**.

Differences in input representation exist **only for demonstration and usability**,
not for correctness, acceptance semantics, or conformance.

Structural behavior — not input format — defines identity in SSP.
