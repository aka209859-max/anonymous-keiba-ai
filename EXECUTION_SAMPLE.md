# 🏇 実行サンプル：run_all_optimized.bat (新モデル Phase 7-8-5)

## 実行コマンド

```cmd
cd E:\anonymous-keiba-ai
run_all_optimized.bat 51 2026-02-12
```

---

## 実行時の出力サンプル

```
============================================================
地方競馬AI予想システム Phase 7-8-5統合版
============================================================
実行開始: 2026/02/12 08:00:00
競馬場: 姫路 (コード: 51)
対象日付: 2026-02-12
新モデル: Phase 7 Boruta特徴量選択 + Phase 8 Optuna最適化
Binary: 31特徴量 / Ranking: 25特徴量 / Regression: 24特徴量
============================================================

[Phase 0] データ取得中...
取得URL: https://nar.netkeiba.com/race/shutuba.html?race_id=202602513401
レース数: 12レース
保存先: data\raw\2026\02\姫路_20260212_raw.csv
レコード数: 135件
カラム数: 50列
[OK] Phase 0 Complete

[Phase 1] 特徴量生成中...
  Input: data\raw\2026\02\姫路_20260212_raw.csv
  Output: data\features\2026\02\姫路_20260212_features.csv
読み込み: 135行 × 50列
特徴量生成: 135行 × 50列（全馬）
[OK] Phase 1 Complete

[Phase 7 Binary] 予測実行中...
  Input: data\features\2026\02\姫路_20260212_features.csv
  Output: data\predictions\phase7_binary\姫路_20260212_phase7_binary.csv
使用モデル: data\models\tuned\himeji_binary_tuned_model.txt
特徴量数: 31 (Boruta選択後)
予測完了: 135頭
平均スコア: 0.6379
[OK] Phase 7 Binary Complete

[Phase 8 Ranking] 予測実行中...
  Input: data\features\2026\02\姫路_20260212_features.csv
  Output: data\predictions\phase8_ranking\姫路_20260212_phase8_ranking.csv
使用モデル: data\models\tuned\himeji_ranking_tuned_model.txt
特徴量数: 25 (Boruta選択後)
予測完了: 135頭
平均スコア: 0.5452
[OK] Phase 8 Ranking Complete

[Phase 8 Regression] 予測実行中...
  Input: data\features\2026\02\姫路_20260212_features.csv
  Output: data\predictions\phase8_regression\姫路_20260212_phase8_regression.csv
使用モデル: data\models\tuned\himeji_regression_tuned_model.txt
特徴量数: 24 (Boruta選択後)
予測完了: 135頭
平均時間: 1357.03秒
最速馬: 1番（1142.64秒）
[OK] Phase 8 Regression Complete

[Phase 5 Ensemble] 統合実行中...
  Binary Input: data\predictions\phase7_binary\姫路_20260212_phase7_binary.csv
  Ranking Input: data\predictions\phase8_ranking\姫路_20260212_phase8_ranking.csv
  Regression Input: data\predictions\phase8_regression\姫路_20260212_phase8_regression.csv
  Output: data\predictions\phase5\姫路_20260212_ensemble_optimized.csv
アンサンブル重み: Binary 30% / Ranking 50% / Regression 20%
統合完了: 135頭 / 12レース
[OK] Phase 5 Ensemble Complete

[Phase 6] 配信用テキスト生成中...
==================================================
Keiba AI Daily Operation
==================================================

Venue: 姫路 (Code: 51)
Date: 2026-02-12

Input : data\predictions\phase5\姫路_20260212_ensemble_optimized.csv
Output: predictions\姫路_20260212_note.txt
       predictions\姫路_20260212_bookers.txt
       predictions\姫路_20260212_tweet.txt
==================================================

[INFO] 馬名を取得中: data\raw\2026\02\姫路_20260212_raw.csv
[OK] 馬名マッピング作成完了: 135件

[1/3] Generating note.txt...
[OK] note.txt created

[2/3] Generating bookers.txt...
[OK] bookers.txt created

[3/3] Generating tweet.txt...
[OK] tweet.txt created

==================================================
Daily Operation Completed!
==================================================

Generated files:
  - predictions\姫路_20260212_note.txt
  - predictions\姫路_20260212_bookers.txt
  - predictions\姫路_20260212_tweet.txt

[OK] Phase 6 Complete

============================================================
全フェーズ完了 (Phase 7-8-5)
============================================================
実行終了: 2026/02/12 08:45:23

【出力ファイル一覧】

[予測CSVファイル]
  - Phase 7 Binary    : data\predictions\phase7_binary\姫路_20260212_phase7_binary.csv
  - Phase 8 Ranking   : data\predictions\phase8_ranking\姫路_20260212_phase8_ranking.csv
  - Phase 8 Regression: data\predictions\phase8_regression\姫路_20260212_phase8_regression.csv
  - Phase 5 Ensemble  : data\predictions\phase5\姫路_20260212_ensemble_optimized.csv

[配信用テキストファイル]
  ✓ Note用    : predictions\姫路_20260212_note.txt
  ✓ ブッカーズ用: predictions\姫路_20260212_bookers.txt
  ✓ Twitter用 : predictions\姫路_20260212_tweet.txt

============================================================

【ファイルを開く】
Noteファイルを開きますか？ (Enter で開く / Ctrl+C でスキップ)
```

