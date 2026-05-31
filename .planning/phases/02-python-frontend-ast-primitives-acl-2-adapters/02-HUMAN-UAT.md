---
status: resolved
phase: 02-python-frontend-ast-primitives-acl-2-adapters
source: [02-VERIFICATION.md, 02-REVIEW.md]
started: 2026-05-31T00:00:00Z
updated: 2026-05-31T00:00:00Z
---

## Current Test

[resolved — CR-01 fixed via resolve_imports gate (Option B), plan 02-08]

## Tests

### 1. CR-01 — type_deps の pyright subprocess を opt-in ゲートにするか

expected: `type_deps.extract()` の import 解決方針が PROJECT.md の HARD constraint「出力は `(raw_content, path, config)` の純粋関数」「決定論性 (Layer M bisimulation の前提)」と整合する形に確定していること。

現状: `type_deps.extract()` は pyright subprocess を**常時**起動して `resolved` flag を導出する。`config.resolve_imports` のような opt-in ゲートがないため、pyright 未インストール環境では `execute()` 全体が `RuntimeError` で hard-fail する。CONTEXT.md D-06 は「fail loudly = 意図的設計」と記録しているが、デフォルトで外部ツール依存・環境依存・hard-fail を持ち込むことが Core Value (決定論) と整合するかはポリシー判断 = 人間決定事項 (contract-level)。

選択肢:
- (A) 現状承認 — D-06 fail-loudly + `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` 固定で「条件付き決定論」として受け入れる。コード変更なし。
- (B) Fix (gap closure) — `ParserConfig` に `resolve_imports: bool = False` を追加し、未設定時は pyright を起動せず AST-only で `resolved=True` 既定を返す。CR-01 / verifier 両者の推奨。additive・後方互換。

result: resolved (Option B applied)

ユーザーが Option B を承認し、plan 02-08 で gap closure を実装した。`ParserConfig.resolve_imports: bool = False` を additive field として追加し、`type_deps.extract()` をゲート化した。デフォルト経路 (`resolve_imports=False`) は pyright/subprocess を一切起動せず AST-only で `resolved=True` を返すため、`execute()` は `(raw_content, path, config)` の純粋関数に復帰した。opt-in 経路 (`resolve_imports=True`) は従来の RESEARCH §2.3 pyright-hybrid (D-06 fail-loudly) を維持。フルスイート 241 passed / 0 failed / 0 skipped、ruff clean。

## Summary

total: 1
passed: 1
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
