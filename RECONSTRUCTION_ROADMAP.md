# 地方競馬AI予想システム Phase 7-8-5 再構築ロードマップ
## 根本的エンコーディング問題解決版

---

## 📋 エグゼクティブサマリー

### 問題の本質
Windowsバッチファイル `run_all_optimized.bat` が「NCODINGエラー」で実行不可能な状態に陥っていた。
根本原因は以下の2つの技術的負債：

1. **BOM（Byte Order Mark）問題**: UTF-8 with BOM（0xEF 0xBB 0xBF）がcmd.exeに誤認識され、`'NCODING'` などのコマンドとして解釈される
2. **chcp 65001バッファ不整合バグ**: バッチファイル実行中にコードページを切り替えると、ファイルポインタがずれてプロセスが停止・誤動作する

### 解決策
**自己再入（リエントラント）構造** を採用した新しいバッチファイルアーキテクチャにより、これらの問題を完全に回避。

---

## 🎯 ロードマップ概要

### フェーズ1: 緊急修復（即日実施）
- ✅ 技術報告書によるエンコーディング問題の完全解明
- 🔧 修正版バッチファイルの作成と配備
- 🧪 14競馬場での動作確認

### フェーズ2: システム安定化（1-3日）
- 📊 旧モデル vs 新モデルの精度比較
- 🔍 モデルファイルの正常性検証
- 📝 運用手順書の整備

### フェーズ3: 完全自動化（1週間）
- 🤖 14競馬場バッチ実行スクリプトの作成
- 📅 スケジューラー設定
- 🚨 エラー通知システムの構築

### フェーズ4: 拡張機能（2-4週間）
- 🎯 トリプル馬単システムの実装
- 📈 予測精度の継続的改善
- 🔄 自動学習パイプラインの構築

---

## 📁 ファイル構成

### 新規作成ファイル

```
E:\anonymous-keiba-ai\
├── run_all_optimized_FIXED.bat      # 修正版メインバッチ（UTF-8 BOM無し）
├── run_all_14_venues.bat            # 14競馬場一括実行
├── verify_models.bat                # モデルファイル検証
├── docs\
│   ├── ENCODING_FIX_REPORT.md       # 技術報告書（日本語版）
│   ├── RECONSTRUCTION_ROADMAP.md    # 本ロードマップ
│   └── OPERATION_MANUAL.md          # 運用手順書
└── tools\
    ├── check_encoding.ps1            # エンコーディング検証ツール
    └── compare_predictions.py        # 予測結果比較ツール
```

---

## 🔧 フェーズ1: 緊急修復（即日実施）

### ステップ1.1: 修正版バッチファイルの作成

#### ファイル: `run_all_optimized_FIXED.bat`

**重要な修正ポイント:**

1. **自己再入構造の実装**
```batch
chcp 65001 > nul
if "%~1"=="__REENTRY__" goto :MAIN_LOGIC
cmd /c "%~f0" __REENTRY__ %*
exit /b
```
- 最初に `chcp 65001` を実行してUTF-8モードに切り替え
- 即座に新しいcmd.exeプロセスで自分自身を再起動
- 新プロセスは最初からUTF-8で正しく解析される

2. **厳密なエンコーディング指定**
- ファイル保存形式: **UTF-8 BOM無し**
- 改行コード: **CRLF**（Windows標準）

3. **完全な競馬場コードマッピング**
```batch
if "%KEIBAJO_CODE%"=="30" set "KEIBAJO_NAME=門別"
if "%KEIBAJO_CODE%"=="35" set "KEIBAJO_NAME=盛岡"
...（全14競馬場）
if "%KEIBAJO_CODE%"=="55" set "KEIBAJO_NAME=佐賀"
```

### ステップ1.2: VS Codeでの正しい保存手順

1. **新規ファイル作成**: `run_all_optimized_FIXED.bat`
2. **コードを貼り付け**: 技術報告書のコードをコピー
3. **エンコーディング設定**:
   - 右下ステータスバーをクリック
   - 「エンコーディング付きで保存」
   - 「UTF-8」を選択（**「UTF-8 with BOM」ではない**）
4. **改行コード設定**:
   - 右下「LF」または「CRLF」をクリック
   - 「CRLF」を選択
5. **保存**: Ctrl+S

### ステップ1.3: PowerShellでの検証

```powershell
cd E:\anonymous-keiba-ai

# エンコーディング確認（BOMが無いことを確認）
Get-Content run_all_optimized_FIXED.bat -Encoding Byte | Select-Object -First 3 | ForEach-Object { '{0:X2}' -f $_ }
# 期待値: 52 45 4D (BOMなしでREMから始まる)

# 改行コード確認
(Get-Content run_all_optimized_FIXED.bat -Raw).Contains("`r`n")
# 期待値: True (CRLFが使われている)
```

### ステップ1.4: テスト実行

