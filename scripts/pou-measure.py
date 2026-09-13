#!/usr/bin/env python3
"""Production measurement for the Tier-3 leveling system (VPS-ready).

Measures what the virtual harness cannot:
1. Cold-prompt identity cost with the REAL ~/.hermes/SOUL.md:
   full dump vs compact pointer + JIT recall (chars + estimated tokens).
2. Live ledger standing from ~/.hermes/cognitive_state.db
   (level, energy, gates, idle projection, recent causes).

Usage:
    python3 scripts/pou-measure.py [--json] [--hermes-home PATH]

No LLM calls, no network, read-only except a TEMPORARY substrate copy used
to measure JIT recall without touching production state.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys
import tempfile

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _tok(chars: int) -> float:
    return chars / 4.0


def measure_identity(home: pathlib.Path) -> dict:
    from agent.tier3_cognitive_core import (
        DynamicSoulMemorySubstrate,
        compact_identity_pointer,
    )

    soul_path = home / "SOUL.md"
    soul_text = soul_path.read_text(encoding="utf-8") if soul_path.exists() else ""
    dump_chars = len(soul_text) if soul_text else 20000
    if not soul_text:
        soul_text = ("# Identity\nBe concise.\n" * 1500)[:20000]  # synthetic cap-size soul

    work = pathlib.Path(tempfile.mkdtemp(prefix="pou-measure-"))
    try:
        sub = DynamicSoulMemorySubstrate(db_path=work / "m.db")
        chunks = sub.ensure_soul_seeded(soul_text)
        probe = " ".join(soul_text.split()[:40])
        recalled = sub.query_relevant_soul_memory(probe, limit=4)
        jit_chars = sum(len(r) for r in recalled)
        pointer_chars = len(compact_identity_pointer(chunks))
    finally:
        shutil.rmtree(work, ignore_errors=True)

    realistic_chars = pointer_chars + jit_chars
    return {
        "soul_source": "real" if soul_path.exists() else "synthetic-20k",
        "dump_chars": dump_chars,
        "dump_tokens_est": round(_tok(dump_chars), 1),
        "pointer_chars": pointer_chars,
        "jit_chars": jit_chars,
        "compact_total_chars": realistic_chars,
        "compact_total_tokens_est": round(_tok(realistic_chars), 1),
        "pointer_only_ratio": round(dump_chars / max(1, pointer_chars), 1),
        "realistic_ratio": round(_tok(dump_chars) / max(0.1, _tok(realistic_chars)), 1),
        "chunks": chunks,
        "recalled_partitions": len(recalled),
    }


def measure_ledger(home: pathlib.Path) -> dict:
    from agent.tier3_cognitive_core import pou_status, pou_why

    import os

    os.environ["HERMES_HOME"] = str(home)
    st = pou_status()
    return {
        "turns": st["turns"],
        "level": st["level"],
        "energy": round(st["energy"], 1),
        "effective_energy": round(st.get("effective_energy", st["energy"]), 1),
        "next_target": round(st["next_target"], 1),
        "progress_pct": round(st["progress_pct"], 1),
        "hci": st["hci"],
        "idle_days": round(st.get("idle_days", 0.0), 1),
        "gates": st.get("gates"),
        "last_cause": st["last_cause"],
        "recent_why": pou_why(limit=5),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Measure Tier-3 leveling production state")
    ap.add_argument("--json", action="store_true", help="Machine-readable output")
    ap.add_argument("--hermes-home", default=None, help="Override HERMES_HOME")
    args = ap.parse_args()

    import os

    home = pathlib.Path(args.hermes_home or os.getenv("HERMES_HOME", pathlib.Path.home() / ".hermes"))
    report = {
        "hermes_home": str(home),
        "identity": measure_identity(home),
        "ledger": measure_ledger(home),
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        ident, led = report["identity"], report["ledger"]
        print(f"HERMES_HOME : {report['hermes_home']}")
        print(f"Identity    : source={ident['soul_source']} dump={ident['dump_tokens_est']}tok "
              f"compact={ident['compact_total_tokens_est']}tok "
              f"ratio={ident['realistic_ratio']}x (pointer-only {ident['pointer_only_ratio']}x)")
        print(f"Ledger      : L{led['level']} E={led['energy']} eff={led['effective_energy']} "
              f"/T={led['next_target']} turns={led['turns']} idle={led['idle_days']}d")
        print(f"Gates       : {led['gates']}")
        print(f"Last cause  : {led['last_cause']}")
        for line in led["recent_why"]:
            print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
