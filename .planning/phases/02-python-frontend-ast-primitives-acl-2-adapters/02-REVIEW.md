---
phase: 02-python-frontend-ast-primitives-acl-2-adapters
reviewed: 2026-05-31T00:00:00Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - lib_code_parser/adapters/__init__.py
  - lib_code_parser/adapters/pyright.py
  - lib_code_parser/extractors/primitives/callgraph.py
  - lib_code_parser/extractors/primitives/contracts.py
  - lib_code_parser/extractors/primitives/functions.py
  - lib_code_parser/extractors/primitives/type_deps.py
  - lib_code_parser/frontends/__init__.py
  - lib_code_parser/frontends/python.py
  - lib_code_parser/models/__init__.py
  - lib_code_parser/models/infrastructure/cav.py
  - lib_code_parser/models/primitives/__init__.py
  - lib_code_parser/models/primitives/contracts.py
  - lib_code_parser/models/primitives/type_deps.py
findings:
  critical: 1
  warning: 6
  info: 3
  total: 10
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-05-31
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

Phase 2 配下の Python frontend / AST primitive extractors / pyright adapter / 関連
Pydantic モデルをレビューした。コード品質は総じて高く、docstring に設計判断
(D-xx) と trace tag が丁寧に紐づけられている。決定論性の意図的な工夫
(`PYTHONHASHSEED=0`, `LC_ALL=C`, sorted outputs) も明確である。

しかし PROJECT.md の HARD constraint である **「出力は `(raw_content, path, config)`
の純粋関数」「決定論性」** に対して、`type_deps` extractor が外部 subprocess
(pyright) の存在・バージョン・解析挙動に依存する点が最大の懸念である。これは
D-06 fail-loudly として設計上認知されているが、決定論性の前提 (Layer M
bisimulation) を実質的に破る BLOCKER 級の構造リスクであり、本レビューで明示する。

加えて `ContractInfo` の `computed_field` + `extra="forbid"` 組み合わせによる
JSON round-trip 破壊、`_collect_annotation_deps` のモジュール名混入、複数の
robustness gap を検出した。

## Critical Issues

### CR-01: `type_deps` extractor が pyright subprocess に強依存し、決定論性・純粋関数性を破る

**File:** `lib_code_parser/extractors/primitives/type_deps.py:129-131`, `lib_code_parser/adapters/pyright.py:181-222`

**Issue:**
PROJECT.md の HARD constraint は「出力は `(raw_content, path, config)` の純粋関数」
かつ「LLM / network / clock / 動的解析を一切使わない … Layer M bisimulation の
前提条件」である。しかし `type_deps.extract` は無条件に
`PyrightAdapter().analyze(cav.raw_content, cav.path)` を呼び、`resolved` フラグを
pyright の `reportMissingImports` 診断から導出する。これにより:

1. **環境依存**: pyright 未インストール (`FileNotFoundError`)・タイムアウト・非0/1
   returncode で `RuntimeError` が送出され、同一入力でも環境によって「出力が
   出る/例外で死ぬ」が分岐する。`type_deps` を含む `execute()` 全体が pyright
   不在の環境では一切動かない (CLAUDE.md は pyright を dev extra 扱いとも読める)。
2. **解析挙動依存**: `resolved` 値は pyright のバージョン・node 環境・解決アルゴ
   リズムに依存する。`PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` で固定しているが、
   これは「同一バージョンを使えば」決定的という条件付き決定論であり、
   `(raw_content, path, config)` だけの純粋関数ではない。
3. **`PrimitiveFn` 契約違反のリスク**: 他の 3 primitive (functions / callgraph /
   contracts) は純粋 AST walk で副作用ゼロだが、type_deps だけが tempfile 書き込み
   + subprocess 起動という重い副作用を primitive レイヤに持ち込む。executor は
   `config.extract_contracts` で contracts をゲートできるが、type_deps を無効化
   する手段がない (常時 pyright 起動)。

これは「事実抽出のみを担って決定論性を維持する」という Core Value に正面から
抵触する。少なくとも (a) pyright 起動を opt-in config フラグでゲートし、
(b) フラグ無効時は `resolved=True` (= unknown を既定値で表現) のまま AST-only で
返す経路を用意すべき。現状は「pyright が無ければ type_deps が機能しない」=
ライブラリ全体が外部 node ツールチェーンに hard-fail する。

