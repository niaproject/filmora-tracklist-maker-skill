# Filmora TrackList Maker

Filmora動画編集プロジェクトファイル（`.wfp`）を解析し、使用されている音楽トラックの一覧をテキスト形式で出力するツールです。

## 出力例

```
============================================================
Project : 0923-Echoes in the Dark
Duration: 00:59:15
FPS     : 25
Res     : 1920x1080
============================================================

[AUDIO Track 1]
   1. 00:03:14  02-0923-s. Rise With the Dawn
   2. 00:09:50  04-0923-a. Chasing Tomorrow
   ...

============================================================
```

## ファイル構成

| ファイル | 説明 |
|---|---|
| `*.wfp` | Filmoraプロジェクトファイル（入力） |
| `*.txt` | 生成されたトラックリスト（出力） |

## サンプルファイル

- `0923-Echoes in the Dark.wfp` / `.txt` — サンプルプロジェクト（約59分）
- `test.wfp` / `.txt` — テスト用プロジェクト（約81分）
- `test-repeart.wfp` / `.txt` — リピート機能のテスト用プロジェクト

---

## Claude Skill として導入する方法

このツールは Claude Code のスキルとして使用できます。

### 前提条件

- [Claude Code](https://claude.ai/code) がインストールされていること
- Node.js または Python がインストールされていること

### インストール手順

#### 個人スコープ（全プロジェクトで使用）

```bash
# スキルディレクトリを作成してファイルをコピー
mkdir -p ~/.claude/skills/filmora-tracklist-maker-skill
cp -r .claude/skills/filmora-tracklist-maker-skill/. ~/.claude/skills/filmora-tracklist-maker-skill/
```

#### プロジェクトスコープ（このプロジェクトのみで使用）

このリポジトリをそのままプロジェクトフォルダとして Claude Code で開くだけで有効になります。`.claude/skills/filmora-tracklist-maker-skill/` がすでに含まれているためです。

### スキルの構成ファイル

```
.claude/skills/filmora-tracklist-maker-skill/
├── SKILL.md      # スキル定義（Claude への指示）
├── parse.js      # Node.js 用パーサー
└── parse.py      # Python 用パーサー
```

### 使い方

Claude Code で以下のように呼び出します。

```
/filmora-tracklist-maker-skill <path-to-project.wfp>
```

引数を省略すると、カレントフォルダ内のすべての `.wfp` ファイルを対象にします。

```
/filmora-tracklist-maker-skill
```

Claude が対話形式で出力設定（ファイル形式・連番・最小クリップ長・リピート表記）を確認してからトラックリストを生成します。

