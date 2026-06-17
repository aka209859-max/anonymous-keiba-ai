# 🚀 JRA版AI予想システム - 新規セッション用クイックスタートガイド

**作成日**: 2026年02月14日  
**対象**: 新規セッションでのJRA版開発  
**所要時間**: 5分で全体像把握 → 実装開始

---

## 📋 このドキュメントについて

新規セッションで **中央競馬（JRA）版AI予想システム** を構築するための最短ルートガイドです。

### 添付ファイル（3つ）

1. **このファイル** - `JRA_NEW_SESSION_QUICKSTART.md`（クイックスタート）
2. **完全リファレンス** - `JRA_VERSION_COMPLETE_REFERENCE.md`（31 KB、コード例込み）
3. **実装指示書** - `JRA_VERSION_INSTRUCTIONS.md`（14 KB、詳細手順）

---

## 🎯 プロジェクト概要（30秒で理解）

### 既存システム
- **地方競馬AI予想システム** が完成（Phase 0-11、100%完成）
- GitHub: https://github.com/aka209859-max/anonymous-keiba-ai
- ブランチ: `phase0_complete_fix_2026_02_07`
- AUC 平均0.77、14競馬場対応

### 新規開発目標
- **プロジェクト名**: jra-keiba-ai
- **対象**: 中央競馬（JRA）10競馬場
- **データソース**: **JRA-VAN Data Lab + JRDB（二本立て）**
- **目標精度**: AUC 0.85以上、回収率120%以上

---

## 🔑 重要ポイント（必読）

### データ取得戦略

#### なぜ JRA-VAN + JRDB の二本立て？

```
[JRA-VAN Data Lab] 公式データの信頼性
├─ 基本情報（馬名、騎手、オッズ）
├─ 過去成績（着順、タイム）
└─ リアルタイム性

[JRDB] 予想精度の向上
├─ IDM（総合指数） ★ 核心的指標
├─ タイム指数、ペース指数
├─ 血統評価、コース適性
└─ 40年以上の実績

[ハイブリッド効果]
AUC: 0.73（JRA-VANのみ） → 0.85以上（ハイブリッド）
回収率: 85%（JRA-VANのみ） → 120%以上（ハイブリッド）
```

#### データ取得フロー

```python
# Step 1: JRA-VANから基本データ取得
df_jravan = fetch_from_jravan(race_date, venue_codes)

# Step 2: JRDBから独自指数取得
df_jrdb = fetch_from_jrdb(race_date, venue_codes)

# Step 3: race_id + umaban でマージ
df_merged = df_jravan.merge(df_jrdb, on=['race_id', 'umaban'], how='left')

# Step 4: CSV保存
df_merged.to_csv("data/raw/2026/02/JRA_20260214_raw.csv", encoding='shift-jis')
```

---

## 📚 実装フェーズ（全10フェーズ）

```
Phase 0: データ取得（JRA-VAN + JRDB ハイブリッド）
  ↓ JRA-VAN SDK + JRDB API → 統合CSV
  
Phase 1: 特徴量エンジニアリング
  ↓ JRA-VAN基本50特徴量 + JRDB独自20特徴量 = 70特徴量
  
Phase 2: 学習データ準備
  ↓ 2020-2025年、10競馬場別データセット
  
Phase 3: 二値分類
  ↓ LightGBM、10競馬場別モデル、目標AUC 0.85以上
  
Phase 4-1: ランキング予測
  ↓ LightGBM Ranker
  
Phase 4-2: 回帰予測
  ↓ LightGBM Regressor
  
Phase 5: アンサンブル統合
  ↓ 重み: Binary 30%, Ranking 50%, Regression 20%
  
Phase 6: 配信ファイル生成
  ↓ WIN5対応、Note/ブッカーズ/Twitter
  
Phase 7-10: 高度化
  ↓ Greedy Boruta, Optuna, Kelly基準, バックテスト
```

---

## 💻 新規セッション開始用テンプレート

### コピー&ペーストして最初のメッセージに使用

