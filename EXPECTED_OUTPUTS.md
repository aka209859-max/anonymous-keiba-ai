# 期待される出力ファイル一覧

## 📋 目次

1. [Phase 7 出力ファイル](#phase-7-出力ファイル)
2. [Phase 8 出力ファイル](#phase-8-出力ファイル)
3. [Phase 5 出力ファイル](#phase-5-出力ファイル)
4. [ファイルサイズ目安](#ファイルサイズ目安)
5. [ファイル確認コマンド](#ファイル確認コマンド)

---

## Phase 7 出力ファイル

### 📁 ディレクトリ: `data/features/selected/`

Phase 7（Boruta特徴選択）を実行すると、以下のファイルが生成されます。

#### ✅ 全会場 × 3モデル = 42ファイル

**会場リスト**: 船橋 / 川崎 / 大井 / 浦和 / 盛岡 / 水沢 / 笠松 / 金沢 / 園田 / 姫路 / 高知 / 佐賀 / 荒尾（計14会場）

**各会場につき3ファイル**:

1. **Binary分類用特徴量**
   - ファイル名: `{venue}_selected_features.csv`
   - 例: `funabashi_selected_features.csv`
   - 内容: Binary分類モデル用に選択された特徴量リスト
   - カラム: `feature`, `importance`, `decision`, `ranking`
   - 行数: 20-30行（選択された特徴量の数）

2. **Ranking予測用特徴量**
   - ファイル名: `{venue}_ranking_selected_features.csv`
   - 例: `kawasaki_ranking_selected_features.csv`
   - 内容: Rankingモデル用に選択された特徴量リスト
   - カラム: `feature`, `importance`, `decision`, `ranking`
   - 行数: 25-35行

3. **Regression予測用特徴量**
   - ファイル名: `{venue}_regression_selected_features.csv`
   - 例: `ohi_regression_selected_features.csv`
   - 内容: Regressionモデル用に選択された特徴量リスト
   - カラム: `feature`, `importance`, `decision`, `ranking`
   - 行数: 15-25行

#### 完全なファイルリスト例

```
data/features/selected/
├─ funabashi_selected_features.csv
├─ funabashi_ranking_selected_features.csv
├─ funabashi_regression_selected_features.csv
├─ kawasaki_selected_features.csv
├─ kawasaki_ranking_selected_features.csv
├─ kawasaki_regression_selected_features.csv
├─ ohi_selected_features.csv
├─ ohi_ranking_selected_features.csv
├─ ohi_regression_selected_features.csv
├─ urawa_selected_features.csv
├─ urawa_ranking_selected_features.csv
├─ urawa_regression_selected_features.csv
├─ morioka_selected_features.csv
├─ morioka_ranking_selected_features.csv
├─ morioka_regression_selected_features.csv
├─ mizusawa_selected_features.csv
├─ mizusawa_ranking_selected_features.csv
├─ mizusawa_regression_selected_features.csv
├─ kasamatsu_selected_features.csv
├─ kasamatsu_ranking_selected_features.csv
├─ kasamatsu_regression_selected_features.csv
├─ kanazawa_selected_features.csv
├─ kanazawa_ranking_selected_features.csv
├─ kanazawa_regression_selected_features.csv
├─ sonoda_selected_features.csv
├─ sonoda_ranking_selected_features.csv
├─ sonoda_regression_selected_features.csv
├─ himeji_selected_features.csv
├─ himeji_ranking_selected_features.csv
├─ himeji_regression_selected_features.csv
├─ kochi_selected_features.csv
├─ kochi_ranking_selected_features.csv
├─ kochi_regression_selected_features.csv
├─ saga_selected_features.csv
├─ saga_ranking_selected_features.csv
├─ saga_regression_selected_features.csv
├─ arao_selected_features.csv
├─ arao_ranking_selected_features.csv
└─ arao_regression_selected_features.csv

合計: 42ファイル（14会場 × 3モデル）
```

---

### 📁 ディレクトリ: `data/reports/phase7_feature_selection/`

Phase 7の詳細レポートが生成されます。

#### 各会場につき6ファイル（3モデル × 2ファイル）

1. **Borutaレポート（テキスト）**
   - `{venue}_boruta_report.txt` (Binary用)
   - `{venue}_ranking_boruta_report.txt` (Ranking用)
   - `{venue}_regression_boruta_report.txt` (Regression用)
   - 内容: 特徴選択の詳細統計、選択/棄却された特徴量リスト

2. **特徴量重要度グラフ（PNG）**
   - `{venue}_feature_importance.png` (Binary用)
   - `{venue}_ranking_feature_importance.png` (Ranking用)
   - `{venue}_regression_feature_importance.png` (Regression用)
   - 内容: 特徴量重要度の可視化グラフ

#### 完全なファイルリスト例

```
data/reports/phase7_feature_selection/
├─ funabashi_boruta_report.txt
├─ funabashi_feature_importance.png
├─ funabashi_ranking_boruta_report.txt
├─ funabashi_ranking_feature_importance.png
├─ funabashi_regression_boruta_report.txt
├─ funabashi_regression_feature_importance.png
├─ kawasaki_boruta_report.txt
├─ kawasaki_feature_importance.png
... (14会場 × 6ファイル = 84ファイル)
```

**Phase 7 合計**: 126ファイル（42 + 84）

---

## Phase 8 出力ファイル

### 📁 ディレクトリ: `data/models/tuned/`

Phase 8（Optunaハイパーパラメータ最適化）を実行すると、以下のファイルが生成されます。

#### ✅ 全会場 × 3モデル × 4ファイル = 168ファイル

**各会場・各モデルにつき4ファイル**:

1. **最適化モデルファイル（.txt）**
   - Binary: `{venue}_tuned_model.txt`
   - Ranking: `{venue}_ranking_tuned_model.txt`
   - Regression: `{venue}_regression_tuned_model.txt`
   - 内容: LightGBM学習済みモデル（テキスト形式）
   - サイズ: 数百KB〜数MB

2. **ベストパラメータ（.csv）**
   - Binary: `{venue}_best_params.csv`
   - Ranking: `{venue}_ranking_best_params.csv`
   - Regression: `{venue}_regression_best_params.csv`
   - 内容: 最適化されたハイパーパラメータ一覧
   - カラム: `parameter`, `value`

3. **最適化履歴グラフ（.png）**
   - Binary: `{venue}_tuning_history.png`
   - Ranking: `{venue}_ranking_tuning_history.png`
   - Regression: `{venue}_regression_tuning_history.png`
   - 内容: Optuna試行回数 vs 評価指標のグラフ

4. **最適化レポート（.json）**
   - Binary: `{venue}_tuning_report.json`
   - Ranking: `{venue}_ranking_tuning_report.json`
   - Regression: `{venue}_regression_tuning_report.json`
   - 内容: 最適化統計（ベストスコア、試行回数、所要時間など）

#### 完全なファイルリスト例（船橋のみ）

```
data/models/tuned/
├─ funabashi_tuned_model.txt
├─ funabashi_best_params.csv
├─ funabashi_tuning_history.png
├─ funabashi_tuning_report.json
├─ funabashi_ranking_tuned_model.txt
├─ funabashi_ranking_best_params.csv
├─ funabashi_ranking_tuning_history.png
├─ funabashi_ranking_tuning_report.json
├─ funabashi_regression_tuned_model.txt
├─ funabashi_regression_best_params.csv
├─ funabashi_regression_tuning_history.png
└─ funabashi_regression_tuning_report.json
```

#### 全会場の完全なファイル数

```
data/models/tuned/
├─ funabashi_*.{txt,csv,png,json} (12ファイル)
├─ kawasaki_*.{txt,csv,png,json} (12ファイル)
├─ ohi_*.{txt,csv,png,json} (12ファイル)
... (14会場)

合計: 168ファイル（14会場 × 3モデル × 4ファイル）
```

**Phase 8 合計**: 168ファイル

---

## Phase 5 出力ファイル

### 📁 ディレクトリ: `data/predictions/phase5_optimized/`

Phase 5（最適化アンサンブル統合）を実行すると、予測結果ファイルが生成されます。

#### ✅ 予測対象日付 × 会場 × 2ファイル

**各予測につき2ファイル**:

1. **アンサンブル予測結果（.csv）**
   - ファイル名: `{venue}_{date}_ensemble_optimized.csv`
   - 例: `funabashi_20260210_ensemble_optimized.csv`
   - 内容: レース・馬番ごとの統合予測結果
   - カラム:
     - `race_id`: レースID
     - `umaban`: 馬番
     - `ensemble_score`: 統合スコア（0〜1）
     - `final_rank`: 最終予測順位
     - `binary_probability`: Binary予測確率
     - `binary_rank`: Binary予測順位
     - `ranking_score`: Ranking予測スコア
     - `ranking_rank`: Ranking予測順位
     - `predicted_time`: Regression予測タイム（1/10秒単位）
     - `time_rank`: Regression予測順位

2. **予測サマリー（.json）**
   - ファイル名: `{venue}_{date}_ensemble_optimized_summary.json`
   - 例: `funabashi_20260210_ensemble_optimized_summary.json`
   - 内容: 予測統計サマリー
   - 構造:
     ```json
     {
       "venue": "funabashi",
       "date": "20260210",
       "total_records": 120,
       "total_races": 12,
       "ensemble_score_stats": {
         "mean": 0.5234,
         "std": 0.2156,
         "min": 0.0823,
         "max": 0.9567
       },
       "binary_probability_stats": {...},
       "ranking_score_stats": {...},
       "predicted_time_stats": {...}
     }
     ```

#### ファイルリスト例

```
data/predictions/phase5_optimized/
├─ funabashi_20260210_ensemble_optimized.csv
├─ funabashi_20260210_ensemble_optimized_summary.json
├─ kawasaki_20260211_ensemble_optimized.csv
├─ kawasaki_20260211_ensemble_optimized_summary.json
├─ ohi_20260212_ensemble_optimized.csv
├─ ohi_20260212_ensemble_optimized_summary.json
... (予測実行回数に応じて増加)
```

**Phase 5 合計**: 予測実行回数 × 2ファイル

---

## ファイルサイズ目安

### Phase 7（特徴選択結果）

| ファイルタイプ | サイズ目安 | 合計（14会場） |
|------------|---------|-------------|
| 特徴量CSV | 2-5 KB | 84-210 KB |
| Borutaレポート（TXT） | 10-30 KB | 420-1,260 KB |
| 重要度グラフ（PNG） | 100-300 KB | 4.2-12.6 MB |
| **Phase 7 合計** | - | **約15-25 MB** |

---

### Phase 8（最適化モデル）

| ファイルタイプ | サイズ目安 | 合計（14会場 × 3モデル） |
|------------|---------|---------------------|
| モデルファイル（TXT） | 500 KB - 3 MB | 21-126 MB |
| ベストパラメータ（CSV） | 1-3 KB | 42-126 KB |
| 最適化履歴（PNG） | 100-300 KB | 4.2-12.6 MB |
| 最適化レポート（JSON） | 2-5 KB | 84-210 KB |
| **Phase 8 合計** | - | **約25-140 MB** |

---

### Phase 5（予測結果）

| ファイルタイプ | サイズ目安 | 備考 |
|------------|---------|------|
| 予測結果CSV | 10-50 KB/レース | レース数に依存 |
| サマリーJSON | 1-3 KB | - |

**例**: 1日12レースの場合
- CSV: 約120-600 KB
- JSON: 約1-3 KB
- **合計**: 約121-603 KB/日

---

### 全体合計（Phase 7 + 8 + 5）

| フェーズ | ファイル数 | サイズ目安 |
|---------|----------|----------|
| Phase 7 | 126ファイル | 15-25 MB |
| Phase 8 | 168ファイル | 25-140 MB |
| Phase 5 | 変動 | 予測回数に依存 |
| **合計** | **294ファイル以上** | **約40-165 MB以上** |

---

## ファイル確認コマンド

### Windows（コマンドプロンプト）

#### Phase 7ファイル確認

```cmd
REM 特徴量CSVファイル数を確認
dir /b data\features\selected\*.csv | find /c /v ""

REM 特徴量CSVファイル一覧表示
dir /b data\features\selected\*.csv

REM Borutaレポート数を確認
dir /b data\reports\phase7_feature_selection\*.txt | find /c /v ""

REM 重要度グラフ数を確認
dir /b data\reports\phase7_feature_selection\*.png | find /c /v ""
```

**期待される出力**:
- 特徴量CSV: 42ファイル
- Borutaレポート: 42ファイル
- 重要度グラフ: 42ファイル

---

#### Phase 8ファイル確認

```cmd
REM モデルファイル数を確認
dir /b data\models\tuned\*.txt | find /c /v ""

REM ベストパラメータ数を確認
dir /b data\models\tuned\*.csv | find /c /v ""

REM 最適化履歴グラフ数を確認
dir /b data\models\tuned\*.png | find /c /v ""

REM 最適化レポート数を確認
dir /b data\models\tuned\*.json | find /c /v ""

REM 全ファイル一覧表示
dir /b data\models\tuned\*.*
```

**期待される出力**:
- モデルファイル（TXT）: 42ファイル
- ベストパラメータ（CSV）: 42ファイル
- 最適化履歴（PNG）: 42ファイル
- 最適化レポート（JSON）: 42ファイル
- **合計**: 168ファイル

---

#### Phase 5ファイル確認

```cmd
REM 予測結果CSV数を確認
dir /b data\predictions\phase5_optimized\*.csv | find /c /v ""

REM サマリーJSON数を確認
dir /b data\predictions\phase5_optimized\*.json | find /c /v ""

REM 全ファイル一覧表示
dir /b data\predictions\phase5_optimized\*.*
```

---

#### 特定会場のファイル確認（船橋の例）

```cmd
REM Phase 7: 船橋の特徴量ファイル
dir /b data\features\selected\funabashi*.csv

REM Phase 8: 船橋のモデルファイル
dir /b data\models\tuned\funabashi*.*

REM Phase 5: 船橋の予測結果
dir /b data\predictions\phase5_optimized\funabashi*.*
```

---

### PowerShell

#### Phase 7ファイル確認

```powershell
# 特徴量CSVファイル数を確認
(Get-ChildItem data\features\selected\*.csv).Count

# ファイルサイズ合計を確認
(Get-ChildItem data\features\selected\*.csv | Measure-Object -Property Length -Sum).Sum / 1MB

# Borutaレポート数を確認
(Get-ChildItem data\reports\phase7_feature_selection\*.txt).Count

# 重要度グラフ数を確認
(Get-ChildItem data\reports\phase7_feature_selection\*.png).Count
```

---

#### Phase 8ファイル確認

```powershell
# モデルファイル数とサイズを確認
Get-ChildItem data\models\tuned\*.txt | Measure-Object -Property Length -Sum | Select-Object Count, @{Name="TotalSizeMB";Expression={$_.Sum / 1MB}}

# 全ファイルタイプ別の統計
Get-ChildItem data\models\tuned\*.* | Group-Object Extension | Select-Object Name, Count
```

---

#### Phase 5ファイル確認

```powershell
# 予測結果CSV数を確認
(Get-ChildItem data\predictions\phase5_optimized\*.csv).Count

# 最新の予測結果を表示
Get-ChildItem data\predictions\phase5_optimized\*.csv | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

---

## ファイル整合性チェック

### Phase 7 → Phase 8の整合性確認

Phase 7で生成された特徴量ファイルが、Phase 8のモデル学習に正しく使われているかを確認します。

```cmd
REM 船橋のBinary用特徴量が存在するか
if exist data\features\selected\funabashi_selected_features.csv (
    echo [OK] Binary用特徴量ファイル存在
) else (
    echo [NG] Binary用特徴量ファイル不足
)

REM 船橋のBinary用モデルが存在するか
if exist data\models\tuned\funabashi_tuned_model.txt (
    echo [OK] Binary用モデルファイル存在
) else (
    echo [NG] Binary用モデルファイル不足
)
```

---

### Phase 8 → Phase 5の整合性確認

Phase 8で生成されたモデルファイルが揃っているかを確認します。

```cmd
REM 船橋の3モデルが全て存在するか
set VENUE=funabashi

if exist data\models\tuned\%VENUE%_tuned_model.txt (
    echo [OK] Binaryモデル存在
) else (
    echo [NG] Binaryモデル不足
)

if exist data\models\tuned\%VENUE%_ranking_tuned_model.txt (
    echo [OK] Rankingモデル存在
) else (
    echo [NG] Rankingモデル不足
)

if exist data\models\tuned\%VENUE%_regression_tuned_model.txt (
    echo [OK] Regressionモデル存在
) else (
    echo [NG] Regressionモデル不足
)
```

---

## まとめ

### 📊 ファイル生成統計

| フェーズ | ファイル数 | サイズ目安 | ディレクトリ |
|---------|----------|----------|------------|
| Phase 7 | 126 | 15-25 MB | `data/features/selected/`<br>`data/reports/phase7_feature_selection/` |
| Phase 8 | 168 | 25-140 MB | `data/models/tuned/` |
| Phase 5 | 変動 | 予測回数依存 | `data/predictions/phase5_optimized/` |
| **合計** | **294以上** | **40-165 MB以上** | - |

### ✅ 完了確認チェックリスト

Phase 7/8/5の実行が正常に完了したか、以下で確認してください：

- [ ] Phase 7特徴量CSV: 42ファイル（14会場 × 3モデル）
- [ ] Phase 7レポート: 84ファイル（14会場 × 3モデル × 2種類）
- [ ] Phase 8モデル: 168ファイル（14会場 × 3モデル × 4種類）
- [ ] Phase 5予測結果: 実行回数に応じたファイル数

全てのファイルが生成されていれば、**究極の競馬AIシステム構築完了**です！🎉
