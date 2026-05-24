---
spike_id: SP-3
phase: 1
target: libclang==18.1.1 on macOS arm64 (Python 3.13/3.14)
policy: "D-22 緩和 — workflow setup + first run kick + provisional verdict"
status: pending-first-run
---

# SP-3: libclang 18.1.1 on macOS arm64 + Python 3.13/3.14

**Spike ID:** SP-3
**Run date:** TBD (Phase 1 commit landing + first CI run)
**Phase 1 close condition (D-22 緩和版):** CI workflow setup 完了 + 最初の run 1 回 kick + 暫定 verdict 記録

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
| 3.13 | macos-14 | ? | ? | ? | ? | TBD |
| 3.14 | macos-14 | ? | ? | ? | ? | TBD |

凡例: `?` = 未実行 (first CI run 後に確定)、`✓` = PASS、`✗` = FAIL。

## Verdict legend (D-21)

D-21 で定義された 4 段階判定ルール:

- All (a)(b)(c)(d) ✓ → **ship-best-effort**
- (a)(b)(c) ✓ かつ (d) 限定的 failure → **ship-best-effort + known limitations** (README に open issue として既知制限を記載)
- (a) ✓ (b) ✗ → **defer to v0.3.0** (dylib load 失敗 = ABI 不整合)
- (a) ✗ → **defer to v0.3.0** (wheel 未配布)

## CI run URL

TBD — first run URL recorded after Phase 1 commit lands on the default branch and the
sp3-libclang-spike job runs on GitHub Actions.

## Re-evaluation

Phase 4 入口で再確認 (D-22)。If verdict was provisional or defer, plan-phase for Phase 4
re-runs the spike with current macos-14 image and updates this table.

## Provisional verdict

TBD — to be filled after Task 4 records the first CI run results (Phase 1 Plan 10 Task 3
checkpoint で user が CI run の (a)(b)(c)(d) 結果を Claude に報告した時点で、Task 4 が
D-21 の 4 段階判定を適用してこの欄を埋める)。
