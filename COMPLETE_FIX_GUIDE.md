# 完全修復ガイド - 地方競馬AI予想システム

## 📋 現状の問題と根本原因

### 🔴 発見された問題
1. **バッチファイルの文字化け** - UTF-8 BOMエンコーディングがWindows cmd.exeで正しく解析されない
2. **モデルファイルパスの不一致** - スクリプトが`data\models\tuned`を探すが、実際は`data\models\tuned\*.txt`形式で存在
3. **ファイル名の不一致** - Phase 0が日本語名でCSVを出力するが、Phase 1が英語名を期待
4. **モデルファイル数の確認不足** - 14競馬場×3モデル=42ファイルが全て存在するか未確認

### ✅ 確認済みの事実
- ✅ モデルファイルは`E:\anonymous-keiba-ai\data\models\tuned\`に存在
- ✅ ファイル形式: `{venue_romaji}_tuned_model.txt` (Binary), `{venue_romaji}_ranking_tuned_model.txt`, `{venue_romaji}_regression_tuned_model.txt`
- ✅ 予測スクリプトは正しくローマ字でモデルファイルを探す
- ✅ Phase 0は日本語の競馬場名でCSVを出力
- ⚠️ バッチファイルがUTF-8 BOMで保存されており、cmd.exeが誤認識

---

## 🎯 完全修復手順

### ステップ1: モデルファイルの確認

```cmd
cd E:\anonymous-keiba-ai\data\models\tuned

REM Binary モデル数を確認（期待値: 14）
dir *_tuned_model.txt /b | find /c ".txt"

REM Ranking モデル数を確認（期待値: 14）
dir *_ranking_tuned_model.txt /b | find /c ".txt"

REM Regression モデル数を確認（期待値: 14）
dir *_regression_tuned_model.txt /b | find /c ".txt"

REM 全ファイルをリスト表示
dir *.txt /b | sort
```

**期待される出力:**
```
14  (Binary)
14  (Ranking)
14  (Regression)

funabashi_ranking_tuned_model.txt
funabashi_regression_tuned_model.txt
funabashi_tuned_model.txt
himeji_ranking_tuned_model.txt
himeji_regression_tuned_model.txt
himeji_tuned_model.txt
... (全42ファイル)
```

### ステップ2: PowerShellスクリプトでバッチファイルを再作成

#### 方法A: PowerShellスクリプトをダウンロードして実行

1. **サンドボックスからダウンロード:**
   - ファイル: `/home/user/webapp/anonymous-keiba-ai/CREATE_BATCH_POWERSHELL.ps1`
   - 保存先: `E:\anonymous-keiba-ai\CREATE_BATCH_POWERSHELL.ps1`

2. **PowerShellで実行:**
```powershell
cd E:\anonymous-keiba-ai
.\CREATE_BATCH_POWERSHELL.ps1
```

3. **結果確認:**
```cmd
cd E:\anonymous-keiba-ai
dir run_all_optimized.bat
```

#### 方法B: 直接PowerShellコマンドで作成

```powershell
cd E:\anonymous-keiba-ai

# 既存のバッチファイルをバックアップ
if (Test-Path "run_all_optimized.bat") {
    Copy-Item "run_all_optimized.bat" "run_all_optimized.bat.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Remove-Item "run_all_optimized.bat"
}

# 上記のPowerShellスクリプト内容を実行
# (CREATE_BATCH_POWERSHELL.ps1 の内容をコピー&ペーストして実行)
```

### ステップ3: バッチファイルの動作テスト

```cmd
cd E:\anonymous-keiba-ai
run_all_optimized.bat 43 2026-02-13
```

**期待される動作フロー:**
```
[Phase 0] データ取得中...
  → data\raw\2026\02\船橋_20260213_raw.csv を作成

[Phase 1] 特徴量生成中...
  → data\features\2026\02\船橋_20260213_features.csv を作成

[Phase 7 Binary] 予測実行中...
  → data\predictions\phase7_binary\船橋_20260213_phase7_binary.csv を作成

[Phase 8 Ranking] 予測実行中...
  → data\predictions\phase8_ranking\船橋_20260213_phase8_ranking.csv を作成

[Phase 8 Regression] 予測実行中...
  → data\predictions\phase8_regression\船橋_20260213_phase8_regression.csv を作成

[Phase 5 Ensemble] 統合実行中...
  → data\predictions\phase5\船橋_20260213_ensemble_optimized.csv を作成

[Phase 6] 配信用テキスト生成中...
  → predictions\船橋_20260213_note.txt を作成
  → predictions\船橋_20260213_bookers.txt を作成
  → predictions\船橋_20260213_tweet.txt を作成

[OK] 全フェーズ完了
```

### ステップ4: 全競馬場での動作確認

```cmd
cd E:\anonymous-keiba-ai

REM 南関東4場のテスト
run_all_optimized.bat 42 2026-02-14  :: 浦和
run_all_optimized.bat 43 2026-02-14  :: 船橋
run_all_optimized.bat 44 2026-02-14  :: 大井
run_all_optimized.bat 45 2026-02-14  :: 川崎

