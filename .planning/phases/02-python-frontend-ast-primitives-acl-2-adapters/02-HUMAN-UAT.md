---
status: partial
phase: 02-python-frontend-ast-primitives-acl-2-adapters
source: [02-VERIFICATION.md, 02-REVIEW.md]
started: 2026-05-31T00:00:00Z
updated: 2026-05-31T00:00:00Z
---

## Current Test

[awaiting human decision on CR-01 determinism policy]

## Tests

### 1. CR-01 — type_deps の pyright subprocess を opt-in ゲートにするか

expected: `type_deps.extract()` の import 解決方針が PROJECT.md の HARD constraint「出力は `(raw_content, path, config)` の純粋関数」「決定論性 (Layer M bisimulation の前提)」と整合する形に確定していること。

現状: `type_deps.extract()` は pyright subprocess を**常時**起動して `resolved` flag を導出する。`config.resolve_imports` のような opt-in ゲートがないため、pyright 未インストール環境では `execute()` 全体が `RuntimeError` で hard-fail する。CONTEXT.md D-06 は「fail loudly = 意図的設計」と記録しているが、デフォルトで外部ツール依存・環境依存・hard-fail を持ち込むことが Core Value (決定論) と整合するかはポリシー判断 = 人間決定事項 (contract-level)。

選択肢:
- (A) 現状承認 — D-06 fail-loudly + `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` 固定で「条件付き決定論」として受け入れる。コード変更なし。
- (B) Fix (gap closure) — `ParserConfig` に `resolve_imports: bool = False` を追加し、未設定時は pyright を起動せず AST-only で `resolved=True` 既定を返す。CR-01 / verifier 両者の推奨。additive・後方互換。

result: [pending]

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps
