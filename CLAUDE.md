# CLAUDE.md — AIアシスタント向けコードベース解説

## プロジェクト概要

GitHub Actions を使って毎朝・昼に Telegram へ日本語ブリーフィングを自動送信するボット。

送信内容：
- 日付・曜日・祝日情報
- 東京の天気（Open-Meteo API）
- Bitcoin 価格（CoinGecko API）
- Google Calendar のイベント一覧
- ランダムな日本語モチベーションメッセージ

---

## ファイル構成

```
morning-briefing/
├── morning_briefing.py          # メインスクリプト（唯一の実装ファイル）
├── requirements.txt             # Python 依存パッケージ
├── README.md                    # 簡易説明
└── .github/workflows/
    ├── morning-briefing.yml     # 朝6時 JST に自動実行
    ├── afternoon-briefing.yml   # 昼12時 JST に自動実行
    └── test-briefing.yml        # 手動トリガー用テストワークフロー
```

PDFファイル（経営管理ビザ関連資料）はスクリプトとは無関係のドキュメントです。

---

## メインスクリプト: `morning_briefing.py`

### 主要関数

| 関数名 | 役割 |
|--------|------|
| `get_date_info()` | 日付・曜日・祝日／記念日を返す |
| `get_events_from_calendars(morning)` | Google Calendar から当日イベントを取得 |
| `get_morning_events()` | 全日のイベントを取得（朝用） |
| `get_afternoon_events()` | 12時以降のイベントを取得（昼用） |
| `get_bitcoin_price()` | CoinGecko から BTC/JPY・USD 価格を取得 |
| `get_weather()` | Open-Meteo から東京の気象情報を取得 |
| `get_daily_message()` | ランダムなモチベーションメッセージを返す |
| `send_telegram_message(text)` | Telegram Bot API でメッセージ送信 |
| `check_if_already_executed_today()` | 当日の重複送信を Telegram 履歴で防止 |
| `main()` | 全体の制御フロー |

### 実行フロー

1. `BRIEFING_TYPE` 環境変数で `morning` / `afternoon` を判定
2. `check_if_already_executed_today()` で当日分の送信済みチェック（Telegram 履歴を参照）
3. 各データ取得関数を呼び出し
4. メッセージを組み立てて `send_telegram_message()` で送信

### 重複実行防止の仕組み

Telegram Bot の `getUpdates` API で当日のメッセージ履歴を確認する。
`朝の総合ブリーフィング`（朝）または `午後のブリーフィング`（昼）が当日分に存在すればスキップ。
エラー時はフェイルオープン（送信側に倒れる）。

---

## GitHub Actions ワークフロー

### スケジュール

| ワークフロー | cron（UTC） | JST 目標時刻 | `BRIEFING_TYPE` |
|---|---|---|---|
| `morning-briefing.yml` | `0 20 * * *` | 朝 5:00（遅延込みで6時前後） | `morning` |
| `afternoon-briefing.yml` | `0 0 * * *` | 昼 9:00（遅延込みで検証中） | `afternoon` |
| `test-briefing.yml` | 手動（`workflow_dispatch`） | 任意 | 入力で選択 |

**注意**: GitHub Actions のスケジュール cron は UTC 基準。JST = UTC + 9h。

### 並列実行防止

朝・昼それぞれのワークフローに `concurrency` グループが設定されており、進行中のジョブはキャンセルされる。

### 必要な GitHub Secrets

| シークレット名 | 内容 |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot のトークン |
| `TELEGRAM_USER_ID` | 送信先 Telegram ユーザー ID |
| `GOOGLE_CREDENTIALS` | Google サービスアカウントの JSON 文字列 |

### カレンダー設定

- デフォルトカレンダー: `styletech.jp@gmail.com`（ハードコード）
- 追加カレンダー: `ADDITIONAL_CALENDAR_IDS` 環境変数にカンマ区切りで指定
  - ワークフロー内に5件のカレンダー ID がすでに設定済み
- Google Calendar API スコープ: `calendar.readonly`

---

## 依存パッケージ（`requirements.txt`）

```
google-auth==2.26.0
google-auth-httplib2==0.2.0
google-auth-oauthlib==1.2.0
google-api-python-client==2.104.0
requests==2.31.0
pytz==2023.3
```

Python バージョン: **3.11**（`zoneinfo` モジュールを標準ライブラリとして使用）

---

## 外部 API

| サービス | エンドポイント | 認証 |
|---|---|---|
| Telegram Bot API | `api.telegram.org/bot{TOKEN}/sendMessage` | Bot Token |
| Telegram Bot API | `api.telegram.org/bot{TOKEN}/getUpdates` | Bot Token |
| Google Calendar API | `googleapis.com/calendar/v3` | サービスアカウント（JSON 認証情報） |
| Open-Meteo | `api.open-meteo.com/v1/forecast` | なし（無料） |
| CoinGecko | `api.coingecko.com/api/v3/simple/price` | なし（無料） |

天気は東京固定（緯度 35.6762、経度 139.6503）。

---

## コーディング規約・注意事項

- **テストなし**: 単体テストは存在しない。手動テストは `test-briefing.yml` を使う。
- **エラーハンドリング**: 各 API 取得関数は try/except で囲み、エラー時は日本語エラーメッセージを返す。`main()` のエラーは再 raise してワークフローを失敗させる。
- **タイムゾーン**: すべて `ZoneInfo('Asia/Tokyo')` で JST を扱う（`pytz` は依存に含まれるが実際には `zoneinfo` を使用）。
- **祝日データ**: `JAPANESE_HOLIDAYS` と `SPECIAL_DATES` は静的辞書（`MM-DD` キー）。移動祝日（成人の日など）は固定日付のため年によってズレる。
- **ログ**: `logging.INFO` レベルで GitHub Actions ログに出力。重要な処理ステップはすべてログに残す。
- **環境変数**: `BRIEFING_TYPE` が `morning` / `afternoon` 以外の場合は何も送信せず終了する。

---

## ローカルでのテスト方法

```bash
# 依存インストール
pip install -r requirements.txt

# 環境変数を設定してから実行
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_USER_ID="..."
export GOOGLE_CREDENTIALS='{"type": "service_account", ...}'
export BRIEFING_TYPE="morning"

python morning_briefing.py
```

または GitHub Actions の `test-briefing.yml` を `workflow_dispatch` で手動トリガーする。

---

## 変更時の注意点

- `ADDITIONAL_CALENDAR_IDS` はワークフロー YAML 内にハードコードされている。カレンダーを追加・削除する場合は3つのワークフローファイルをすべて更新すること。
- cron スケジュールを変更する場合は UTC/JST の変換を確認する。
- `check_if_already_executed_today()` は Telegram の `getUpdates` が最大100件しか返さないため、大量のメッセージがある場合は当日分のチェックが不完全になる可能性がある。
- `JAPANESE_HOLIDAYS` の移動祝日は年次で手動更新が必要。