REM その他主要競馬場
run_all_optimized.bat 55 2026-02-14  :: 佐賀
run_all_optimized.bat 54 2026-02-14  :: 高知
run_all_optimized.bat 48 2026-02-14  :: 名古屋
```

---

## 📊 問題のトラブルシューティング

### 問題1: Phase 0が成功するが Phase 1が失敗

**症状:**
```
[Phase 0] OK
[Phase 1] ERROR - File not found: data\raw\2026\02\Funabashi_20260213_raw.csv
```

**原因:**
Phase 0が日本語名でCSVを出力: `船橋_20260213_raw.csv`  
Phase 1が英語名を期待: `Funabashi_20260213_raw.csv`

**解決策 (一時的):**
```cmd
cd E:\anonymous-keiba-ai\data\raw\2026\02
copy 船橋_20260213_raw.csv Funabashi_20260213_raw.csv
cd E:\anonymous-keiba-ai
run_all_optimized.bat 43 2026-02-13
```

**解決策 (根本的):**
`scripts\phase0_data_acquisition\extract_race_data.py` を確認し、出力ファイル名を日本語に統一する。

### 問題2: Phase 7/8でモデルファイルが見つからない

**症状:**
```
[Phase 7 Binary] ERROR - Model file not found: data\models\tuned\lgb_binary_43_optimized.txt
```

**原因:**
スクリプトが間違ったファイル名を探している。

**確認コマンド:**
```cmd
cd E:\anonymous-keiba-ai
type scripts\phase7_binary\predict_optimized_binary.py | findstr /N "model_filename"
```

**期待される内容:**
```python
model_filename = f"{venue_romaji}_tuned_model.txt"
model_path = os.path.join(model_dir, model_filename)
```

**もし異なる場合は、スクリプトを修正する必要があります。**

### 問題3: Phase 6で配信用テキストが作成されない

**症状:**
```
[Phase 6] WARNING - Phase 6 ERROR
[INFO] Manual execution:
  scripts\phase6_betting\DAILY_OPERATION.bat 43 2026-02-13 "data\predictions\phase5\船橋_20260213_ensemble_optimized.csv"
```

**解決策:**
```cmd
cd E:\anonymous-keiba-ai
call scripts\phase6_betting\DAILY_OPERATION.bat 43 2026-02-13 "data\predictions\phase5\船橋_20260213_ensemble_optimized.csv"
```

---

## 🔬 精度低下の原因調査

### 調査ステップ1: モデルファイルの特徴量数を確認

```cmd
cd E:\anonymous-keiba-ai
type data\models\tuned\funabashi_tuned_model.txt | findstr /C:"num_features"
```

**期待値:** 25～35特徴量

**もし10特徴量未満の場合:**
- Borutaが特徴量を過剰に削除している可能性
- 再トレーニングが必要

### 調査ステップ2: 旧モデルと新モデルの比較

```cmd
cd E:\anonymous-keiba-ai

REM 旧モデルで予測
run_all.bat 43 2026-02-13

REM 新モデルで予測
run_all_optimized.bat 43 2026-02-13

REM 結果比較
python -c "import pandas as pd; old=pd.read_csv('data/predictions/phase5/船橋_20260213_ensemble.csv'); new=pd.read_csv('data/predictions/phase5/船橋_20260213_ensemble_optimized.csv'); print('旧モデル上位3頭:'); print(old.nlargest(3, 'ensemble_score')[['race_bango','umaban','ensemble_score']]); print('\n新モデル上位3頭:'); print(new.nlargest(3, 'ensemble_score')[['race_bango','umaban','ensemble_score']])"
```

### 調査ステップ3: アンサンブル重みの確認

```cmd
cd E:\anonymous-keiba-ai
type scripts\phase5_ensemble\ensemble_optimized.py | findstr /N "weight"
```

**期待される重み:**
```python
binary_weight = 0.4
ranking_weight = 0.3
regression_weight = 0.3
```

**もし全て0.33の場合:**
重み最適化が機能していない可能性。

---

## 🚀 次のアクション

### 即座に実行すべきこと (優先度: 高)

1. **ステップ1を実行** - モデルファイルの存在確認
2. **ステップ2を実行** - PowerShellスクリプトでバッチファイルを再作成
3. **ステップ3を実行** - 船橋競馬場でテスト実行
4. **結果を報告** - 成功/失敗のログを共有

### 中期的に対応すべきこと (優先度: 中)

1. **全14競馬場のテスト実行**
2. **旧モデルとの精度比較**
3. **Phase 6の安定化**

### 長期的に改善すべきこと (優先度: 低)

1. **バッチファイルのShift-JIS化** (現在UTF-8 BOM)
2. **ファイル名の統一** (日本語 vs 英語)
3. **エラーハンドリングの強化**

---

## 📝 チェックリスト

実行前に以下を確認してください:

- [ ] モデルファイルが`E:\anonymous-keiba-ai\data\models\tuned\`に42個存在
- [ ] PowerShellスクリプトで`run_all_optimized.bat`を再作成
- [ ] 船橋競馬場 (43) でテスト実行が成功
- [ ] Phase 0～6まで全てエラーなく完了
- [ ] 配信用テキストファイル (note.txt, bookers.txt, tweet.txt) が作成

---

## 🆘 サポートが必要な場合

以下の情報を提供してください:

1. **実行コマンド:**
   ```
   run_all_optimized.bat 43 2026-02-13
   ```

2. **エラーメッセージ:** (コピー&ペースト)

3. **ファイル存在確認:**
   ```cmd
   dir data\models\tuned\funabashi*.txt
   dir data\raw\2026\02\*.csv
   dir data\predictions\phase5\*.csv
   ```

4. **スクリプトの内容確認:**
   ```cmd
   type scripts\phase7_binary\predict_optimized_binary.py | findstr /N "model"
   ```

---

**作成日:** 2026-02-14  
**バージョン:** 1.0  
**対象システム:** 地方競馬AI予想システム Phase 7-8-5統合版
