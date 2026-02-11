# 🎯 Phase 8 完了後の実行手順

**作成日**: 2026-02-11  
**目的**: Phase 8 完了後、既存の run_all.bat ワークフローで即座に予想を生成

---

## 📋 現状確認

### **既存ワークフロー**
```batch
run_all.bat [KEIBAJO_CODE] [DATE]
```

### **内部フロー**
1. **Phase 0**: データ取得 (`extract_race_data.py`)
2. **Phase 1**: 特徴量作成 (`prepare_features.py`)
3. **Phase 3**: Binary予測 (`predict_phase3_inference.py`)
4. **Phase 4-1**: Ranking予測 (`predict_phase4_ranking_inference.py`)
5. **Phase 4-2**: Regression予測 (`predict_phase4_regression_inference.py`)
6. **Phase 5**: アンサンブル統合 (`ensemble_predictions.py`) ← **旧モデル**
7. **Phase 6**: 配信用テキスト生成 (`DAILY_OPERATION.bat`)

---

## ⚠️ 重要な問題

### **現在の Phase 5 は旧モデルを使用**

```batch
REM run_all.bat の Phase 5 部分
python scripts\phase5_ensemble\ensemble_predictions.py "!OUTPUT_P3!" "!OUTPUT_P4_RANK!" "!OUTPUT_P4_REG!" "!OUTPUT_ENSEMBLE!"
```

**これは Phase 3-4-5 の旧モデルです！**

### **新モデル（Phase 7-8-5）を使う必要がある**

Phase 8 完了後は、**Phase 7-8 で最適化されたモデル**を使用する必要があります。

---

## 🎯 Phase 8 完了後の対応方針

### **方針1: run_all.bat を Phase 7-8-5 対応に更新（推奨）**

#### **変更点**
- Phase 3 → Phase 8 Binary を使用
- Phase 4-1 → Phase 8 Ranking を使用
- Phase 4-2 → Phase 8 Regression を使用
- Phase 5 → `ensemble_optimized.py` を使用

---

### **方針2: 新しい run_all_optimized.bat を作成**

既存の `run_all.bat` は保持したまま、Phase 7-8-5 用の新しいバッチファイルを作成。

---

## 🚀 推奨アクション（方針2）

### **新ファイル: `run_all_optimized.bat`**

