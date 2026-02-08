# Phase 5.5: 実オッズを使った正確なバックテスト実行計画書

**作成日**: 2026年2月5日  
**ステータス**: 実行準備完了  
**目的**: Phase 5の仮オッズ（回収率23.86%）を捨て、PC-KEIBAの実払戻金データで正確な回収率を算出

---

## 🎯 Phase 5 の問題点

### Phase 5 で使用した仮オッズ
```python
# 仮オッズ（現実と乖離）
odds = {
    'tansho': 3.0,    # 単勝3.0倍（固定）
    'umaren': 10.0,   # 馬連10.0倍（固定）
    'wide': 5.0,      # ワイド5.0倍（固定）
    'sanrenpuku': 30.0 # 三連複30.0倍（固定）
}
```

### 結果
- **回収率**: 23.86%（異常に低い）
- **的中率**: 4.12%
- **総投資額**: 293,800円
- **総払戻額**: 70,100円
- **損益**: -223,700円

**問題**: 仮オッズは現実の配当と大きく乖離しており、バックテストとして無意味

---

## 📊 PC-KEIBAデータベースの実データ構造

### データベース接続情報（確定）
```python
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}
```

### データベースサイズ
- **pckeiba**: 25 GB（数年分の地方競馬データ）
- PostgreSQL 16.4（PC-KEIBA公式サポート）

---

## 📋 実払戻金データの所在（確認済み）

### テーブル: nvd_hr（払戻金データ）

| 券種 | カラム名 | データ型 | 例 |
|:---|:---|:---|:---|
| **単勝払戻** | haraimodoshi_tansho_1b | VARCHAR(9) | "000000120" = 120円 |
| **複勝払戻** | haraimodoshi_fukusho_*b | VARCHAR(9) | "000000100" = 100円 |
| **馬連払戻** | haraimodoshi_umaren_1b | VARCHAR(9) | "000000400" = 400円 |
| **馬単払戻** | haraimodoshi_umatan_1b | VARCHAR(9) | "000000620" = 620円 |
| **ワイド払戻** | haraimodoshi_wide_*b | VARCHAR(9) | "000000160" = 160円 |
| **三連複払戻** | haraimodoshi_sanrenpuku_1b | VARCHAR(9) | "000001330" = 1,330円 |
| **三連単払戻** | haraimodoshi_sanrentan_1b | VARCHAR(9) | "000002600" = 2,600円 |

**重要**: 
- カラム名の `*b` が**払戻金額**
- `*a` は馬番/組番
- `*c` は人気順

### 実データ例（2026年1月31日 佐賀 1R）
```
単勝: 5番 120円
複勝: 5番 100円, 1番 120円, 10番 210円
馬連: 5-1 400円
ワイド: 5-1 160円
三連複: 1-5-10 1,330円
三連単: 5-1-10 2,600円
```

---

## 🚀 Phase 5.5 実行計画

### Step 1: 実払戻金データ取得スクリプトの作成

#### ファイル名: `backtest_2025_with_real_odds.py`

#### 機能:
1. **PC-KEIBAから実払戻金を取得**
   - テーブル: nvd_hr
   - 対象期間: 2025年全データ
   - 対象競馬場: まず大井（後で全14競馬場に拡張）

2. **Phase 4.5の予測結果と紐付け**
   - 予測結果: `predictions/phase5_ooi_test/ensemble_prediction.csv`
   - 買い目: `predictions/phase5_ooi_test/betting_recommendations.json`
   - 実払戻金とマッチング

3. **券種別回収率の算出**
   - 単勝
   - 複勝
   - 馬連
   - 馬単
   - ワイド
   - 三連複
   - 三連単

4. **結果レポート出力**
   - 総投資額
   - 総払戻額
   - 回収率
   - 的中率
   - 損益

---

### Step 2: 買い目戦略の最適化

#### 現在の戦略（Phase 5）
```
単勝: Sランク本命のみ
馬連: S×A（軸馬流し）
ワイド: S×B（穴馬狙い）
三連複: S-A-B（フォーメーション）
```

#### 新戦略の検討
1. **複勝重視戦略**（安定収益）
   - Sランク3頭に複勝購入
   - 的中率が高く、回収率の安定化

2. **馬単戦略**（高配当狙い）
   - S→A の馬単
   - 三連単よりリスク低く、配当は高め

3. **期待値ベース戦略**
   - 予測確率 × 実オッズ > 1.0 の買い目のみ購入
   - 回収率の最大化

