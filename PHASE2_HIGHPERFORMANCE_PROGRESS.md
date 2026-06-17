# Phase 2高性能化 実装進捗レポート

**最終更新**: 2026-05-05

---

## 🎯 最終目標

### 性能目標
- **本命複勝的中率**: 56-60%（現状52.8%から+3.2~+7.2pt）
- **AUC**: 0.77-0.79（現状0.7546から+0.0154~+0.0354）
- **三連複的中率**: 20-25%（現状~15%から+5~+10pt）
- **回収率**: 80-88%（現状~75%から+5~+13pt）
- **年間回収率**: 105-110%（投資競馬として）

### 実装方針
- **統計特徴量17個追加**（単純平均11個 + 加重平均6個）
- **加重方式**: 直近重視型（重み [5, 4, 3, 2, 1]）
- **モデル再学習**: 14競馬場 × 3モデル（Binary, Ranking, Regression）
- **投資判断TXT**: 複勝・馬連・ワイド・三連複（複数組み合わせ対応）

---

## 📊 全体工程（選択肢2: 高性能化）

| 工程 | 内容 | 所要時間 | 状態 |
|------|------|----------|------|
| **工程1** | Phase 1修正（統計特徴量17個） | 1時間 | ✅ **完了** |
| **工程2** | Phase 2モデル再学習（14競馬場） | 8-12時間 | ⏳ **次** |
| 工程3 | Phase 6作成（投資判断TXT） | 2時間 | ⏸️ 待機 |
| 工程4 | サンドボックステスト | 30分 | ⏸️ 待機 |
| 工程5 | Git push | 10分 | ⏸️ 待機 |
| 工程6 | Eドライブ実行 | 1時間 | ⏸️ 待機 |

**合計所要時間**: 約11-15時間

---

## 🔧 工程1: Phase 1修正（統計特徴量17個追加）

### 1-1. 現状確認 ✅ 完了
- ✅ `prepare_features.py`（旧版49特徴量）確認済み
- ✅ `prepare_features_v2.py`（単純平均11個）作成済み
- ✅ サンドボックステスト成功（浦和12レース、137件、61特徴量）
- ✅ あなたのPCでテスト成功（E:\anonymous-keiba-ai\）

### 1-2. 加重平均6個の追加 ✅ 完了

#### 追加する統計特徴量（6項目）
1. **recent5_weighted_avg_rank** - 直近5走加重平均着順
   - 重み: [5, 4, 3, 2, 1]
   - 計算式: (prev1×5 + prev2×4 + prev3×3 + prev4×2 + prev5×1) / (有効重みの合計)
   
2. **recent5_weighted_avg_time** - 直近5走加重平均タイム
   - 重み: [5, 4, 3, 2, 1]
   - 計算式: (prev1_time×5 + prev2_time×4 + prev3_time×3 + prev4_time×2 + prev5_time×1) / (有効重みの合計)
   
3. **recent3_avg_rank** - 直近3走平均着順
   - 計算式: (prev1 + prev2 + prev3) / (有効走数)
   - 超直近の調子を反映
   
4. **recent3_top3_rate** - 直近3走3着以内率
   - 計算式: 3着以内回数 / 有効走数
   - 超直近の好走率
   
5. **form_trend** - 調子トレンド
   - 計算式: recent5_weighted_avg_rank - recent5_avg_rank
   - 正の値 = 調子下降、負の値 = 調子上昇
   
6. **consistency_score** - 安定度スコア
   - 計算式: 1 / (recent5_time_std + 1)
   - 値が大きいほど安定

#### 最終特徴量数
```
race_id: 1個
元の特徴量: 49個
単純平均統計: 11個
加重平均統計: 6個
---
合計: 67特徴量
```

### 1-3. サンドボックステスト ✅ 完了
- ✅ 浦和_20260423_raw.csv でテスト成功
- ✅ 67特徴量が正しく生成確認

### 1-4. あなたのPCでテスト ✅ 完了
- ✅ E:\anonymous-keiba-ai\ でテスト実行成功
- ✅ 出力CSV確認（137件、67カラム）
- ✅ 加重平均6個が正しく追加確認

### 1-5. Git commit & push ✅ 完了
- ✅ `prepare_features_v3.py`（67特徴量版）コミット済み
- ✅ 進捗レポート更新済み
- ✅ GitHub push完了