---

## 生成されるファイル例

### 1. note.txt（Note用フォーマット）

```markdown
# 🏇 姫路競馬 AI予想

**開催日**: 2026年02月12日  
**対象レース**: 12R  

---

## 📋 予想結果一覧


## 🏇 第1R 予想

### 📊 予想順位

**1. 10番 アークリオーソ** （スコア: 0.80 / ランクS）
**2. 2番 ダズリングアイス** （スコア: 0.48 / ランクD）
**3. 6番 キンショーワールド** （スコア: 0.43 / ランクD）
4. 8番 ニシノフォーリーフ （スコア: 0.40 / ランクD）
5. 1番 ケイアイマヌカ （スコア: 0.38 / ランクD）
6. 4番 ヴァリオ （スコア: 0.36 / ランクD）
7. 7番 サンライズグレート （スコア: 0.33 / ランクD）
8. 3番 メイショウバイラン （スコア: 0.30 / ランクD）
9. 9番 ハシノオージャ （スコア: 0.21 / ランクD）
10. 5番 テーオーモンブラン （スコア: 0.04 / ランクD）

### 💰 購入推奨

**🎯 本命軸**
- 単勝: **10番**
- 複勝: **10番**、2番

**🔄 相手候補**
- 馬単: 10→2、2→10、10→6、6→10
- 三連複: 10-2-6-8-1 BOX
- 三連単: **10** → 2-6-8 → 2-6-8-1-4-7


---

（以下、第2R〜第12Rまで同様の形式）

---

## ⚠️ 注意事項

> 本予想はAIによる分析結果です。
> 投資判断は自己責任でお願いします。
> 過去の成績は将来の結果を保証するものではありません。

---

### 📌 ランク評価基準

- **S**: スコア0.80以上（最有力候補）
- **A**: スコア0.70-0.79（有力候補）
- **B**: スコア0.60-0.69（注目候補）
- **C**: スコア0.50-0.59（穴候補）
- **D**: スコア0.50未満（警戒候補）

---

*姫路競馬 2026年02月12日 開催分*  
*地方競馬AI予想システム v3*
```

### 2. bookers.txt（ブッカーズ用フォーマット）

