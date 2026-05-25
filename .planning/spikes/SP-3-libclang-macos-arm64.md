---
spike_id: SP-3
phase: 1
target: libclang==18.1.1 on macOS arm64 (Python 3.13/3.14)
policy: "D-22 緩和 — workflow setup + first run kick + provisional verdict"
status: verdict-recorded-ship-best-effort
---

# SP-3: libclang 18.1.1 on macOS arm64 + Python 3.13/3.14

**Spike ID:** SP-3
**Run date:** 2026-05-25 (first successful run after orchestrator hot-fix; see CI run URL section below)
**Phase 1 close condition (D-22 緩和版):** CI workflow setup 完了 + 最初の run 1 回 kick + 暫定 verdict 記録 — **すべて満たした (ship-best-effort)**

## 目的

`libclang==18.1.1` wheel が macOS arm64 (Apple Silicon) ランナーで Python 3.13 と 3.14 から正しく
利用できることを検証する。Phase 4 (LNG-02 — C++ frontend) のリスクプロファイル入力として、
ABI 互換性 (`.dylib` ロード)、`Config.library_path` 解決、最小 C++ ソースの parse 動作の 4 段階
ステップ (D-21) を実行する。

このスパイクは `continue-on-error: true` で構成されており、結果は PR マージをブロックしない (D-22)。
Phase 1 の close 条件は workflow setup + 1 回の run kick + 暫定 verdict 記録までであり、verdict
の RESULT は Phase 1 の close を block しない (Phase 4 入口で再評価)。

## Test matrix

| Python | macOS arm64 | (a) install | (b) dylib load | (c) library_path | (d) C++ parse | Verdict |
|--------|-------------|-------------|----------------|------------------|---------------|---------|
| 3.13 | macos-14 | ✓ | ✓ | ✓ | ✓ | ship-best-effort |
| 3.14 | macos-14 | ✓ | ✓ | ✓ | ✓ | ship-best-effort |

凡例: `?` = 未実行 (first CI run 後に確定)、`✓` = PASS、`✗` = FAIL。

### Per-step CI evidence (run 26406202099, jobs 77730010113 / 77730010138)

**Python 3.13 (job 77730010113 — 21s — ALL STEPS PASS):**
- (a) install: ✓ PASS — `libclang==18.1.1` installed via pip
- (b) `Index.create()`: ✓ PASS — log: `Index OK <clang.cindex.Index object at 0x1009dde80>`
- (c) `Config.library_path`: ✓ PASS — `/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/clang/native`
- (d) minimal C++ parse (`int main() { return 0; }`): ✓ PASS — `SP-3 (d) PASS - parsed 1 top-level cursors`

**Python 3.14 (job 77730010138 — 17s — ALL STEPS PASS):**
- (a) install: ✓ PASS — `libclang==18.1.1` installed via pip with `--allow-prereleases` (3.14 still pre-release at run time)
- (b) `Index.create()`: ✓ PASS — log: `Index OK <clang.cindex.Index object at 0x104d6fb60>`
- (c) `Config.library_path`: ✓ PASS — `/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/site-packages/clang/native`
- (d) minimal C++ parse: ✓ PASS — `SP-3 (d) PASS - parsed 1 top-level cursors`

A confirming subsequent run (`26406392965` on commit `0afdb7d` = current Wave 3 base) also shows all 3 jobs (`test` + `sp3-libclang-spike (3.13)` + `sp3-libclang-spike (3.14)`) green — the verdict is stable across at least two consecutive commits.

## Verdict legend (D-21)

D-21 で定義された 4 段階判定ルール:

- All (a)(b)(c)(d) ✓ → **ship-best-effort**
- (a)(b)(c) ✓ かつ (d) 限定的 failure → **ship-best-effort + known limitations** (README に open issue として既知制限を記載)
- (a) ✓ (b) ✗ → **defer to v0.3.0** (dylib load 失敗 = ABI 不整合)
- (a) ✗ → **defer to v0.3.0** (wheel 未配布)

## CI run URL

**First successful run (verdict source):** https://github.com/bibi-meow/lib-code-parser/actions/runs/26406202099

**Background note (Phase 1 hot-fix):** The initial run on commit `69c952e` failed
because `lib-diagram-parser>=0.1.0` (declared by Plan 01-01 in `pyproject.toml` as a hard
dependency) is not yet on PyPI — `pip install -e ".[dev]"` therefore failed at the
"Install with libclang pinned" step before SP-3 (b)(c)(d) could run. The orchestrator
hot-fixed this in commit `53688ca` (`fix(01-01): remove lib-diagram-parser from hard
deps (defer to Phase 3 DIA-04)`) per Plan 01-05 OQ#5 + Plan 01-10 D-22 scope, and
re-triggered the workflow. The re-run (`26406202099`) completed all 4 SP-3 steps
successfully on both Python 3.13 and 3.14.

**Confirming run on Wave 3 base commit `0afdb7d`:** https://github.com/bibi-meow/lib-code-parser/actions/runs/26406392965
(also all-green — `test` + `sp3-libclang-spike (3.13)` + `sp3-libclang-spike (3.14)`).

## Re-evaluation

Phase 4 入口で再確認 (D-22)。If verdict was provisional or defer, plan-phase for Phase 4
re-runs the spike with current macos-14 image and updates this table.

## Provisional verdict

**Provisional verdict: ship-best-effort** (Phase 4 will mark macOS arm64 as best-effort CI per LNG-02)

**D-21 tier applied:** All 4 verification steps (a)(b)(c)(d) PASS on BOTH Python 3.13
AND Python 3.14 on `macos-14` (Apple Silicon arm64). Per the D-21 verdict legend, this
matches the **"All (a)(b)(c)(d) ✓ → ship-best-effort"** tier (the strongest of the
4 tiers; no known limitations to document).

**Rationale for Phase 4 (LNG-02):** Phase 4 can proceed with `libclang==18.1.1` as the
C++ frontend dependency choice without further investigation. The macOS arm64 +
Python 3.13/3.14 combination is supported with stable wheels — no fall-back to a
different libclang version is needed. The job remains `continue-on-error: true` in
Phase 1 per D-22 (does not block PR merges); Phase 4 LNG-01 will graduate it to a
mandatory matrix entry alongside the Linux + Windows mandatory matrices.

**Stability evidence:** Two consecutive CI runs on two different commits (`69c952e`
re-run after hot-fix → run `26406202099`; `0afdb7d` → run `26406392965`) both
green for all 3 jobs — the verdict is not a single-run fluke.

---

Last updated by Plan 10 Task 4 on 2026-05-25 (continuation agent after orchestrator
hot-fix of `lib-diagram-parser` hard dep in commit `53688ca`).