```cmd
cd E:\anonymous-keiba-ai

REM バックアップ
ren run_all_optimized.bat run_all_optimized.bat.broken

REM 新バージョン配置
copy run_all_optimized_FIXED.bat run_all_optimized.bat

REM テスト実行（船橋）
run_all_optimized.bat 43 2026-02-13

REM 結果確認
dir data\predictions\phase5\船橋_20260213_ensemble_optimized.csv
dir predictions\船橋_20260213_*.txt
```

**成功条件:**
- ✅ エンコーディングエラーが出ない
- ✅ Phase 0-6 が全て完了
- ✅ 日本語の競馬場名が正しく表示される
- ✅ 配信用テキストファイルが生成される

---

## 📊 フェーズ2: システム安定化（1-3日）

### ステップ2.1: 全14競馬場での動作確認

#### ファイル: `verify_all_venues.bat`

```batch
@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

set TEST_DATE=2026-02-14
set VENUES=30 35 36 42 43 44 45 46 47 48 50 51 54 55

echo ============================================================
echo 14競馬場 動作確認テスト
echo ============================================================

for %%V in (%VENUES%) do (
    echo.
    echo [TEST] 競馬場コード: %%V
    call run_all_optimized.bat %%V %TEST_DATE%
    if errorlevel 1 (
        echo [FAIL] 競馬場コード %%V で失敗
        pause
    ) else (
        echo [OK] 競馬場コード %%V 成功
    )
)

echo.
echo ============================================================
echo 全競馬場テスト完了
echo ============================================================
pause
```

### ステップ2.2: モデルファイルの正常性検証

```cmd
cd E:\anonymous-keiba-ai

REM 全モデルファイルの存在確認
dir data\models\tuned\*_tuned_model.txt /b | find /c ".txt"
REM 期待値: 14

dir data\models\tuned\*_ranking_tuned_model.txt /b | find /c ".txt"
REM 期待値: 14

dir data\models\tuned\*_regression_tuned_model.txt /b | find /c ".txt"
REM 期待値: 14

REM 合計42ファイルの確認
dir data\models\tuned\*.txt /b | find /c ".txt"
REM 期待値: 42
```

### ステップ2.3: 旧モデル vs 新モデルの精度比較

#### ファイル: `compare_predictions.py`

```python
import pandas as pd
import sys

def compare_models(venue, date):
    old_file = f"data/predictions/phase5/{venue}_{date}_ensemble.csv"
    new_file = f"data/predictions/phase5/{venue}_{date}_ensemble_optimized.csv"
    
    try:
        old = pd.read_csv(old_file)
        new = pd.read_csv(new_file)
        
        print(f"=== {venue} {date} 比較 ===")
        print(f"旧モデル上位3頭:")
        print(old.nlargest(3, 'ensemble_score')[['race_bango', 'umaban', 'bamei', 'ensemble_score']])
        print(f"\n新モデル上位3頭:")
        print(new.nlargest(3, 'ensemble_score')[['race_bango', 'umaban', 'bamei', 'ensemble_score']])
        
        # スコア分布の比較
        print(f"\n旧モデル スコア統計:")
        print(old['ensemble_score'].describe())
        print(f"\n新モデル スコア統計:")
        print(new['ensemble_score'].describe())
        
    except FileNotFoundError as e:
        print(f"エラー: ファイルが見つかりません - {e}")

if __name__ == "__main__":
    compare_models("船橋", "20260213")
```

実行:
```cmd
python tools\compare_predictions.py
```

---

## 🤖 フェーズ3: 完全自動化（1週間）

### ステップ3.1: 14競馬場一括実行スクリプト

#### ファイル: `run_all_14_venues.bat`

```batch
@echo off
chcp 65001 > nul
if "%~1"=="__REENTRY__" goto :MAIN_LOGIC
cmd /c "%~f0" __REENTRY__ %*
exit /b

:MAIN_LOGIC
shift /1
setlocal enabledelayedexpansion

set TARGET_DATE=%~1
if "%TARGET_DATE%"=="" set TARGET_DATE=%DATE:~0,4%-%DATE:~5,2%-%DATE:~8,2%

set VENUES=30 35 36 42 43 44 45 46 47 48 50 51 54 55

echo ============================================================
echo 地方競馬AI予想システム 14競馬場一括実行
echo ============================================================
echo 実行日: %TARGET_DATE%
echo ============================================================

for %%V in (%VENUES%) do (
    echo.
    echo [実行中] 競馬場コード: %%V
    call run_all_optimized.bat %%V %TARGET_DATE%
    
    if errorlevel 1 (
        echo [エラー] 競馬場コード %%V で失敗
        echo 続行しますか？ (Y/N)
        set /p CONTINUE=
        if /i not "!CONTINUE!"=="Y" exit /b 1
    ) else (
        echo [完了] 競馬場コード %%V
    )
)

echo.
echo ============================================================
echo 全競馬場の予想が完了しました
echo ============================================================

REM 結果サマリー
echo.
echo [生成された予測ファイル]
dir data\predictions\phase5\*_ensemble_optimized.csv /b

endlocal
pause
```