---

## 🤖 工程2: Phase 2モデル再学習 ⏳ **実行中**

### 2-0. データ現状確認 ✅ **完了**（2026-05-05 実施）

#### 確認コマンド実行結果
```cmd
E:\anonymous-keiba-ai\old\data\training_csv で14競馬場のCSVファイルを確認
```

#### ✅ 確認結果: 全データ揃っている！
| 競馬場 | ファイル名 | サイズ | レコード数（推定） |
|--------|-----------|--------|-------------------|
| 浦和 | urawa_2020-2025_v3.csv | 7.8 MB | ~43,000件 |
| 船橋 | funabashi_2020-2025_v3.csv | 8.0 MB | ~44,000件 |
| 川崎 | kawasaki_2020-2025_v3.csv | 9.0 MB | ~50,000件 |
| 大井 | ooi_2023-2025_v3.csv | 9.0 MB | ~50,000件 |
| 盛岡 | morioka_2020-2025_v3.csv | 9.4 MB | ~52,000件 |
| 水沢 | mizusawa_2020-2025_v3.csv | 9.1 MB | ~50,000件 |
| 門別 | monbetsu_2020-2025_v3.csv | 12.5 MB | ~69,000件 |
| 金沢 | kanazawa_2020-2025_v3.csv | 11.3 MB | ~62,000件 |
| 笠松 | kasamatsu_2020-2025_v3.csv | 10.3 MB | ~57,000件 |
| 名古屋 | nagoya_2022-2025_v3.csv | 12.9 MB | ~71,000件 |
| 園田 | sonoda_2020-2025_v3.csv | 21.2 MB | ~117,000件 |
| 姫路 | himeji_2020-2025_v3.csv | 4.0 MB | ~22,000件 |
| 高知 | kochi_2020-2025_v3.csv | 16.0 MB | ~88,000件 |
| 佐賀 | saga_2020-2025_v3.csv | 16.8 MB | ~93,000件 |

**合計**: 14競馬場、約157MB、約87万レコード

---

### 2-1. プロジェクト整理 ✅ **完了**（2026-05-05）

#### 完了内容
- ✅ 旧モデル（34特徴量版）42個を `old/models_34features/` に移動
- ✅ 旧スクリプト（Phase1,7-8,11-12）を `old/scripts/` に移動
- ✅ 学習データCSV約80件を `old/data/training_csv/` に保存（整理完了）
- ✅ 学習結果（PNG/TXT）約140件を `old/results/` に移動
- ✅ 旧バッチファイル約40件を `old/batch_scripts/` に移動
- ✅ 古いドキュメント約100件を `old/docs_archive/` に移動
- ✅ Gitコミット完了

---

### 2-2. 学習データ変換（50特徴量→67特徴量） ✅ **完了**（2026-05-06）

#### 2-2-A. 統計特徴量追加スクリプト作成 ✅ **完了**
- ✅ `scripts/phase1_feature_engineering/add_statistical_features.py` 作成完了
- ✅ 17個の統計特徴量を追加（11個単純平均 + 6個加重平均）
- ✅ Unicodeエンコーディングエラー修正（Windows CP932対応）
- ✅ Gitコミット完了

#### 2-2-B. 浦和テスト ✅ **完了**
- ✅ 入力: `urawa_2020-2025_v3.csv`（43,303件、50カラム）
- ✅ 出力: `urawa_2020-2025_67features.csv`（43,303件、67カラム）
- ✅ 統計値確認:
  - recent5_avg_rank: 平均6.74
  - recent5_top3_rate: 平均0.46
  - recent5_win_rate: 平均0.37
  - recent5_avg_time: 平均1300.56秒
  - recent5_time_std: 平均141.89秒

#### 2-2-C. 14競馬場一括変換 ✅ **完了**（2026-05-06）
- ✅ `batch_convert_67features_fixed.bat` 実行完了
- ✅ 13競馬場バッチ処理成功
- ✅ 浦和を手動処理完了
- ✅ **全14競馬場の67特徴量CSV生成完了**

