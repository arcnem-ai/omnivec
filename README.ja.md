<p align="center">
  <img src="arcnem-logo.svg" alt="Arcnem AI" width="120" />
</p>

<h1 align="center">omnivec</h1>

<p align="center">
  <strong>ローカルファーストの文書・画像類似分析を行う、APIファーストのアセットライブラリアン。</strong>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="#インストール">インストール</a> ·
  <a href="#クイックスタート">クイックスタート</a> ·
  <a href="#api">API</a> ·
  <a href="#docker">Docker</a> ·
  <a href="#開発">開発</a>
</p>

---

omnivecは、アセット整理のためのオープンソースAPIです。文書と画像をまとめたZIPを受け取り、文書類似は `texvec`、画像類似は `picvec` でローカル分析し、最後に小さなCrewAIクルーが重複、関連クラスタ、整理の提案を含むMarkdownレポートを書きます。

Arcnem AIが開発しているomnivecは、私たちが好む実用的なAIツールの考え方を反映しています。重要な類似検索レイヤーはローカルに保ちつつ、1台のマシンでも小さなRailwayデプロイでも扱いやすい形です。

## omnivecの特徴

- ZIPを1回送るだけで、構造化レポートが返る
- 類似検索と保存はローカル中心
- 外部ベクトルデータベースは不要
- curlで扱いやすいAPIファースト設計
- 重複判定やクラスタリングは決定的に処理し、CrewAIはレポート生成に集中

## インストール