**Fix:**
```python
# config.py に追加
class ParserConfig(BaseModel):
    ...
    resolve_imports: bool = False  # pyright 起動を opt-in に。既定は AST-only 純粋関数

# type_deps.py extract() 内
    if not config.resolve_imports:
        # 純粋関数経路: resolved は既定 True (= 未判定) のまま AST-only で返す
        raw_deps.sort(key=lambda d: (d.source, d.target, d.kind, d.source_line))
        return raw_deps

    adapter = PyrightAdapter(python_version=config.python_version)
    pyright_result = adapter.analyze(cav.raw_content, cav.path)
    ...
```
これにより「決定論的な純粋抽出」が既定動作になり、解決オラクルは明示 opt-in に
なる。Layer M bisimulation を要求する verifier 経路では `resolve_imports=True` を
明示する。

## Warnings

### WR-01: `ContractInfo` の `computed_field` + `extra="forbid"` が `model_validate(model_dump())` round-trip を破壊する

**File:** `lib_code_parser/models/primitives/contracts.py:65-83`

**Issue:**
`ContractInfo` は `model_config = ConfigDict(extra="forbid")` を持ちながら、3 つの
`@computed_field` (`preconditions` / `invariants` / `postconditions`) を公開する。
Pydantic v2 では computed_field は `model_dump()` / `model_dump_json()` の出力に
含まれる。したがって `ContractInfo.model_validate(ci.model_dump())` を呼ぶと、
`extra="forbid"` が出力された computed_field を未知キーとして拒否し
`ValidationError` を送出する。既存テスト
(`tests/unit/models/test_contracts_model.py:114-138`) はこの破壊を認識しており、
`model_validate(model_dump())` を避けて `entries` だけから再構築する迂回をして
いる。

しかし本 lib の Core Value は「verifier (LLM agent) が JSON を受け取り同形式で
比較する」ことである。verifier 側が出力 JSON を `ContractInfo.model_validate(...)`
で復元しようとすると確実に失敗する。これは公開スキーマ契約の latent な破壊で
あり、消費者側でデバッグ困難なエラーを引き起こす。

**Fix:**
computed_field を serialization 出力から外すか (`@computed_field` を通常の
`@property` に変えて dump に含めない)、もしくは `model_validate` 側で computed
キーを無視する。最も安全なのは dump に出さない案:
```python
# computed_field を廃し、純粋 property にする (dump に出ない = round-trip 安全)
@property
def preconditions(self) -> list[str]:
    return [e.name for e in self.entries if e.kind == "precondition"]
```
verifier が JSON で precondition 一覧を必要とするなら、それは `entries` から
導出させる (派生データを serialize しない原則)。

### WR-02: `_collect_annotation_deps` が型注釈中のモジュール名を TypeDep に混入させる

**File:** `lib_code_parser/extractors/primitives/type_deps.py:44-66`

**Issue:**
注釈ツリーを `ast.walk` して `ast.Name` を全て TypeDep として記録するが、
`ast.Attribute` 形式の注釈 (例: `typing.List`, `mymod.SomeType`) を walk すると
内部の `ast.Name` (`typing` / `mymod`) も `ast.Name` として拾われ、target に
モジュール名そのものが混入する。例えば返り値注釈 `typing.Optional[int]` は
`Optional` (Attribute, uppercase→記録) と `typing` (Name→記録) と `int`
(Name→記録) を生む。`typing` はクラス型ではなくモジュール名であり、物理アーキ
表現に不要なノイズを混入させる。これは Core Value の「最大忠実度の事実抽出」を
名目に低品質な事実を出力している状態。

`# v0.1.0 parity` とコメントされており意図的な踏襲だが、parity を理由に既知の
誤抽出を温存するのは physical↔logical 比較精度を下げる。

**Fix:**
Attribute 形式の場合は内部の Name (モジュール名) を記録しないようにする。
`ast.walk` ではなく注釈ルートを判別して、Attribute なら末端 attr のみ、Name 単独
なら id のみを記録する再帰処理に変更する:
```python
def _collect_annotation_deps(annotation, module_name, source_line, deps):
    if isinstance(annotation, ast.Attribute):
        if annotation.attr and annotation.attr[0].isupper():
            deps.append(TypeDep(source=module_name, target=annotation.attr,
                                kind="uses", source_line=source_line))
        return  # 内部 Name (モジュール名) は辿らない
    if isinstance(annotation, ast.Name):
        if annotation.id not in _EXCLUDED_NAMES:
            deps.append(TypeDep(source=module_name, target=annotation.id,
                                kind="uses", source_line=source_line))
        return
    for child in ast.iter_child_nodes(annotation):
        _collect_annotation_deps(child, module_name, source_line, deps)
```