```batch
@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

if "%~1"=="" (
    echo Usage: run_all_optimized.bat [KEIBAJO_CODE] [DATE]
    echo Example: run_all_optimized.bat 55 2026-02-12
    exit /b 1
)

if "%~2"=="" (
    echo Usage: run_all_optimized.bat [KEIBAJO_CODE] [DATE]
    echo Example: run_all_optimized.bat 55 2026-02-12
    exit /b 1
)

REM 引数処理
set "KEIBAJO_CODE=%~1"
set "KEIBAJO_CODE=%KEIBAJO_CODE: =%"
set "TARGET_DATE=%~2"
set "TARGET_DATE=%TARGET_DATE: =%"

for /f "tokens=1,2,3 delims=-" %%a in ("!TARGET_DATE!") do (
    set YEAR=%%a
    set MONTH=%%b
    set DAY=%%c
)
set "DATE_SHORT=!YEAR!!MONTH!!DAY!"

REM 競馬場コード→名前の変換
set "KEIBAJO_NAME="
if "!KEIBAJO_CODE!"=="30" set "KEIBAJO_NAME=門別"
if "!KEIBAJO_CODE!"=="35" set "KEIBAJO_NAME=盛岡"
if "!KEIBAJO_CODE!"=="36" set "KEIBAJO_NAME=水沢"
if "!KEIBAJO_CODE!"=="42" set "KEIBAJO_NAME=浦和"
if "!KEIBAJO_CODE!"=="43" set "KEIBAJO_NAME=船橋"
if "!KEIBAJO_CODE!"=="44" set "KEIBAJO_NAME=大井"
if "!KEIBAJO_CODE!"=="45" set "KEIBAJO_NAME=川崎"
if "!KEIBAJO_CODE!"=="46" set "KEIBAJO_NAME=金沢"
if "!KEIBAJO_CODE!"=="47" set "KEIBAJO_NAME=笠松"
if "!KEIBAJO_CODE!"=="48" set "KEIBAJO_NAME=名古屋"
if "!KEIBAJO_CODE!"=="50" set "KEIBAJO_NAME=園田"
if "!KEIBAJO_CODE!"=="51" set "KEIBAJO_NAME=姫路"
if "!KEIBAJO_CODE!"=="54" set "KEIBAJO_NAME=高知"
if "!KEIBAJO_CODE!"=="55" set "KEIBAJO_NAME=佐賀"

REM 競馬場コード→英語名の変換
set "VENUE_EN="
if "!KEIBAJO_CODE!"=="30" set "VENUE_EN=monbetsu"
if "!KEIBAJO_CODE!"=="35" set "VENUE_EN=morioka"
if "!KEIBAJO_CODE!"=="36" set "VENUE_EN=mizusawa"
if "!KEIBAJO_CODE!"=="42" set "VENUE_EN=urawa"
if "!KEIBAJO_CODE!"=="43" set "VENUE_EN=funabashi"
if "!KEIBAJO_CODE!"=="44" set "VENUE_EN=ooi"
if "!KEIBAJO_CODE!"=="45" set "VENUE_EN=kawasaki"
if "!KEIBAJO_CODE!"=="46" set "VENUE_EN=kanazawa"
if "!KEIBAJO_CODE!"=="47" set "VENUE_EN=kasamatsu"
if "!KEIBAJO_CODE!"=="48" set "VENUE_EN=nagoya"
if "!KEIBAJO_CODE!"=="50" set "VENUE_EN=sonoda"
if "!KEIBAJO_CODE!"=="51" set "VENUE_EN=himeji"
if "!KEIBAJO_CODE!"=="54" set "VENUE_EN=kochi"
if "!KEIBAJO_CODE!"=="55" set "VENUE_EN=saga"

if "!KEIBAJO_NAME!"=="" (
    echo [ERROR] Invalid venue code: !KEIBAJO_CODE!
    exit /b 1
)

echo ============================================================
echo 地方競馬AI予想システム（Phase 7-8-5 最適化版）
echo ============================================================
echo 実行開始: %DATE% %TIME%
echo 競馬場: !KEIBAJO_NAME! (コード: !KEIBAJO_CODE!)
echo 対象日付: !TARGET_DATE!
echo ============================================================
echo.

echo [Phase 0] データ取得中...
python scripts\phase0_data_acquisition\extract_race_data.py --keibajo !KEIBAJO_CODE! --date !TARGET_DATE!
if errorlevel 1 (
    echo [ERROR] Phase 0 失敗
    exit /b 1
)
echo [OK] Phase 0 完了
echo.

set "INPUT_CSV=data\raw\!YEAR!\!MONTH!\!KEIBAJO_NAME!_!DATE_SHORT!_raw.csv"
set "OUTPUT_CSV=data\features\!YEAR!\!MONTH!\!KEIBAJO_NAME!_!DATE_SHORT!_features.csv"

echo [Phase 1] 特徴量作成中...
python scripts\phase1_feature_engineering\prepare_features.py "!INPUT_CSV!" --output "!OUTPUT_CSV!"
if errorlevel 1 (
    echo [ERROR] Phase 1 失敗
    exit /b 1
)
echo [OK] Phase 1 完了
echo.

set "FEATURES_CSV=data\features\!YEAR!\!MONTH!\!KEIBAJO_NAME!_!DATE_SHORT!_features.csv"
set "OUTPUT_ENSEMBLE=data\predictions\phase5_optimized\!KEIBAJO_NAME!_!DATE_SHORT!_ensemble_optimized.csv"

echo [Phase 5] アンサンブル統合中（Phase 7-8-5 最適化版）...
python scripts\phase5_ensemble\ensemble_optimized.py !VENUE_EN! "!FEATURES_CSV!" --output-dir data\predictions\phase5_optimized
if errorlevel 1 (
    echo [ERROR] Phase 5 失敗
    exit /b 1
)
echo [OK] Phase 5 完了
echo.

REM Phase 5 出力ファイルの存在確認
if not exist "!OUTPUT_ENSEMBLE!" (
    echo [ERROR] Phase 5 output not found: !OUTPUT_ENSEMBLE!
    exit /b 1
)
echo [DEBUG] Phase 5 output confirmed: !OUTPUT_ENSEMBLE!
echo.

REM Phase 6: 配信用ファイル生成
echo [Phase 6] 配信用ファイル生成中（Note/Bookers/Tweet）...
call scripts\phase6_betting\DAILY_OPERATION.bat !KEIBAJO_CODE! !TARGET_DATE!
if errorlevel 1 (
    echo [ERROR] Phase 6 失敗
    exit /b 1
)
echo [OK] Phase 6 完了
echo.

echo ============================================================
echo 全フェーズ完了（Phase 7-8-5 最適化版）
echo ============================================================
echo.
echo 予想結果: !OUTPUT_ENSEMBLE!
echo.
echo 配信用ファイル:
echo   - predictions\!KEIBAJO_NAME!_!DATE_SHORT!_note.txt
echo   - predictions\!KEIBAJO_NAME!_!DATE_SHORT!_bookers.txt
echo   - predictions\!KEIBAJO_NAME!_!DATE_SHORT!_tweet.txt
echo.
echo ============================================================

endlocal
```

