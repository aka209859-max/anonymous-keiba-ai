# TARGET frontier JV データ活用による JRA-VAN データ再取得不要性の調査

**作成日**: 2026-02-14  
**目的**: TARGET frontier JV ユーザーが既存データをAI予測システムに流用可能かを検証  
**調査方法**: ディープサーチ推奨

---

## 📋 調査背景

**現状**:
- ユーザーは TARGET frontier JV を以前から使用中
- JRA-VAN Data Lab からのデータ取得（約30時間）を回避したい
- TARGET frontier JV のデータベースを AI システムに流用できるか確認が必要

**TARGET frontier JV とは**:
- JRA-VAN Data Lab が提供する公式競馬データベースソフト
- JV-Link を使用して JRA 公式データを取得・蓄積
- SQLite データベースに格納（推定）

---

## 🔍 調査項目

### 1. TARGET frontier JV のデータ格納形式

**調査内容**:
- データベースファイルの保存場所（デフォルトパス）
- データベース形式（SQLite / Access / 独自形式）
- テーブル構造とスキーマ定義
- 格納されているレコードID（RA, SE, HR, O1-O6, WF, BLOD等）

**調査キーワード**（日本語）:
- `TARGET frontier JV データベース 保存場所`
- `TARGET frontier JV SQLite ファイル パス`
- `TARGET frontier JV テーブル構造 スキーマ`
- `TARGET frontier JV データ エクスポート 方法`

**調査キーワード**（英語）:
- `TARGET frontier JV database file location`
- `TARGET frontier JV SQLite schema structure`
- `TARGET frontier JV data export CSV`

---

### 2. 蓄積データの範囲と期間

**調査内容**:
- ユーザーが TARGET frontier JV を使用している期間（例: 5年、10年）
- 自動更新設定の有無（週次・日次）
- 過去データの保持期間（古いデータが削除されるか）
- 欠損データの有無（特定レース・競馬場のデータが不足していないか）

**確認すべき点**:
- AI学習に必要な「過去15年分（2010-2024）」のデータが揃っているか
- 血統データ（BLOD）、調教データ（WF）も含まれているか
- オッズデータ（O1-O6）の時系列データが保存されているか

---

### 3. データベースからの抽出方法

**調査内容**:
- SQLite データベースの直接アクセス方法
- テーブル構造の解析ツール（DB Browser for SQLite等）
- Python での読み込み方法（sqlite3, sqlalchemy）
- CSV エクスポート機能の有無

**想定される実装**:
```python
import sqlite3
import pandas as pd

# TARGET frontier JV のデータベースに接続
conn = sqlite3.connect('C:/TARGET/database.db')  # パスは要調査

# レース詳細テーブル取得（例）
df_races = pd.read_sql('SELECT * FROM races WHERE date >= "2010-01-01"', conn)

# 馬データ取得
df_horses = pd.read_sql('SELECT * FROM horses', conn)

conn.close()
```

---

### 4. AI システムへの統合戦略

**調査内容**:
- TARGET frontier JV のテーブル構造と、作成した `unified_race_data` スキーマの対応関係
- データマッピング（カラム名の変換）が必要な項目
- 欠損カラムの補完方法

**統合シナリオ**:

#### シナリオ A: TARGET DB を直接使用
- TARGET frontier JV のデータベースを読み取り専用で参照
- AI 学習スクリプトを TARGET DB のスキーマに合わせて調整
- **メリット**: データ再取得不要
- **デメリット**: TARGET 専用スキーマへの依存

#### シナリオ B: ETL でマイグレーション
- TARGET DB から必要データを抽出
- 作成した `unified_race_data` スキーマへ変換・投入
- **メリット**: 独立した AI 専用 DB を構築
- **デメリット**: 初回 ETL に数時間必要

---

### 5. JRDB データとの統合

**調査内容**:
- TARGET frontier JV に JRDB データは含まれているか？
- 含まれていない場合、JRDB 単体での取得・統合が必要
- JRDB データのキーマッチング（TARGET DB の race_id との対応）

**想定される結論**:
- TARGET frontier JV = JRA-VAN データのみ
- JRDB データは別途取得必須
- 統合キー（年月日+場所+レース+馬番）で LEFT JOIN

---

## 📝 調査結果のまとめ方

調査完了後、以下の形式でサマリーを作成してください:

```markdown
# TARGET frontier JV 活用可否判定レポート

## 1. データベース情報
- 保存場所: [パス]
- 形式: SQLite / Access / その他
- テーブル数: [数]
- 主要テーブル名: [リスト]

## 2. 蓄積データ範囲
- 期間: [開始年-終了年]
- 総レース数: [数]
- 含まれるレコードID: RA, SE, HR, ...

## 3. AI システム流用可否
### ✅ 流用可能（推奨）
- 理由: [詳細]
- 実装方法: [シナリオA or B]

### ⚠️ 部分的に流用可能
- 理由: [詳細]
- 追加取得が必要なデータ: [リスト]

### ❌ 流用不可（再取得必須）
- 理由: [詳細]
```

---

## 🌐 ディープサーチ推奨クエリ

以下のクエリを使用してウェブ検索を実行してください:

### クエリ 1: データベースファイル特定
```
TARGET frontier JV データベース ファイル 保存場所 パス SQLite
```

### クエリ 2: スキーマ構造
```
TARGET frontier JV テーブル構造 スキーマ定義 データベース設計
```

### クエリ 3: データ抽出・エクスポート
```
TARGET frontier JV データ エクスポート CSV SQL 抽出方法
```

### クエリ 4: AI システム活用事例
```
TARGET frontier JV 機械学習 AI予想 データベース 活用 Python
```

### クエリ 5: 公式ドキュメント
```
TARGET frontier JV マニュアル ヘルプ データベース仕様
```

---

## 🎯 期待される調査結果

### ベストケース
- TARGET frontier JV のデータベースが SQLite 形式
- 過去15年分のデータが完全に蓄積済み
- テーブル構造が解析可能
- Python で直接アクセス可能
- → **JRA-VAN データ再取得不要**、ETL で統合可能

### ワーストケース
- データベースが独自バイナリ形式
- 過去5年分しかデータがない
- エクスポート機能が制限されている
- → **JRA-VAN データ再取得必須**

---

## 📌 次のアクション

調査完了後の手順:

1. **流用可能と判定された場合**:
   - TARGET DB 読み込み用 ETL スクリプトを作成
   - スキーママッピング定義書を作成
   - JRDB データとの統合処理を実装

2. **部分的に流用可能と判定された場合**:
   - 不足期間のみ JRA-VAN から追加取得
   - 既存データと新規データをマージ

3. **流用不可と判定された場合**:
   - 当初計画通り JRA-VAN Data Lab から全データ取得（約30時間）

---

**更新履歴**:
- 2026-02-14: 初版作成（TARGET frontier JV 調査指示）
