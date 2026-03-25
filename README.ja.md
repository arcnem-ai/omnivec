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
  <a href="#ドキュメント">ドキュメント</a>
</p>

---

omnivec は、文書と画像をまとめた ZIP を受け取り、`texvec` と `picvec` でローカル類似分析を行い、次の 2 つを返します。

- 構造化された JSON 分析結果
- その分析結果から作る Markdown レポート

対応入力:

- 文書: `.txt`, `.md`, `.markdown`
- 画像: `.jpg`, `.jpeg`, `.png`

## 最初に押さえること

- 1 回のアップロードごとに 1 つのジョブディレクトリを使います。
- ZIP 展開、ファイル分類、重複判定、類似検索、クラスタリングは決定的に処理されます。
- CrewAI を使うのは最後の Markdown レポート生成だけです。

## インストール

Python `>=3.10,<3.14` と [uv](https://docs.astral.sh/uv/) を用意してください。

依存をインストールします:

```sh
uv sync
```

Docker なしでローカル実行する場合は、`texvec` と `picvec` が `PATH` 上に必要です。

ローカルソースからビルドする例:

```sh
cd ~/Documents/GitHub/picvec
go build -o /usr/local/bin/picvec .

cd ~/Documents/GitHub/texvec
go build -o /usr/local/bin/texvec .
```

最低限の環境変数を設定します:

```sh
export OPENAI_API_KEY=your-key
export OMNIVEC_DATA_DIR=$PWD/.omnivec-data
export OMNIVEC_API_KEY=dev-secret
```

`OPENAI_API_KEY` は CrewAI レポート生成に必要です。必要なら `.env` に入れても構いません。

## クイックスタート

このリポジトリには `sample_assets/` に小さなデモ用コーパスが入っています。

API を起動:

```sh
make serve
```

別ターミナルでサンプルの一連フローを実行:

```sh
make smoke-all
```

このフローで `sample-assets.zip` の作成、アップロード、ジョブ完了待ち、最終レポート取得まで行えます。最初の起動は、`make serve` が共有 `texvec` / `picvec` キャッシュを温めるため少し時間がかかることがあります。

API を直接叩く最短の流れは次の通りです:

```sh
make sample-zip

curl -X POST \
  -H "X-API-Key: dev-secret" \
  -F "file=@sample-assets.zip" \
  http://127.0.0.1:8000/v1/jobs
```

最終レポートの方向づけをしたい場合は、`-F "curation_goal=discovery"`、`dedupe`、`taxonomy_cleanup` を追加できます。

## API

| エンドポイント | 内容 |
|---------------|------|
| `POST /v1/jobs` | ZIP をアップロードして新しい分析ジョブを作成 |
| `GET /v1/jobs/{job_id}` | ジョブ状態、時刻、件数、エラーを返す |
| `GET /v1/jobs/{job_id}/report` | Markdown レポートと構造化分析 JSON を返す |
| `GET /healthz` | ヘルスチェック |

`OMNIVEC_API_KEY` が設定されている場合、`/v1/*` には `X-API-Key` が必要です。

`POST /v1/jobs` は次を受け付けます:

- ZIP アップロード用の `file`
- 任意の `curation_goal`。値は `discovery`、`dedupe`、`taxonomy_cleanup`

## ドキュメント

詳細ドキュメントは英語です。

- [Technical overview](docs/technical-overview.md)
- [Operations and development](docs/operations.md)
- [Deployment](docs/deployment.md)
- [Extending Omnivec](docs/extending-omnivec.md)

## ライセンス

omnivec は [MIT License](LICENSE) で公開しています。

---

<p align="center">
  <a href="https://arcnem.ai">Arcnem AI</a> が開発。
</p>