---

## 📝 Phase 8 完了後の実行コマンド

### **従来通りの実行方法**

```batch
cd E:\anonymous-keiba-ai

REM Phase 7-8-5 最適化版を使用
run_all_optimized.bat 43 2026-02-13
run_all_optimized.bat 48 2026-02-13
run_all_optimized.bat 51 2026-02-13
run_all_optimized.bat 55 2026-02-13

REM Phase 6: 配信用テキスト一括生成
scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-12

REM 確認
explorer predictions
```

---

## ⚠️ 注意事項

### **Phase 6 (DAILY_OPERATION.bat) の調整が必要**

Phase 6 が Phase 5 の出力ファイルを参照しているため、以下を確認：

1. **入力ファイルパス**
   - 旧: `data\predictions\phase5\{venue}_{date}_ensemble.csv`
   - 新: `data\predictions\phase5_optimized\{venue}_{date}_ensemble_optimized.csv`

2. **カラム名**
   - 旧: `ensemble_score`, `predicted_rank`
   - 新: `ensemble_score`, `final_rank`, `binary_probability`, `ranking_score`, `predicted_time`

---

## 🎯 次のアクション

### **Phase 8 完了後、すぐに実行**

1. **run_all_optimized.bat を作成**
   - 上記のコードをコピー
   - `E:\anonymous-keiba-ai\run_all_optimized.bat` として保存

2. **Phase 6 の調整確認**
   - `scripts\phase6_betting\DAILY_OPERATION.bat` を確認
   - Phase 5 の出力ファイルパスを確認

3. **テスト実行**
   ```batch
   run_all_optimized.bat 43 2026-02-13
   ```

4. **出力確認**
   ```batch
   type predictions\船橋_20260213_tweet.txt
   type predictions\船橋_20260213_note.txt
   ```

---

## 📊 まとめ

| 項目 | 旧 (run_all.bat) | 新 (run_all_optimized.bat) |
|------|-----------------|---------------------------|
| Phase 3 | Phase 3 Binary | （スキップ） |
| Phase 4 | Phase 4 Ranking/Regression | （スキップ） |
| Phase 5 | ensemble_predictions.py | **ensemble_optimized.py** |
| モデル | Phase 3-4-5 | **Phase 7-8-5** |
| 出力 | phase5/*.csv | **phase5_optimized/*.csv** |

**Phase 8 完了後は、`run_all_optimized.bat` を使用してください！**

---

**Phase 7 Ranking 実行中... 完了をお待ちください 🚀**