```
🏇 【地方競馬AI】姫路競馬 全12R予想

📅 2026年02月12日(Thu)

本日はAI予想システムによる分析結果をお届けします。
過去の膨大なレースデータから、今日の馬場状態と出走馬の相性を完全数値化しました。

---


🏁 第1R 予想結果

🎯 AI推奨馬

◎ 10 アークリオーソ (ランクS)
AIスコア: 0.80

○ 2 ダズリングアイス (ランクD)
AIスコア: 0.48

▲ 6 キンショーワールド (ランクD)
AIスコア: 0.43

△ 8 ニシノフォーリーフ
△ 1 ケイアイマヌカ

💰 購入推奨（買い目）

【単勝/複勝】
・単勝：10
・複勝：10, 2

【馬単/馬連】
・10 ↔ 2, 6 (各2点)

【三連複/三連単】
・三連複：10-2-6-8-1 (BOX)
・三連単：10 → 2,6,8 → 2,6,8,1,4,7


---

（以下、第2R〜第12Rまで同様の形式）

---


⚠️ ご利用上の注意

本予想はAIによる統計分析に基づくデータです。
レース結果を保証するものではありません。
馬券購入は自己判断・自己責任でお願いいたします。

---

📌 ランク評価基準

S：スコア0.80以上（最有力）
A：スコア0.70-0.79（有力）
B：スコア0.60-0.69（注目）
C：スコア0.50-0.59（穴）
D：スコア0.50未満（警戒）

---

#姫路競馬 #AI予想 #地方競馬予想 #20260212
```

### 3. tweet.txt（Twitter用コピペフォーマット）

```
02/12（木）姫路1R
📊 購入推奨
・単勝: 10番
・複勝: 10番、2番
・馬単: 10→2、2→10、10→6、6→10
・三連複: 10.2.6.8.1 BOX
・三連単: 10→2.6.8→2.6.8.1.4.7

==================================================

02/12（木）姫路2R
📊 購入推奨
・単勝: 7番
・複勝: 7番、6番
・馬単: 7→6、6→7、7→10、10→7
・三連複: 7.6.10.1.5 BOX
・三連単: 7→6.10.1→6.10.1.5.3.8

==================================================

（以下、第3R〜第12Rまで同様の形式）
```

---

## ポイント

### ✅ 正しい出力形式

1. **note.txt**: Markdown形式で、馬名・スコア・ランク・購入推奨を詳細に記載
2. **bookers.txt**: ブッカーズ風のレイアウトで、印(◎○▲△)付きで表示
3. **tweet.txt**: Twitter投稿用の簡潔なコピペフォーマット

### ✅ 確認ポイント

- 各ファイルに**馬名が正しく表示**されている
- **スコアとランク**（S/A/B/C/D）が明記されている
- **購入推奨（単勝・複勝・馬単・三連複・三連単）**がレース毎に記載
- **日付フォーマット**が統一（MM/DD（曜日））
- **全12レース分**が正確に記載

### ✅ 旧モデル (run_all.bat) との違い

- **旧モデル**: Phase 3-4-5 → ensemble.csv → 同じフォーマットのテキスト生成
- **新モデル**: Phase 7-8-5 → ensemble_optimized.csv → 同じフォーマットのテキスト生成
- **出力形式は同一** - Phase 6 の生成スクリプトは共通

---

## トラブルシューティング

### 問題1: 「note.txt が生成されない」

**原因**: DAILY_OPERATION.bat の `cd /d E:\anonymous-keiba-ai` がハードコードされていた

**修正**: `cd /d "%~dp0..\.."` に変更（相対パス対応）

### 問題2: 「実行時の出力が以前と違う」

**原因**: Phase 6 のエラーメッセージが分かりにくかった

**修正**: エラーハンドリングを強化し、生成ファイルの存在確認を追加

### 問題3: 「ファイルの場所が分からない」

**修正**: 実行完了時に ✓/✗ で存在確認を表示し、自動的にNotepad で開くオプションを追加

---

## 実行後の確認コマンド

```cmd
REM 生成されたファイルを確認
dir predictions\姫路_20260212*.txt

REM Noteファイルを開く
notepad predictions\姫路_20260212_note.txt

REM 3ファイルすべてを開く
notepad predictions\姫路_20260212_note.txt
notepad predictions\姫路_20260212_bookers.txt
notepad predictions\姫路_20260212_tweet.txt
```

---

**【重要】** 今回の修正により、**旧モデル (run_all.bat)** も **新モデル (run_all_optimized.bat)** も、まったく同じ形式の note.txt / bookers.txt / tweet.txt を出力します。
