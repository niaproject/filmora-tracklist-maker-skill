---
name: filmora-tracklist-maker-skill
description: Filmora動画編集プロジェクトファイル(.wfp)を解析してトラックリストを生成する。ユーザーがFilmoraプロジェクトの曲リスト・トラック構成・クリップのタイムコードを知りたい時に使用する。
argument-hint: <path-to-project.wfp>
---

Filmoraプロジェクトファイル `$ARGUMENTS` のトラックリストを生成する。

## 実行手順

**Step 1**: 実行環境を確認し、使用するパーサーとパスを決定する。

まず `node --version` を実行して Node.js が利用可能か確認する。
- Node.js が使える場合: `parse.js` を使用する
- Node.js がない場合: `python --version` または `python3 --version` で Python を確認し、`parse.py` を使用する。両方なければユーザーに Node.js または Python のインストールを案内して終了する。

パスは Glob で `.claude/skills/filmora-tracklist-maker-skill/parse.js`（または `parse.py`）を検索するか、以下の候補を順に試す:
- `.claude/skills/filmora-tracklist-maker-skill/` (プロジェクトスコープ)
- `~/.claude/skills/filmora-tracklist-maker-skill/` (個人スコープ)

**Step 1.5**: 対象ファイルを決定する。
- `$ARGUMENTS` が指定されている場合: そのファイルのみを対象にする
- `$ARGUMENTS` が空の場合: Glob で現在のフォルダ配下の `**/*.wfp` をすべて検索し、見つかったファイルを対象にする。対象ファイルの一覧をユーザーに示す。ファイルが見つからない場合はその旨を伝えて終了する。

**Step 2**: 実行前にユーザーへ以下の4点を確認する（まとめて1回で聞く。複数ファイルの場合も1回だけ確認し、全ファイルに同じ設定を使う）:
1. **保存ファイルの拡張子** — デフォルト: `txt`（例: txt, csv, md）
2. **連番を表示するか** — デフォルト: はい
3. **除外する最小クリップ長（秒）** — デフォルト: 10秒（これより短いクリップは除外）
4. **Repeat表記にする番号N** — 連番N以降のエントリをまとめて1行の `Repeat` と表示。`auto` を指定した場合はAIが自動判定する。0または未指定で無効

**Step 3**: 対象ファイルごとにパーサーを実行する（複数ファイルの場合は順番に処理する）。

- N が数値の場合: `--repeat-below=<N>` オプションを渡して実行
- N が **auto** の場合:
  1. まず `--repeat-below` なしで実行してトラックリストを取得する
  2. 出力を分析し、同じ曲名が繰り返し登場し始める位置（最初の重複エントリの番号）をNと判定する
  3. 判定したNを `--repeat-below=<N>` に指定して再実行する
  4. 自動判定したNをユーザーに伝える

**Node.js の場合:**
```
node <parse.jsのパス> <wfpファイルパス> [--ext=<拡張子>] [--no-seq] [--min-duration=<秒>] [--repeat-below=<N>]
```
```bash
node .claude/skills/filmora-tracklist-maker-skill/parse.js "test.wfp" --ext=txt --min-duration=10
node .claude/skills/filmora-tracklist-maker-skill/parse.js "test.wfp" --ext=md --no-seq --min-duration=5 --repeat-below=3
```

**Python の場合（Node.js がない環境）:**
```
python <parse.pyのパス> <wfpファイルパス> [--ext=<拡張子>] [--no-seq] [--min-duration=<秒>] [--repeat-below=<N>]
```
```bash
python .claude/skills/filmora-tracklist-maker-skill/parse.py "test.wfp" --ext=txt --min-duration=10
python3 .claude/skills/filmora-tracklist-maker-skill/parse.py "test.wfp" --ext=md --no-seq --min-duration=5 --repeat-below=3
```

オプションの省略時はデフォルト値が使われるため、デフォルトのままの項目はオプション不要。

**Step 4**: 各ファイルの出力をユーザーに表示する。パーサーは .wfp と同じ階層に同名ファイルを自動保存するので、全ファイルの保存先パスをまとめてユーザーに伝える。

## 出力形式

時刻は `hh:mm:ss` 形式。AUDIOトラック1のみ出力。各クリップは開始時刻とファイル名のみ表示する。

```
============================================================
Project : <プロジェクト名>
Duration: <総時間>
FPS     : <フレームレート>
Res     : <解像度>
============================================================

[AUDIO Track 1]
   1. hh:mm:ss  <ファイル名>
   2. hh:mm:ss  <ファイル名>

============================================================
```

## エラー時

| エラー | 対処 |
|--------|------|
| `unzip: not found` | unzip コマンドのインストールをユーザーに案内 |
| `.wfp` 以外のファイル | Filmora プロジェクトファイル(.wfp)を指定するよう案内 |
| `timeline.wesproj not found` | ファイルが破損している可能性をユーザーに伝える |
