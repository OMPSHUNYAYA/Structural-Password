#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSP Demo v0.3.0 — Phase III (SSP-T: Structural Time Binding)
Deterministic, replay-verifiable structural authentication with posture binding.

Core invariant (preserved):
  phi((m, a, s)) = m

Phase III rule implemented:
  - ENROLL at posture p0
  - AUTH_OK at posture p0 => ACCEPT (exact trace signature match)
  - AUTH_CROSS at posture p1 => ABSTAIN (posture inadmissible vs enrolled posture)
  - ATTACK deltas at posture p0 => REJECT (trace signature mismatch)
  - ATTACK deltas at posture p1 => ABSTAIN (posture inadmissible)

Hard guarantees:
  - No randomness
  - Deterministic artifacts (CSV/TXT/CONFIG/MANIFEST)
  - --verify_replay produces byte-identical outputs across REPLAY_A and REPLAY_B
"""

import argparse
import csv
import hashlib
import os
import shutil
import sys
from typing import Dict, List, Tuple


VERSION = "v0.3.0"
ENGINE_TAG = "SSP_DEMO__V03"


# ----------------------------
# Utilities
# ----------------------------

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def rm_tree(path: str) -> None:
    if os.path.isdir(path):
        shutil.rmtree(path)


def write_text(path: str, text: str) -> None:
    # Force stable newlines and encoding
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def write_csv(path: str, header: List[str], rows: List[List[str]]) -> None:
    # Force stable CSV output across platforms:
    # - newline="\n"
    # - lineterminator="\n"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def stable_relpaths(root: str) -> List[str]:
    rels: List[str] = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace("\\", "/")
            rels.append(rel)
    rels.sort()
    return rels


def compare_trees(a_root: str, b_root: str) -> Tuple[bool, str]:
    a_files = stable_relpaths(a_root)
    b_files = stable_relpaths(b_root)
    if a_files != b_files:
        return False, "file list mismatch"

    for rel in a_files:
        ap = os.path.join(a_root, rel.replace("/", os.sep))
        bp = os.path.join(b_root, rel.replace("/", os.sep))
        with open(ap, "rb") as fa:
            ab = fa.read()
        with open(bp, "rb") as fb:
            bb = fb.read()
        if ab != bb:
            return False, f"byte mismatch at {rel}"
    return True, ""


# ----------------------------
# Structural posture (SSP-T)
# ----------------------------

def posture_signature(posture_id: int, modulus: int = 1000003) -> str:
    # Deterministic posture signature (not wall-clock, not OTP).
    payload = f"SSP_T|p={posture_id}|mod={modulus}".encode("utf-8")
    return sha256_bytes(payload)


def posture_salt(posture_sig: str) -> int:
    # Deterministic salt from signature prefix
    return int(posture_sig[:16], 16)


# ----------------------------
# Deterministic traversal engine
# ----------------------------

def traverse(m: int, horizon_steps: int, salt: int) -> Tuple[List[List[str]], Dict[str, int]]:
    """
    Deterministic multi-layer traversal producing a canonical event stream.

    Output:
      - rows for ssp_trace.csv
      - stats dict
    """
    # Multi-layer state
    x = (m ^ salt) & 0x7FFFFFFF
    s0 = (m + (salt & 0xFFFF)) & 0xFFFFFFFF
    s1 = (m * 1315423911 + salt) & 0xFFFFFFFF
    s2 = (m ^ (salt >> 3)) & 0xFFFFFFFF
    s3 = (m + (salt >> 7)) & 0xFFFFFFFF

    counts: Dict[str, int] = {}
    rows: List[List[str]] = []

    def emit(step: int, layer: str, event: str, gate: str) -> None:
        key = f"{layer}:{event}"
        counts[key] = counts.get(key, 0) + 1
        # Keep x visible for audit (still deterministic)
        rows.append([str(step), layer, event, str(x), gate])

    # Deterministic gates
    def gate_pass(name: str, v: int, mod: int, target: int) -> bool:
        return (v % mod) == target

    for step in range(horizon_steps):
        # Layer 0: admissibility gates
        g0_ok = gate_pass("G0", s0 + x + step, 17, 0) or gate_pass("G0b", s0 ^ x, 19, 1)
        if g0_ok:
            emit(step, "L0", "GATE_PASS", "G0_OK")
        else:
            emit(step, "L0", "GATE_HOLD", "G0_HOLD")

        # Layer 1: bounded evolution loop
        # deterministic update
        x = (x * 1103515245 + 12345 + (salt & 0xFFFF) + step) & 0x7FFFFFFF
        s1 = (s1 + (x ^ (step * 2654435761 & 0xFFFFFFFF))) & 0xFFFFFFFF
        if gate_pass("L1", s1 + x, 29, 0):
            emit(step, "L1", "STEP_ACCEL", "L1_A")
        else:
            emit(step, "L1", "STEP_NORM", "L1_N")

        # Layer 2: refusal / reroute posture (collapse-capable)
        # collapse witness: when a deterministic condition hits, emit refusal markers
        s2 = (s2 ^ (x >> 5) ^ (salt & 0xFFFFFFFF) ^ step) & 0xFFFFFFFF
        if gate_pass("L2", s2, 31, 7):
            emit(step, "L2", "REFUSAL", "L2_R")
            # deterministic reroute: adjust x/s0 to simulate structural reroute
            x = (x ^ (s2 & 0xFFFF) ^ 0xA5A5) & 0x7FFFFFFF
            s0 = (s0 + 97 + (x & 0xFF)) & 0xFFFFFFFF
            emit(step, "L2", "REROUTE", "L2_RR")
        else:
            emit(step, "L2", "FLOW", "L2_F")

        # Layer 3: closure posture
        s3 = (s3 + (x & 0xFFFF) + (salt >> 11) + step) & 0xFFFFFFFF
        if gate_pass("L3", s3 ^ x, 23, 5):
            emit(step, "L3", "EXIT", "L3_E")
            # Deterministic early closure (bounded)
            break
        else:
            emit(step, "L3", "KEEP", "L3_K")

    # Stats
    stats = {
        "steps_executed": (int(rows[-1][0]) + 1) if rows else 0,
        "events_total": len(rows),
    }
    # Layer counts
    for k, v in counts.items():
        stats[f"count_{k}"] = v

    return rows, stats


def trace_signature(rows: List[List[str]]) -> str:
    # Canonical serialization (stable)
    # Exclude CSV header. Join by '\n' with '|' separators.
    lines = []
    for r in rows:
        lines.append("|".join(r))
    blob = ("\n".join(lines) + "\n").encode("utf-8")
    return sha256_bytes(blob)


def distance_metrics(expected_rows: List[List[str]], actual_rows: List[List[str]]) -> Dict[str, int]:
    # Deterministic audit-only metrics (not used for thresholds)
    exp_len = len(expected_rows)
    act_len = len(actual_rows)
    overlap = min(exp_len, act_len)

    first_div = 0
    div_in_overlap = 0
    found_first = False

    # Event-type histogram L1 distance (counts over "layer:event")
    def hist(rows: List[List[str]]) -> Dict[str, int]:
        h: Dict[str, int] = {}
        for r in rows:
            key = f"{r[1]}:{r[2]}"
            h[key] = h.get(key, 0) + 1
        return h

    eh = hist(expected_rows)
    ah = hist(actual_rows)
    keys = sorted(set(eh.keys()) | set(ah.keys()))
    l1 = 0
    for k in keys:
        l1 += abs(eh.get(k, 0) - ah.get(k, 0))

    for i in range(overlap):
        if expected_rows[i] != actual_rows[i]:
            div_in_overlap += 1
            if not found_first:
                first_div = i + 1  # 1-based
                found_first = True

    if not found_first:
        first_div = 0

    return {
        "first_div_step": first_div,
        "event_divergences_in_overlap": div_in_overlap,
        "hist_l1_delta": l1,
        "expected_events": exp_len,
        "actual_events": act_len,
        "length_delta": act_len - exp_len,
    }


# ----------------------------
# Run construction
# ----------------------------

def build_config_text(mode: str,
                      m: int,
                      horizon_steps: int,
                      posture_id: int,
                      posture_sig: str,
                      salt: int,
                      tag: str,
                      decision: str,
                      reason: str) -> str:
    return (
        f"SSP Demo {VERSION}\n"
        f"engine={ENGINE_TAG}\n"
        f"mode={mode}\n"
        f"tag={tag}\n"
        f"m={m}\n"
        f"horizon_steps={horizon_steps}\n"
        f"posture_id={posture_id}\n"
        f"posture_sig={posture_sig}\n"
        f"posture_salt_int={salt}\n"
        f"decision={decision}\n"
        f"reason={reason}\n"
    )


def write_manifest(folder: str, files: List[str]) -> None:
    # Manifest should be stable and not include itself.
    lines = []
    for fn in sorted(files):
        p = os.path.join(folder, fn)
        h = sha256_file(p)
        lines.append(f"{h}  {fn}")
    write_text(os.path.join(folder, "MANIFEST.sha256"), "\n".join(lines) + "\n")


def run_case(out_dir: str,
             case_name: str,
             mode: str,
             m: int,
             horizon_steps: int,
             posture_id: int,
             tag: str,
             expected_posture_sig: str,
             expected_sig: str,
             expected_rows: List[List[str]]) -> Tuple[str, str, Dict[str, int], Dict[str, int]]:
    """
    Executes one case folder with deterministic artifacts.
    Returns (decision, actual_sig, stats, dist)
    """
    case_dir = os.path.join(out_dir, case_name)
    ensure_dir(case_dir)

    psig = posture_signature(posture_id)
    salt = posture_salt(psig)

    # Posture admissibility: must match enrolled posture signature
    if psig != expected_posture_sig:
        decision = "ABSTAIN"
        reason = "POSTURE_MISMATCH_INADMISSIBLE"
        # Still produce deterministic minimal artifacts
        rows, stats = traverse(m, horizon_steps, salt)
        act_sig = trace_signature(rows)

        header = ["step", "layer", "event", "x", "gate"]
        write_csv(os.path.join(case_dir, "ssp_trace.csv"), header, rows)

        dist = distance_metrics(expected_rows, rows) if expected_rows else {
            "first_div_step": 0, "event_divergences_in_overlap": 0, "hist_l1_delta": 0,
            "expected_events": 0, "actual_events": len(rows), "length_delta": len(rows)
        }

        summary = []
        summary.append(f"SSP Demo {VERSION} — {case_name}")
        summary.append(f"decision = {decision}")
        summary.append(f"reason = {reason}")
        summary.append(f"m = {m}")
        summary.append(f"horizon_steps = {horizon_steps}")
        summary.append(f"posture_id = {posture_id}")
        summary.append(f"posture_sig = {psig}")
        summary.append(f"expected_posture_sig = {expected_posture_sig}")
        summary.append(f"expected_sig = {expected_sig}")
        summary.append(f"actual_sig = {act_sig}")
        summary.append("")
        summary.append("audit_distance_metrics (not used for acceptance):")
        for k in ["first_div_step", "event_divergences_in_overlap", "hist_l1_delta",
                  "expected_events", "actual_events", "length_delta"]:
            summary.append(f"{k} = {dist[k]}")
        summary.append("")
        summary.append("trace_stats:")
        summary.append(f"events_total = {stats['events_total']}")
        summary.append(f"steps_executed = {stats['steps_executed']}")
        write_text(os.path.join(case_dir, "ssp_summary.txt"), "\n".join(summary) + "\n")

        cfg = build_config_text(mode, m, horizon_steps, posture_id, psig, salt, tag, decision, reason)
        write_text(os.path.join(case_dir, "SSP_CONFIG.txt"), cfg)

        write_manifest(case_dir, ["ssp_trace.csv", "ssp_summary.txt", "SSP_CONFIG.txt"])
        return decision, act_sig, stats, dist

    # Admissible posture -> decision by exact signature match
    rows, stats = traverse(m, horizon_steps, salt)
    act_sig = trace_signature(rows)

    if expected_sig == "":
        # enrollment case: record expected signature deterministically
        decision = "OK"
        reason = "ENROLL_RECORDED"
    else:
        if act_sig == expected_sig:
            decision = "ACCEPT"
            reason = "EXACT_TRACE_MATCH"
        else:
            decision = "REJECT"
            reason = "TRACE_MISMATCH"

    header = ["step", "layer", "event", "x", "gate"]
    write_csv(os.path.join(case_dir, "ssp_trace.csv"), header, rows)

    dist = distance_metrics(expected_rows, rows) if expected_rows else {
        "first_div_step": 0, "event_divergences_in_overlap": 0, "hist_l1_delta": 0,
        "expected_events": 0, "actual_events": len(rows), "length_delta": len(rows)
    }

    summary = []
    summary.append(f"SSP Demo {VERSION} — {case_name}")
    summary.append(f"decision = {decision}")
    summary.append(f"reason = {reason}")
    summary.append(f"m = {m}")
    summary.append(f"horizon_steps = {horizon_steps}")
    summary.append(f"posture_id = {posture_id}")
    summary.append(f"posture_sig = {psig}")
    summary.append(f"expected_posture_sig = {expected_posture_sig}")
    summary.append(f"expected_sig = {expected_sig}")
    summary.append(f"actual_sig = {act_sig}")
    summary.append("")
    summary.append("audit_distance_metrics (not used for acceptance):")
    for k in ["first_div_step", "event_divergences_in_overlap", "hist_l1_delta",
              "expected_events", "actual_events", "length_delta"]:
        summary.append(f"{k} = {dist[k]}")
    summary.append("")
    summary.append("trace_stats:")
    summary.append(f"events_total = {stats['events_total']}")
    summary.append(f"steps_executed = {stats['steps_executed']}")
    write_text(os.path.join(case_dir, "ssp_summary.txt"), "\n".join(summary) + "\n")

    cfg = build_config_text(mode, m, horizon_steps, posture_id, psig, salt, tag, decision, reason)
    write_text(os.path.join(case_dir, "SSP_CONFIG.txt"), cfg)

    write_manifest(case_dir, ["ssp_trace.csv", "ssp_summary.txt", "SSP_CONFIG.txt"])
    return decision, act_sig, stats, dist


def run_demo(out_dir: str,
             m: int,
             horizon_steps: int,
             postures: List[int],
             attack_deltas: List[int],
             tag: str) -> None:
    ensure_dir(out_dir)

    # Phase III demo contract:
    # - enroll at postures[0]
    # - auth_ok at postures[0]
    # - auth_cross at postures[1] (if provided) using same m (ABSTAIN expected)
    p0 = postures[0]
    p1 = postures[1] if len(postures) > 1 else (postures[0] + 1)

    enrolled_posture_sig = posture_signature(p0)
    enrolled_salt = posture_salt(enrolled_posture_sig)

    # Compute enrollment trace deterministically
    enroll_rows, _ = traverse(m, horizon_steps, enrolled_salt)
    expected_sig = trace_signature(enroll_rows)

    # ENROLL
    run_case(
        out_dir=out_dir,
        case_name="ENROLL",
        mode="demo",
        m=m,
        horizon_steps=horizon_steps,
        posture_id=p0,
        tag=tag,
        expected_posture_sig=enrolled_posture_sig,
        expected_sig="",
        expected_rows=[]
    )

    # AUTH_OK (same posture)
    run_case(
        out_dir=out_dir,
        case_name="AUTH_OK",
        mode="demo",
        m=m,
        horizon_steps=horizon_steps,
        posture_id=p0,
        tag=tag,
        expected_posture_sig=enrolled_posture_sig,
        expected_sig=expected_sig,
        expected_rows=enroll_rows
    )

    # AUTH_CROSS (different posture, same m) -> ABSTAIN expected
    run_case(
        out_dir=out_dir,
        case_name=f"AUTH_CROSS_P{p1}",
        mode="demo",
        m=m,
        horizon_steps=horizon_steps,
        posture_id=p1,
        tag=tag,
        expected_posture_sig=enrolled_posture_sig,
        expected_sig=expected_sig,
        expected_rows=enroll_rows
    )

    # Attacks (posture p0 and p1)
    for d in attack_deltas:
        if d == 0:
            continue
        mm = m + d
        name = f"ATTACK_M{'PLUS' if d > 0 else 'MINUS'}{abs(d)}_P{p0}"
        run_case(
            out_dir=out_dir,
            case_name=name,
            mode="demo",
            m=mm,
            horizon_steps=horizon_steps,
            posture_id=p0,
            tag=tag,
            expected_posture_sig=enrolled_posture_sig,
            expected_sig=expected_sig,
            expected_rows=enroll_rows
        )

        name2 = f"ATTACK_M{'PLUS' if d > 0 else 'MINUS'}{abs(d)}_P{p1}"
        run_case(
            out_dir=out_dir,
            case_name=name2,
            mode="demo",
            m=mm,
            horizon_steps=horizon_steps,
            posture_id=p1,
            tag=tag,
            expected_posture_sig=enrolled_posture_sig,
            expected_sig=expected_sig,
            expected_rows=enroll_rows
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["demo"], default="demo")
    ap.add_argument("--m", type=int, required=True)
    ap.add_argument("--horizon_steps", type=int, default=128)
    ap.add_argument("--postures", type=int, nargs="+", default=[0, 1])
    ap.add_argument("--attack_deltas", type=int, nargs="*", default=[1, -1])
    ap.add_argument("--tag", type=str, default="V03_DEMO")
    ap.add_argument("--out_root", type=str, default=os.path.join("outputs", "ssp_out"))
    ap.add_argument("--verify_replay", action="store_true")
    args = ap.parse_args()

    tag = args.tag.strip()
    if not tag:
        print("ERROR: empty --tag", file=sys.stderr)
        return 2

    out_root = args.out_root
    ensure_dir(out_root)

    if args.verify_replay:
        a_dir = os.path.join(out_root, f"REPLAY_A__{ENGINE_TAG}__{tag}")
        b_dir = os.path.join(out_root, f"REPLAY_B__{ENGINE_TAG}__{tag}")

        rm_tree(a_dir)
        rm_tree(b_dir)

        run_demo(a_dir, args.m, args.horizon_steps, args.postures, args.attack_deltas, tag)
        run_demo(b_dir, args.m, args.horizon_steps, args.postures, args.attack_deltas, tag)

        ok, why = compare_trees(a_dir, b_dir)
        if not ok:
            print(f"VERIFY_REPLAY: FAIL ({why})")
            return 1

        print("VERIFY_REPLAY: PASS (all CSV/TXT/CONFIG/MANIFEST outputs byte-identical)")
        print(f"OK: SSP demo {VERSION} complete")
        print(f"Output folder: {out_root}")
        return 0

    # Non-replay mode (timestamped)
    # (Not used for formal evidence; provided for convenience)
    import datetime
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(out_root, f"{ts}__{ENGINE_TAG}__{tag}")
    rm_tree(run_dir)
    run_demo(run_dir, args.m, args.horizon_steps, args.postures, args.attack_deltas, tag)

    print(f"OK: SSP demo {VERSION} complete")
    print(f"Output folder: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