### WR-03: `type_deps` の重複 TypeDep が無排除でソートされ、出力に重複が残る

**File:** `lib_code_parser/extractors/primitives/type_deps.py:142-153`

**Issue:**
`annotated` リストは `(source, target, kind, source_line)` でソートするだけで
重複排除をしない。同一注釈が複数箇所に現れる、あるいは同じ型が複数引数で使われる
場合、同一 `(source, target, kind, source_line)` の TypeDep が複数生成され、出力に
重複エントリが残る。callgraph extractor は `dict.fromkeys` でノード重複を排除して
いる (callgraph.py:97) のに対し、type_deps は一貫性なく重複を残す。決定論的では
あるが、verifier 側の集合比較でノイズになり、physical↔logical の一致判定を誤らせる
可能性がある。

**Fix:**
ソート後に重複排除を加える (DET-04 のソート順を保ったまま):
```python
annotated.sort(key=lambda d: (d.source, d.target, d.kind, d.source_line))
seen: set[tuple[str, str, str, int]] = set()
deduped: list[TypeDep] = []
for d in annotated:
    key = (d.source, d.target, d.kind, d.source_line)
    if key not in seen:
        seen.add(key)
        deduped.append(d)
return deduped
```
v0.1.0 parity を理由に重複を残す場合でも、その判断を docstring に明記すべき。

### WR-04: `assert isinstance(...)` を入力検証に使用しており `-O` 実行で無効化される

**File:** `lib_code_parser/extractors/primitives/functions.py:84-87`, `callgraph.py:66-69`, `contracts.py:151-154`, `type_deps.py:79-82`

**Issue:**
4 つの extractor すべてが `cav.payload` の型検証を `assert isinstance(tree,
ast.Module)` で行っている。Python を `-O` (PYTHONOPTIMIZE) で実行すると assert は
完全に除去されるため、不正な payload (例: C++ frontend が誤って渡した
`TranslationUnit`) が型検証をすり抜け、後続の `tree.body` アクセスで不明瞭な
`AttributeError` になる。ライブラリコードでの入力契約の強制に assert を使うのは
アンチパターン。CAV.payload は `object` 型で意図的に opaque にしているため
(cav.py:44)、ここでの実行時検証は契約上重要である。

**Fix:**
明示的な型チェック + 例外送出に変更する:
```python
tree = cav.payload
if not isinstance(tree, ast.Module):
    raise TypeError(
        f"functions extractor requires Python CAV (ast.Module payload), "
        f"got {type(tree).__name__}"
    )
```

### WR-05: `PyrightAdapter.parse_output` が ABC の `parse_output` シグネチャと非互換で LSP を破る

**File:** `lib_code_parser/adapters/pyright.py:128-143`, `lib_code_parser/adapters/base.py:146-168`

**Issue:**
`SubprocessAdapter` ABC は `parse_output(self, stdout, stderr, returncode) ->
BaseModel` を抽象メソッドとして定義し、`execute()` テンプレートメソッドが
`self.parse_output(result.stdout, result.stderr, result.returncode)` で呼ぶ
(base.py:168)。`PyrightAdapter.parse_output` は追加の keyword-only 引数
`tmpdir` / `caller_path` を持つ。これら無しで ABC の `execute()` を呼ぶと、
`tmpdir_fwd=""` となり tmpdir ストリップが効かず、診断の `file` フィールドに
tmpdir 内部パスが漏洩する (caller_path に置換されない)。docstring で「execute() は
これらを渡さない、analyze() が直接渡す」と注記しているが、ABC が提供する
`execute()` を PyrightAdapter インスタンスで誤って呼ぶと silently 誤った出力
(内部 tmpdir パス漏洩) を返す。これは Liskov 置換違反であり、将来の保守者が
`adapter.execute(...)` を呼ぶと内部 tmpdir パスが出力に混入する罠。

**Fix:**
`PyrightAdapter` で ABC の `execute()` を override して誤用を防ぐか、tmpdir/
caller_path を持たない経路で呼ばれた場合に明示的に `RuntimeError` を送出する。
あるいは `parse_output` の追加引数を専用メソッド名 (例 `_parse_pyright`) に分離し、
ABC の `parse_output` は最小限の委譲だけにする。