```markdown
# 🏇 中央競馬（JRA）AI予想システム構築の依頼

こんにちは！新規セッションで中央競馬（JRA）版AI予想システムを構築します。

## 📋 前提情報

### 既存システム
- **地方競馬AI予想システム** が完成しています（Phase 0-11、100%完成）
- GitHubリポジトリ: https://github.com/aka209859-max/anonymous-keiba-ai
- ブランチ: `phase0_complete_fix_2026_02_07`

### 完全リファレンスドキュメント
以下の4つのMDファイルを添付しています:
1. **JRA_NEW_SESSION_QUICKSTART.md** - クイックスタート（5分で全体像把握）
2. **JRA_VERSION_COMPLETE_REFERENCE.md** - 完全リファレンス（47 KB、コード例込み）
3. **JRA_VERSION_INSTRUCTIONS.md** - 実装指示書（23 KB）
4. **docs/jra_context_protocol.md** - コンテキスト維持プロトコル（必読）

⚠️ **重要**: 特に `jra_context_protocol.md` は必ず読んでください。長時間セッションでのコンテキスト喪失を防ぐための運用ルールが記載されています。

## 🎯 新規開発目標

- **プロジェクト名**: jra-keiba-ai
- **対象**: 中央競馬（JRA）10競馬場
- **データソース**: **JRA-VAN Data Lab + JRDB（二本立て）**
- **目標精度**: AUC 0.85以上、回収率120%以上

## 🔑 データ取得戦略（重要）

**JRA-VAN + JRDB ハイブリッドアプローチ**を採用:
- **JRA-VAN**: 公式データ（基本情報、オッズ、結果）
- **JRDB**: 独自指数（IDM、タイム指数、ペース指数、血統評価）
- **ハイブリッド効果**: AUC 0.73 → 0.85以上、回収率 85% → 120%以上

## 📚 実装フェーズ

Phase 0: データ取得（JRA-VAN + JRDB ハイブリッド）
Phase 1: 特徴量エンジニアリング（70特徴量）
Phase 2: 学習データ準備（2020-2025年）
Phase 3-5: モデル学習・予測・アンサンブル
Phase 6: 配信ファイル生成（WIN5対応）
Phase 7-10: 高度化（Greedy Boruta, Optuna, Kelly基準, バックテスト）

## 🔍 最初の質問・確認事項

添付の **JRA_VERSION_COMPLETE_REFERENCE.md** を確認し、以下について提案してください:

### 1. Phase 0（データ取得）のハイブリッド実装方針
- JRA-VAN SDK の使い方
- JRDB API の使い方
- データマージの具体的な方法

### 2. Phase 1（特徴量エンジニアリング）の設計
- 芝/ダート特徴量の実装
- JRDB独自指数の活用方法（IDM、タイム指数など）

### 3. Phase 6（配信ファイル生成）のWIN5対応
- WIN5買い目生成のアルゴリズム
- 指定5レースのTOP3組み合わせ（3^5 = 243点）

## 🚀 開始準備

準備が整ったら、以下の順で進めましょう:

1. 完全リファレンス（JRA_VERSION_COMPLETE_REFERENCE.md）を読み込む
2. 既存システムのアーキテクチャを理解
3. JRA版の具体的な設計方針を提案
4. Phase 0の実装から開始

よろしくお願いします！
```

---

## 📖 詳細情報の参照先

### すぐに参照すべきセクション

#### Phase 0（データ取得）
→ `JRA_VERSION_COMPLETE_REFERENCE.md` の「8. JRA-VAN + JRDB 二本立てデータ取得戦略」

```python
# 実装例（コピー可能）
def fetch_from_jravan(race_date, venue_codes):
    """JRA-VANから基本データを取得"""
    # ... （完全なコードは JRA_VERSION_COMPLETE_REFERENCE.md に記載）

def fetch_from_jrdb(race_date, venue_codes):
    """JRDBから独自指数を取得"""
    # ... （完全なコードは JRA_VERSION_COMPLETE_REFERENCE.md に記載）
```

#### Phase 1（特徴量エンジニアリング）
→ `JRA_VERSION_COMPLETE_REFERENCE.md` の「3. Phase 1: 特徴量エンジニアリングの実装例」

```python
# JRDB指数の活用例
JRDB_INDICES = [
    'idm',                    # IDM（総合指数） - 最重要
    'time_index',             # タイム指数
    'pace_index',             # ペース指数
    'jockey_index',           # 騎手指数
    'trainer_index',          # 調教師指数
    # ... 他15指数
]
```

#### Phase 6（買い目生成）
→ `JRA_VERSION_COMPLETE_REFERENCE.md` の「6. Phase 6: 買い目生成の実装例」

```python
# WIN5買い目生成
def generate_win5_tickets(df, target_races):
    """指定5レースのTOP3組み合わせ（3^5 = 243点）"""
    # ... （完全なコードは JRA_VERSION_COMPLETE_REFERENCE.md に記載）
```

---

## 🎯 実装チェックリスト

### Phase 0（最優先）
- [ ] JRA-VAN Data Lab SDK導入
- [ ] JRDB API導入
- [ ] ハイブリッドデータ取得スクリプト作成
- [ ] 統合CSV生成確認

### Phase 1
- [ ] 芝/ダート特徴量実装
- [ ] JRDB独自指数統合
- [ ] 特徴量CSV生成確認

### Phase 2-5
- [ ] 10競馬場別モデル学習
- [ ] Phase 3-5 実装
- [ ] AUC 0.85以上達成

### Phase 6
- [ ] WIN5買い目生成実装
- [ ] Note/ブッカーズ/Twitter用スクリプト実装

### Phase 7-10
- [ ] Greedy Boruta実装
- [ ] Optuna実装
- [ ] Kelly基準実装
- [ ] バックテスト実装

---

## 🔗 関連リンク

- **既存システム（地方競馬）**: https://github.com/aka209859-max/anonymous-keiba-ai
- **ブランチ**: phase0_complete_fix_2026_02_07
- **最新コミット**: 67d4670

---

## ⚠️ 重要な注意点

### 新規セッションでの制約
- ❌ 既存GitHubリポジトリのファイルを直接確認できない
- ✅ すべての重要なコード実装例を `JRA_VERSION_COMPLETE_REFERENCE.md` に含めた
- ✅ コピー&ペーストで即座に使用可能

### コスト試算
```
JRA-VAN Data Lab: 月額 3,000円〜5,000円
JRDB: 月額 3,000円〜5,000円
合計: 月額 6,000円〜10,000円

回収率120%を目標とした場合:
月間投資額: 10万円 → 期待リターン: 12万円
利益: 2万円 - データ費用: 1万円 = 実質利益: 1万円/月
```

### リスク管理
- Kelly基準による賭け金最適化（Phase 9）
- バックテストでのROI検証（Phase 10）
- 総資金の25%超投資はNG

---

**準備完了！** 上記のテンプレートをコピーして、新規セッションを開始してください。

**作成者**: Claude (AI Assistant)  
**作成日**: 2026年02月14日  
**バージョン**: 1.0  
**ステータス**: ✅ 完成

---

**Good Luck with JRA Version Development! 🏇🎯**