Python `>=3.10,<3.14` と [uv](https://docs.astral.sh/uv/) を用意してください。

Python依存をインストールします:

```sh
uv sync
```

Dockerなしでローカル実行する場合は、`texvec` と `picvec` が `PATH` 上に必要です。

ローカルソースからビルドする例:

```sh
cd ~/Documents/GitHub/picvec
go build -o /usr/local/bin/picvec .

cd ~/Documents/GitHub/texvec
go build -o /usr/local/bin/texvec .
```

必要な環境変数を設定します:

```sh
export OPENAI_API_KEY=your-key
export OMNIVEC_DATA_DIR=$PWD/.omnivec-data
export OMNIVEC_API_KEY=dev-secret
```

必要なら、これらの値を `.env` に入れても構いません。同梱の `Makefile` は `.env` が存在すれば自動で読み込みます。

## クイックスタート

このリポジトリには `sample_assets/` に小さなデモ用コーパスが入っています。

ZIPを作成:

```sh
cd sample_assets
zip -r ../sample-assets.zip .
```

APIを起動:

```sh
uv run omnivec
```

ジョブを作成:

```sh
curl -X POST \
  -H "X-API-Key: dev-secret" \
  -F "file=@sample-assets.zip" \
  http://127.0.0.1:8000/v1/jobs
```

状態確認:

```sh
curl -H "X-API-Key: dev-secret" \
  http://127.0.0.1:8000/v1/jobs/<job_id>
```

完了後のレポート取得:

```sh
curl -H "X-API-Key: dev-secret" \
  http://127.0.0.1:8000/v1/jobs/<job_id>/report
```

## よく使うコマンド

整理されたコマンド群を使いたい場合は、同梱の `Makefile` を使えます。

```sh
make help
make sync
make test
make serve
make sample-zip
make smoke-all
```

おすすめの流れ:

1. `make sync`
2. `make test`
3. `make serve`
4. 別ターミナルで `make sample-zip`
5. その後 `make smoke-all`

`make serve` は起動前に共有 `texvec` / `picvec` キャッシュを初期化するようになったため、最初の起動時はランタイムやモデル準備で少し時間がかかることがあります。

`make create-job`、`make job-status`、`make job-report`、`make smoke-all` は、デフォルトで `.env` の `OMNIVEC_API_KEY` を使い、未設定時のみ `dev-secret` にフォールバックします。

特定ジョブを個別に確認したい場合:

```sh
make job-status JOB_ID=<job_id>
make job-report JOB_ID=<job_id>
```

## API

| エンドポイント | 内容 |
|---------------|------|
| `POST /v1/jobs` | ZIPをアップロードして新しい分析ジョブを作成 |
| `GET /v1/jobs/{job_id}` | ジョブ状態、件数、時刻、エラーを返す |
| `GET /v1/jobs/{job_id}/report` | Markdownレポートと構造化分析JSONを返す |
| `GET /healthz` | ヘルスチェック |

`OMNIVEC_API_KEY` が設定されている場合、`/v1/*` には `X-API-Key` が必要です。

### 対応入力

- 文書: `.txt`, `.md`, `.markdown`
- 画像: `.jpg`, `.jpeg`, `.png`

文書だけ、画像だけ、両方を含むZIPに対応しています。未対応ファイルは無視され、結果に一覧表示されます。

## 仕組み

1. アップロードされたZIPをジョブ用ワークスペースへ安全に展開します。
2. 対応ファイルと無視ファイルを分類します。
3. SHA-256で完全一致重複をまとめます。
4. 対応文書を `texvec` でインデックスします。
5. 対応画像を `picvec` でインデックスします。
6. 相互top-k検索から類似クラスタを作ります。
7. 構造化された分析結果をCrewAIクルーへ渡し、最終Markdownレポートを生成します。

## サンプルアセット

`sample_assets/` には次のものが入っています。

- ローカル `texvec` リポジトリ由来の文書サンプル
- ローカル `picvec` リポジトリ由来のJPEG画像サンプル
- 意図的に複製した文書1件
- 意図的に複製した画像1件

ローカルデモや手動スモークチェックに使えます。

## データ保存先

実行時データは `OMNIVEC_DATA_DIR` 配下に保存されます。

```text
OMNIVEC_DATA_DIR/
  jobs/
    <job_id>/
      upload.zip
      extracted/
      status.json
      analysis.json
      report.md
  cache/
    texvec/
    picvec-home/
```

共有キャッシュには重いランタイム資産やモデル資産を保存します。一方で各ジョブは個別のインデックス状態を持つため、別アップロードの結果が混ざりません。

## 設定

| 変数 | 内容 | デフォルト |
|------|------|------------|
| `OMNIVEC_DATA_DIR` | ジョブと共有キャッシュの保存先 | `.omnivec-data` |
| `OMNIVEC_API_KEY` | `/v1/*` 用の任意APIキー | 未設定 |
| `MODEL` | CrewAIで使うモデル文字列 | `openai/gpt-4o-mini` |
| `OMNIVEC_TEXVEC_BIN` | `texvec` バイナリパス | `texvec` |
| `OMNIVEC_PICVEC_BIN` | `picvec` バイナリパス | `picvec` |
| `OMNIVEC_MAX_CONCURRENT_JOBS` | 同時実行ジョブ数 | `1` |
| `OMNIVEC_MAX_NEIGHBORS` | クラスタリングに使う近傍数 | `3` |
| `OMNIVEC_JOB_TTL_HOURS` | 完了ジョブ成果物のTTL | `72` |
| `OPENAI_API_KEY` | CrewAIレポート生成に必要 | 未設定 |

## Docker

イメージをビルド:

```sh
docker build -t omnivec .
```

実行:

```sh
docker run --rm \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  -e OMNIVEC_API_KEY=prod-secret \
  -e OMNIVEC_DATA_DIR=/data \
  -v "$(pwd)/.omnivec-data:/data" \
  omnivec
```

Dockerfileでは:

- 固定リビジョンの `picvec` と `texvec` をGoステージでビルド
- Python依存を `uv` でインストール
- Uvicornでomnivec APIを起動

## Railway

このリポジトリには `railway.toml` と Dockerfile ベースのデプロイ設定があります。

推奨構成:

1. `/data` にマウントする永続ボリュームを作成
2. `OMNIVEC_DATA_DIR=/data` を設定
3. `OPENAI_API_KEY` を設定
4. 必要なら `OMNIVEC_API_KEY` も設定

最初の実行時に、`texvec` と `picvec` は共有キャッシュへONNX Runtimeとデフォルトモデルをダウンロードします。

## リポジトリ構成

- `src/omnivec/api.py` FastAPIアプリとHTTPエンドポイント
- `src/omnivec/jobs.py` ジョブ実行と分析オーケストレーション
- `src/omnivec/runners.py` `texvec` と `picvec` のサブプロセス連携
- `src/omnivec/crew.py` CrewAIレポートクルー
- `src/omnivec/config/` CrewAI用YAML設定
- `sample_assets/` ローカルデモ用コーパス
- `tests/` 決定的なユニット/ APIテスト

## 対応プラットフォーム

| デプロイ形態 | 主な対象 |
|-------------|----------|
| ローカル開発 | Pythonとローカルバイナリを使うmacOS / Linux |
| Docker | Linuxコンテナ |
| Railway | 永続ボリューム付きのDockerfileベースLinuxデプロイ |

## 開発

```sh
uv sync
uv run pytest
uv run omnivec
```

デフォルトのテストスイートはオフラインで動き、fake runner と fake report generator を使うため、OpenAI認証情報やモデルダウンロード、ネットワークアクセスは不要です。

コントリビュート手順は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。AIエージェント向けのリポジトリ固有ルールは [AGENTS.md](AGENTS.md) にあります。

## ライセンス

omnivec は [MIT License](LICENSE) で公開しています。

---

<p align="center">
  <a href="https://arcnem.ai">Arcnem AI</a> が開発。
</p>
