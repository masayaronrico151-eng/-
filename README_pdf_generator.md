# PDF 類題自動生成システム

PDFの問題集から問題を抽出し、AIを使って難易度別の類題を自動生成するツールです。

## 機能

- **PDF問題抽出**: 様々な形式の問題番号パターンに対応（問1、(1)、Q1 など）
- **AI類題生成**: OpenAI / Anthropic API を使って3段階の難易度で類題を生成
  - 基本（Easy）: 元問題より簡単
  - 標準（Normal）: 元問題と同程度
  - 発展（Hard）: 元問題より難しい
- **解答・解説付き**: 途中の計算過程や考え方を含む丁寧な解説
- **Word文書出力**: 問題パートと解答パートが分かれた整形済みドキュメント

## セットアップ

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# または開発モードでインストール
pip install -e .
```

## APIキーの設定

OpenAI または Anthropic のいずれかのAPIキーを環境変数に設定してください。

```bash
# OpenAI を使う場合
export OPENAI_API_KEY='sk-...'

# Anthropic を使う場合
export ANTHROPIC_API_KEY='sk-ant-...'
```

## 使い方

### 問題の抽出確認

```bash
# PDFから問題を抽出して一覧表示
python main.py extract 数学問題集.pdf
```

### 類題の生成

```bash
# 全問題に対して全難易度の類題を生成
python main.py generate 数学問題集.pdf

# 出力ファイル名を指定
python main.py generate 数学問題集.pdf -o 類題集.docx

# 特定の問題番号だけ生成
python main.py generate 数学問題集.pdf -n 1,3,5

# 範囲指定も可能
python main.py generate 数学問題集.pdf -n 1-5,8,10

# 難易度を指定
python main.py generate 数学問題集.pdf -d hard

# AIプロバイダとモデルを指定
python main.py generate 数学問題集.pdf --provider anthropic --model claude-sonnet-4-20250514

# 文書タイトルを変更
python main.py generate 数学問題集.pdf --title "期末対策 類題演習"

# 元問題を含めない
python main.py generate 数学問題集.pdf --no-originals
```

### pip インストール後

```bash
# pdf-gen コマンドとして使用可能
pdf-gen extract 数学問題集.pdf
pdf-gen generate 数学問題集.pdf -o output.docx
```

## オプション一覧

| オプション | 短縮 | 説明 | デフォルト |
|-----------|------|------|-----------|
| `--output` | `-o` | 出力ファイルパス | `{入力ファイル名}_類題.docx` |
| `--difficulty` | `-d` | 難易度 (all/easy/normal/hard) | `all` |
| `--numbers` | `-n` | 対象問題番号（カンマ区切り） | 全問題 |
| `--provider` | | AIプロバイダ (openai/anthropic) | 環境変数から自動判定 |
| `--model` | | モデル名 | プロバイダのデフォルト |
| `--title` | | Word文書のタイトル | `類題集` |
| `--no-originals` | | 元問題を含めない | false |

## プロジェクト構成

```
├── main.py                         # エントリーポイント
├── setup.py                        # パッケージ設定
├── requirements.txt                # 依存パッケージ
├── README_pdf_generator.md         # このファイル
└── pdf_problem_generator/
    ├── __init__.py
    ├── cli.py                      # CLIインターフェース
    ├── extractor.py                # PDF問題抽出
    ├── generator.py                # AI類題生成
    ├── models.py                   # データモデル
    └── word_exporter.py            # Word出力
```

## 対応する問題番号パターン

- `問1` / `問 1` / `問１`
- `第1問` / `第 1 問`
- `(1)` / `（1）`
- `1.` / `1）`
- `Q1` / `Q.1`
- `【問題1】` / `【問1】`

## 出力例

生成されるWord文書の構成:

1. **問題パート**（前半）
   - 元問題の参照表示
   - 基本レベルの類題
   - 標準レベルの類題
   - 発展レベルの類題

2. **解答・解説パート**（後半 / 改ページ後）
   - 各類題の解答
   - 途中過程を含む詳細な解説