#### 変換結果サマリー
| 競馬場 | レコード数 | 状態 |
|--------|-----------|------|
| 浦和 | 43,303件 | ✅ 完了 |
| 船橋 | 44,376件 | ✅ 完了 |
| 川崎 | 50,140件 | ✅ 完了 |
| 大井 | 40,842件 | ✅ 完了 |
| 門別 | 57,017件 | ✅ 完了 |
| 盛岡 | 42,984件 | ✅ 完了 |
| 水沢 | 41,544件 | ✅ 完了 |
| 金沢 | 51,334件 | ✅ 完了 |
| 笠松 | 47,062件 | ✅ 完了 |
| 名古屋 | 58,798件 | ✅ 完了 |
| 園田 | 96,119件 | ✅ 完了 |
| 姫路 | 17,969件 | ✅ 完了 |
| 高知 | 71,984件 | ✅ 完了 |
| 佐賀 | 75,845件 | ✅ 完了 |

**合計**: 739,317レコード、全て67特徴量に変換完了

### 2-3. 学習スクリプト作成 ✅ **完了**（2026-05-06）

以下の3つの学習スクリプトを作成しました:

#### 作成したスクリプト
1. **train_phase3_binary.py** ✅ - 2値分類モデル（複勝的中予測）
   - パス: `scripts/phase3_binary/train_phase3_binary.py`
   - 目的: 3着以内に入るかどうかを予測
   - ターゲット: `target` (1=3着以内, 0=それ以外)
   - モデル: LightGBM Binary Classification
   - 評価指標: Accuracy, Precision, Recall, F1-Score, ROC-AUC
   - 出力: `models/binary/{競馬場}_2020-2025_v3_67features_model.txt`

2. **train_phase4_ranking.py** ✅ - ランキングモデル（着順予測）
   - パス: `scripts/phase4_ranking/train_phase4_ranking.py`
   - 目的: 着順を予測（1位〜最下位）
   - ターゲット: `rank_target` (1=1位, 2=2位, ...)
   - モデル: LightGBM LambdaRank
   - 評価指標: Top-1/3/5 Accuracy, NDCG@1,3,5
   - 出力: `models/ranking/{競馬場}_2020-2025_v3_67features_ranking_model.txt`

3. **train_phase4_regression.py** ✅ - 回帰モデル（タイム予測）
   - パス: `scripts/phase4_regression/train_phase4_regression.py`
   - 目的: 走行時間を予測（秒単位）
   - ターゲット: `time` (レース完走時間)
   - モデル: LightGBM Regression
   - 評価指標: MAE, RMSE, R²Score, MAPE
   - 出力: `models/regression/{競馬場}_2020-2025_v3_67features_time_regression_model.txt`

#### 共通仕様
- **入力**: `data/features/67features/*.csv`（67特徴量CSV）
- **競馬場別学習**: 14競馬場ごとに独立したモデルを学習
- **Train/Val分割**: 80% / 20%（Rankingはrace_id単位で分割）
- **Early Stopping**: 50〜100 rounds
- **特徴量**: 67個（50元特徴量 + 17統計特徴量）
- **メタデータ保存**: JSON形式で特徴量リスト・評価指標を保存

#### 学習パラメータ
- `learning_rate`: 0.05
- `num_leaves`: 31
- `feature_fraction`: 0.8
- `bagging_fraction`: 0.8
- `bagging_freq`: 5
- `num_boost_round`: 1000〜2000
- `seed`: 42

#### Gitコミット
- ✅ コミット完了: `feat(training): 67特徴量版学習スクリプト3種類作成 - Binary/Ranking/Regression`
- ✅ 3ファイル追加: 807行

---

### 2-4. 42モデル再学習 ⏳ **次のタスク**

14競馬場 × 3モデル（Binary, Ranking, Regression）= 42モデルを学習します。

#### 実行コマンド
```bash
# Binary Classification
python scripts/phase3_binary/train_phase3_binary.py \
  --input data/features/67features \
  --output models/binary

# Ranking
python scripts/phase4_ranking/train_phase4_ranking.py \
  --input data/features/67features \
  --output models/ranking

# Regression
python scripts/phase4_regression/train_phase4_regression.py \
  --input data/features/67features \
  --output models/regression
```

#### 予想所要時間
- **Binary**: 約2〜3時間（14競馬場 × 10〜15分）
- **Ranking**: 約3〜4時間（14競馬場 × 15〜20分）
- **Regression**: 約2〜3時間（14競馬場 × 10〜15分）
- **合計**: 約8〜12時間