4. **ケリー基準による賭け金配分**
   - 信頼度に応じた賭け金調整
   - リスク管理

---

### Step 3: 全14競馬場での回収率分析

#### 対象競馬場
1. 門別（30）
2. 盛岡（35）
3. 水沢（36）
4. 浦和（42）
5. 船橋（43）
6. 大井（44）← まずここから
7. 川崎（45）
8. 金沢（46）
9. 笠松（47）
10. 名古屋（48）
11. 園田（50）
12. 姫路（51）
13. 高知（54）
14. 佐賀（55）

#### 分析項目
- 競馬場別の回収率
- モデル精度（Phase 4.5 の AUC/NDCG）との相関
- 最適な券種の選定
- 競馬場別の買い目戦略

---

## 📝 実装の詳細仕様

### データ取得SQL（完全版）

```sql
-- 2025年全レースの実払戻金データを取得
SELECT 
    -- レース識別情報
    hr.kaisai_nen,
    hr.kaisai_tsukihi,
    hr.keibajo_code,
    hr.race_bango,
    
    -- 単勝払戻
    hr.haraimodoshi_tansho_1a AS tansho_umaban,
    hr.haraimodoshi_tansho_1b AS tansho_haraimodoshi,
    hr.haraimodoshi_tansho_1c AS tansho_ninkijun,
    
    -- 複勝払戻（1-5着）
    hr.haraimodoshi_fukusho_1a AS fukusho_1_umaban,
    hr.haraimodoshi_fukusho_1b AS fukusho_1_haraimodoshi,
    hr.haraimodoshi_fukusho_2a AS fukusho_2_umaban,
    hr.haraimodoshi_fukusho_2b AS fukusho_2_haraimodoshi,
    hr.haraimodoshi_fukusho_3a AS fukusho_3_umaban,
    hr.haraimodoshi_fukusho_3b AS fukusho_3_haraimodoshi,
    hr.haraimodoshi_fukusho_4a AS fukusho_4_umaban,
    hr.haraimodoshi_fukusho_4b AS fukusho_4_haraimodoshi,
    hr.haraimodoshi_fukusho_5a AS fukusho_5_umaban,
    hr.haraimodoshi_fukusho_5b AS fukusho_5_haraimodoshi,
    
    -- 馬連払戻
    hr.haraimodoshi_umaren_1a AS umaren_kumiban,
    hr.haraimodoshi_umaren_1b AS umaren_haraimodoshi,
    
    -- 馬単払戻
    hr.haraimodoshi_umatan_1a AS umatan_kumiban,
    hr.haraimodoshi_umatan_1b AS umatan_haraimodoshi,
    
    -- ワイド払戻（1-3通り）
    hr.haraimodoshi_wide_1a AS wide_1_kumiban,
    hr.haraimodoshi_wide_1b AS wide_1_haraimodoshi,
    hr.haraimodoshi_wide_2a AS wide_2_kumiban,
    hr.haraimodoshi_wide_2b AS wide_2_haraimodoshi,
    hr.haraimodoshi_wide_3a AS wide_3_kumiban,
    hr.haraimodoshi_wide_3b AS wide_3_haraimodoshi,
    
    -- 三連複払戻
    hr.haraimodoshi_sanrenpuku_1a AS sanrenpuku_kumiban,
    hr.haraimodoshi_sanrenpuku_1b AS sanrenpuku_haraimodoshi,
    
    -- 三連単払戻
    hr.haraimodoshi_sanrentan_1a AS sanrentan_kumiban,
    hr.haraimodoshi_sanrentan_1b AS sanrentan_haraimodoshi

FROM nvd_hr hr
WHERE hr.kaisai_nen = '2025'
  AND hr.keibajo_code = '44'  -- 大井競馬場
ORDER BY hr.kaisai_tsukihi, CAST(hr.race_bango AS INTEGER);
```

### 払戻金の変換関数

```python
def parse_haraimodoshi(haraimodoshi_str: str) -> int:
    """
    払戻金文字列を整数に変換
    
    Args:
        haraimodoshi_str: 払戻金（"000000120"形式）
    
    Returns:
        払戻金（円）
    
    Examples:
        >>> parse_haraimodoshi("000000120")
        120
        >>> parse_haraimodoshi("000106870")
        106870
    """
    if not haraimodoshi_str or haraimodoshi_str.strip() == '':
        return 0
    
    try:
        return int(haraimodoshi_str)
    except:
        return 0
```