### WR-06: `PyrightAdapter.tool_argv` の `-p` フラグがディレクトリでなく config ファイルを指す

**File:** `lib_code_parser/adapters/pyright.py:115-126`

**Issue:**
pyright CLI の `-p` / `--project` フラグは **プロジェクトルートディレクトリ
または `pyrightconfig.json` を含むディレクトリ** を引数に取る (pyright のドキュメ
ント上 `-p <directory>` か `-p <path-to-config-file>` のどちらも受理するが、歴史的
に directory 指定が標準)。ここでは `str(Path(tmpdir) / "pyrightconfig.json")` という
**ファイルパス** を渡している。pyright のバージョンによってはファイルパス受理が
未サポート/挙動差があり、config が読まれず caller の `pyproject.toml` がフォール
バックで効く (Pitfall 3 の回避が失敗する) リスクがある。`cwd=tmpdir` を渡している
ので、`-p tmpdir` (ディレクトリ) を渡せば pyright は同ディレクトリの
`pyrightconfig.json` を確実に読む。少なくとも採用した pyright 1.1.409 で
ファイルパス `-p` が config を読むことを実機検証 (フィールドテスト) し、その根拠を
docstring に残すべき (CLAUDE.md change-verification: hook/script 同様 subprocess
挙動は実機 fire で確認)。

**Fix:**
```python
def tool_argv(self, target_path: str) -> Sequence[str]:
    tmpdir = str(Path(target_path).parent)
    return [
        "pyright",
        "--outputjson",
        "--pythonversion", self.python_version,
        "-p", tmpdir,        # config ファイルでなくディレクトリを指す
        target_path,
    ]
```
合わせて `analyze()` の実データで `generalDiagnostics` に caller の
`reportMissingImports` 以外の混入が無いか目視確認する。

## Info

### IN-01: `_get_call_name` がチェーン呼び出しで複数エッジを生成する設計が docstring 任せ

**File:** `lib_code_parser/extractors/primitives/callgraph.py:43-52`

**Issue:**
`_collect_calls` が `ast.walk` で全 `ast.Call` を拾うため、`a.b().c()` が
callee=`c` と callee=`b` の 2 エッジを生む。module docstring (callgraph.py:7-10) に
意図として明記されているので bug ではないが、verifier がシーケンス図比較で
single-edge を期待すると不一致になる。Phase 3 で再検討予定との注記はあるが、
出力契約として `CallEdge` のセマンティクス (どの呼び出しが 1 エッジになるか) を
モデル docstring 側にも残すと消費者が迷わない。

**Fix:** `CallEdge` モデル (callgraph.py models) の docstring に「chain/nested の
エッジ展開規則」を 1 行追記する。

### IN-02: `FunctionNode.contracts` の default_factory が `__import__` 文字列ハックを使用

**File:** `lib_code_parser/models/primitives/functions.py:46-50`

**Issue:**
循環インポート回避のため `default_factory=lambda: __import__("...",
fromlist=["ContractInfo"]).ContractInfo()` という動的 import ハックを使っている。
直下 (functions.py:56) で `from ...contracts import ContractInfo` を実際に行って
`model_rebuild()` しているため、この `__import__` ハックは冗長で可読性を下げる。
モジュールロード順が確定している以上、通常の遅延参照で十分。

**Fix:** ファイル末尾で import 済みなので `default_factory=ContractInfo` に簡素化
できる (TYPE_CHECKING ガードと model_rebuild で型は解決済み)。

### IN-03: `models/__init__.py` docstring の名称数が実体と不整合

**File:** `lib_code_parser/models/__init__.py:1`

**Issue:**
モジュール docstring は「re-exports all 19 v0.1.0 + v0.2.0 names」と記すが、
`__all__` は 5 (infra) + 8 (primitives) + 5 (evaluations) = 18 名。`ContractEntry` /
`ContractKind` / `SourceKind` はここでは re-export していない (primitives barrel
のみ)。docstring の数値が実体とずれており、将来の保守者を誤認させる。

**Fix:** docstring を実数 (18) に合わせるか、自動生成可能なら `len(__all__)` を
参照する旨に変える (手動カウントは陳腐化する)。

---

_Reviewed: 2026-05-31_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