---

## 📄 工程3: Phase 6作成（投資判断TXT）

### 3-1. calculate_investment_advice.py 作成 ⏸️ 待機
- アンサンブル結果から投資判断計算
- スコア0.50以上の馬を抽出
- 三連複の組み合わせ生成（最大5点）

### 3-2. generate_investment_txt.py 作成 ⏸️ 待機
- 投資判断TXT出力
- 推奨馬券: 複勝・馬連・ワイド・三連複
- リスク管理情報

### 3-3. run_phase6_investment.bat 作成 ⏸️ 待機
- バッチファイル作成

---

## 🧪 工程4: サンドボックステスト

### テスト項目 ⏸️ 待機
- [ ] Phase 0 → Phase 1（67特徴量生成）
- [ ] Phase 1 → Phase 3, 4（新モデルで予測）
- [ ] Phase 3, 4 → Phase 5（アンサンブル）
- [ ] Phase 5 → Phase 6（投資判断TXT出力）

---

## 📤 工程5: Git push

### コミット内容 ⏸️ 待機
- prepare_features_v2.py（67特徴量版）
- 新学習済みモデル（42個）
- Phase 6スクリプト3個
- 進捗レポート

---

## 💻 工程6: Eドライブ実行

### 実行内容 ⏸️ 待機
- 実際のレースデータで動作確認
- 投資判断TXT生成確認

---

## 📈 期待効果

| 指標 | 現状 | 目標 | 改善幅 |
|------|------|------|--------|
| 本命複勝的中率 | 52.8% | 56-60% | +3.2~+7.2pt |
| AUC | 0.7546 | 0.77-0.79 | +0.0154~+0.0354 |
| 三連複的中率 | ~15% | 20-25% | +5~+10pt |
| 回収率 | ~75% | 80-88% | +5~+13pt |
| 年間回収率 | - | 105-110% | 投資競馬実現 |

---

## 📝 次のアクション

**現在**: 工程2-2-C（14競馬場一括変換）✅ **完了**

**完了内容**:
- ✅ 全14競馬場の67特徴量CSV生成完了（739,317レコード）
- ✅ 統計特徴量17個追加成功（recent5_avg_rank, recent5_top3_rate等）
- ✅ Unicodeエンコーディングエラー修正完了

**次のステップ**: 工程2-3（学習スクリプト作成）

### 📋 完了確認コマンド

以下のコマンドで最終確認を実行してください:

```cmd
cd E:\anonymous-keiba-ai\data\features\67features

echo ===== Conversion Summary ===== > conversion_summary.txt
echo. >> conversion_summary.txt
echo Files created: >> conversion_summary.txt
dir /b *.csv >> conversion_summary.txt
echo. >> conversion_summary.txt
echo Total files: >> conversion_summary.txt
dir *.csv | find "File(s)" >> conversion_summary.txt
echo. >> conversion_summary.txt
echo File sizes: >> conversion_summary.txt
dir *.csv >> conversion_summary.txt

type conversion_summary.txt
```

**期待される結果**: 14ファイル、約200-300MB

### 🎯 次の作業

工程2-3の学習スクリプト作成に進みます:
1. `train_phase3_binary.py` - 2値分類（複勝的中予測）
2. `train_phase4_ranking.py` - ランキング（着順予測）
3. `train_phase4_regression.py` - 回帰（タイム予測）

準備ができたら指示してください。

---

## 🔗 関連ファイル

### サンドボックス
- `/home/user/webapp/anonymous-keiba-ai/scripts/phase1_feature_engineering/prepare_features_v2.py`
- `/home/user/webapp/anonymous-keiba-ai/IMPLEMENTATION_PLAN_20260505.md`
- `/home/user/webapp/anonymous-keiba-ai/PHASE2_HIGHPERFORMANCE_PROGRESS.md`

### GitHub
- リポジトリ: https://github.com/aka209859-max/anonymous-keiba-ai
- ブランチ: `phase0_complete_fix_2026_02_07`

### あなたのPC
- `E:\anonymous-keiba-ai\scripts\phase1_feature_engineering\prepare_features_v2.py`

---

**最終更新日時**: 2026-05-05
**担当**: AI Assistant
**承認**: User