---

## 📊 期待される結果

### Phase 5（仮オッズ）vs Phase 5.5（実オッズ）の比較

| 項目 | Phase 5（仮） | Phase 5.5（実） | 改善 |
|:---|---:|---:|:---|
| 回収率 | 23.86% | **目標 80%以上** | 予測精度に基づく |
| 的中率 | 4.12% | **目標 30%以上** | 買い目戦略の最適化 |
| 単勝回収率 | 29.94% | ? | 実データで算出 |
| 複勝回収率 | 24.74% | ? | 実データで算出 |
| 馬連回収率 | 18.28% | ? | 実データで算出 |

**根拠**:
- Phase 4.5で確認された驚異的な精度:
  - Phase 3 AUC: 0.8829
  - Phase 4 ランキング NDCG@1: 0.8775（87.75%的中）
  - Phase 4 回帰 RMSE: 0.8725秒、R²: 1.0000

これらの精度が実際の回収率に反映されるはず。

---

## 🎯 成功基準

### 最低限の成功基準
- ✅ 実払戻金データの取得成功
- ✅ Phase 5の買い目との紐付け成功
- ✅ 回収率が Phase 5（23.86%）より向上

### 理想的な成功基準
- ✅ 回収率 80%以上
- ✅ 的中率 30%以上
- ✅ 複勝回収率 90%以上（安定収益）
- ✅ 三連単で超高配当的中の事例発見

---

## 📁 成果物

### 実装ファイル
1. `backtest_2025_with_real_odds.py` - バックテストメインスクリプト
2. `betting_strategy_v2.py` - 最適化された買い目戦略
3. `recovery_rate_analyzer.py` - 回収率分析ツール

### レポートファイル
1. `docs/phase5.5_real_odds_backtest_results.md` - 実行結果レポート
2. `predictions/phase5.5_ooi_backtest/` - 大井競馬場のバックテスト結果
3. `predictions/phase5.5_all_venues/` - 全14競馬場のバックテスト結果

---

## 🚀 実行手順

### Step 1: スクリプト作成
```bash
cd /home/user/webapp
# backtest_2025_with_real_odds.py を作成
```

### Step 2: 実行
```bash
python backtest_2025_with_real_odds.py \
    --keibajo 44 \
    --year 2025 \
    --predictions predictions/phase5_ooi_test/ensemble_prediction.csv \
    --bets predictions/phase5_ooi_test/betting_recommendations.json \
    --output predictions/phase5.5_ooi_backtest/
```

### Step 3: 結果確認
```bash
cat predictions/phase5.5_ooi_backtest/recovery_rate_summary.json
```

### Step 4: レポート作成
```bash
python generate_phase5.5_report.py
```

### Step 5: GitHub コミット
```bash
git add .
git commit -m "feat(phase5.5): 実オッズを使った正確なバックテスト実装"
git push origin phase4_specialized_models
```

---

## 📌 重要な注意事項

### PC-KEIBAデータの制約
1. **文字エンコーディング**: UTF-8（PostgreSQL 16.4）
2. **データ形式**: 固定長文字列（前ゼロ埋め）
3. **NULL値の扱い**: 空文字列 "" として格納される場合がある

### Phase 4.5の予測結果の制約
1. **対象期間**: 2023-2025データの最新20%
2. **データ件数**: 7,942件（662レース）
3. **競馬場**: 大井のみ

### バックテストの前提
1. **購入タイミング**: レース前（オッズ確定後）
2. **賭け金**: 1点100円（固定）
3. **的中判定**: 確定着順とマッチング

---

## 🎊 Phase 5.5 完了後の次のステップ

### Phase 6: Webシステム化
1. **レース情報の自動取得**: PC-KEIBAから当日データを取得
2. **リアルタイム予測API**: FastAPI で REST API 構築
3. **買い目提示UI**: Streamlit or React で Webアプリ
4. **実績追跡機能**: 実際の結果を自動取得・回収率追跡

### Phase 7: 実戦投入
1. **2026年2月のレースで検証**
2. **回収率の継続的追跡**
3. **モデルの再学習トリガー**

---

**実行計画書作成日**: 2026年2月5日  
**作成者**: AI開発チーム  
**次回アクション**: 「GO」サイン待ち → backtest_2025_with_real_odds.py の実装開始

---

# 🚀 準備完了！「GO」を待っています！