### ステップ3.2: タスクスケジューラー設定

**毎日自動実行の設定:**

```powershell
# PowerShellでタスク作成
$action = New-ScheduledTaskAction -Execute "E:\anonymous-keiba-ai\run_all_14_venues.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At "06:00AM"
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "地方競馬AI予想_毎日実行" -Action $action -Trigger $trigger -Principal $principal -Settings $settings
```

---

## 🔍 フェーズ4: 拡張機能（2-4週間）

### ステップ4.1: 精度低下の原因調査

#### 調査項目

1. **モデルの特徴量数確認**
```cmd
cd E:\anonymous-keiba-ai\data\models\tuned
type funabashi_tuned_model.txt | findstr "num_features"
```
期待値: 25～35特徴量（10未満の場合はBoruta過剰削除の疑い）

2. **アンサンブル重みの確認**
```cmd
type scripts\phase5_ensemble\ensemble_optimized.py | findstr "weight"
```
期待値:
- binary_weight = 0.4
- ranking_weight = 0.3
- regression_weight = 0.3

3. **ハイパーパラメータの確認**
- learning_rate: 0.01～0.1（高すぎると過学習）
- max_depth: 3～8（深すぎると過学習）
- num_leaves: 20～100（多すぎると過学習）

### ステップ4.2: トリプル馬単システムの実装

**別プロジェクトとして管理:**
```
E:\anonymous-keiba-ai-triple\
├── scripts\phase0_triple_data_acquisition\
│   ├── extract_triple_historical.py
│   ├── extract_triple_today.py
│   └── scrape_carryover.py
├── data\
│   ├── raw\historical\
│   ├── raw\prediction\
│   └── carryover\
└── keiba_triple.db
```

---

## ✅ 成功基準とKPI

### 即時目標（フェーズ1）
- ✅ `run_all_optimized.bat` がエンコーディングエラーなく実行できる
- ✅ 船橋競馬場でPhase 0-6が完全に動作する
- ✅ 配信用テキストファイルが生成される

### 短期目標（フェーズ2-3）
- ✅ 14競馬場全てで安定動作する
- ✅ 旧モデルと新モデルの予測精度を数値比較できる
- ✅ 毎日自動実行が設定されている

### 中長期目標（フェーズ4）
- 🎯 的中率が旧モデルより向上する
- 🎯 トリプル馬単システムが稼働する
- 🎯 自動学習パイプラインが構築される

---

## 📝 運用チェックリスト

### 毎日の運用
- [ ] 前日のバッチ実行ログを確認
- [ ] エラーがあれば原因を調査
- [ ] 予測CSVファイルが生成されているか確認
- [ ] 配信用テキストを各プラットフォームに投稿

### 週次の運用
- [ ] 14競馬場全ての予測精度を集計
- [ ] モデルの再学習が必要か判断
- [ ] システムログのバックアップ

### 月次の運用
- [ ] 月間的中率・回収率のレポート作成
- [ ] モデルのアップデート検討
- [ ] 新機能の開発計画レビュー

---

## 🆘 トラブルシューティング

### エンコーディングエラーが再発した場合

```powershell
# ファイルのエンコーディング確認
Get-Content run_all_optimized.bat -Encoding Byte | Select-Object -First 3

# 期待値: 52 45 4D (REM の ASCII)
# NG値: EF BB BF (UTF-8 BOM)
```

**対処法**: VS Codeで「UTF-8」（BOM無し）で再保存

### Phase 7/8でモデルが見つからない場合

```cmd
# モデルファイルの存在確認
dir data\models\tuned\funabashi*.txt

# 期待値: 3ファイル（binary, ranking, regression）
```

**対処法**: モデルファイル名が `{venue_romaji}_tuned_model.txt` 形式になっているか確認

### Phase 6で配信テキストが生成されない場合

```cmd
# 手動実行
cd E:\anonymous-keiba-ai
call scripts\phase6_betting\DAILY_OPERATION.bat 43 2026-02-13 "data\predictions\phase5\船橋_20260213_ensemble_optimized.csv"
```

---

## 📚 参考資料

### 作成済みドキュメント
1. `ENCODING_FIX_REPORT.md` - エンコーディング問題の技術報告書
2. `RECONSTRUCTION_ROADMAP.md` - 本ロードマップ
3. `DEEPSEARCH_BATCH_FIX_REQUEST.md` - 他AI依頼用の仕様書
4. `COMPLETE_FIX_GUIDE.md` - 完全修復ガイド

### 外部リンク
- [Microsoft Docs: chcp コマンド](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/chcp)
- [UTF-8 BOM の問題](https://stackoverflow.com/questions/17218684/utf-8-bom-in-batch-files)
- [cmd.exe の既知の問題](https://ss64.com/nt/syntax-issues.html)

---

**作成日**: 2026-02-14  
**バージョン**: 2.0  
**ステータス**: 実装準備完了  
**優先度**: 🔴 最高  
**担当**: anonymous競馬AIシステム開発チーム
