# Twitter投稿用コピペフォーマット - 使い方ガイド

## 🎯 概要

Twitter投稿用の簡潔なコピペフォーマットを自動生成します。

### 出力例

```
2/8（日）佐賀2R
📊 購入推奨
・単勝: 11番
・複勝: 11番、5番
・馬単: 11→5、5→11、11→12、12→11
・三連複: 11.5.12.6.3 BOX
・三連単: 11→5.12.6→5.12.6.3.1.8

==================================================

2/8（日）佐賀3R
📊 購入推奨
・単勝: 7番
・複勝: 7番、2番
・馬単: 7→2、2→7、7→4、4→7
・三連複: 7.2.4.9.1 BOX
・三連単: 7→2.4.9→2.4.9.1.5.8
```

---

## 📋 使い方

### ステップ1: Phase 0-5 を実行

```batch
cd E:\anonymous-keiba-ai

REM 佐賀競馬のデータ取得と予測
run_all.bat 55 2026-02-08
```

### ステップ2: Phase 6 実行（Twitter形式生成）

```batch
REM 単一競馬場
scripts\phase6_betting\DAILY_OPERATION.bat 55 2026-02-08

REM 複数競馬場一括処理
scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-08
```

### ステップ3: 生成ファイル確認

```batch
explorer predictions
```

生成されるファイル：
- `Saga_20260208_note.txt` - Note投稿用（詳細版）
- `Saga_20260208_bookers.txt` - ブッカーズ投稿用（詳細版）
- `Saga_20260208_tweet.txt` - **Twitter投稿用（簡潔版）** ← 新規追加！

---

## 🎨 Twitter投稿用フォーマットの特徴

### 1. 簡潔なレイアウト

- レース番号と日付を1行で表示
- 購入推奨のみに絞った情報
- コピペしやすい短文構成

### 2. 購入推奨の内訳

| 馬券種類 | 内容 |
|---------|------|
| **単勝** | 1位の馬番 |
| **複勝** | 1位、2位の馬番 |
| **馬単** | 1位↔2位、1位↔3位（各2点） |
| **三連複** | 上位5頭のBOX |
| **三連単** | 1位 → 2,3,4位 → 2,3,4,5,6,7位 |

### 3. フォーマット記号

- `→` : 馬単・三連単の軸（流し）
- `.` : BOX・相手馬の区切り
- `、` : 複勝など並列の区切り
- `↔` : 相互の組み合わせ

---

## 💡 活用方法

### Twitter投稿例

```
【佐賀競馬AI予想】

2/8（日）佐賀2R
📊 購入推奨
・単勝: 11番
・複勝: 11番、5番
・馬単: 11→5、5→11、11→12、12→11
・三連複: 11.5.12.6.3 BOX
・三連単: 11→5.12.6→5.12.6.3.1.8

#佐賀競馬 #AI予想 #地方競馬
```

### レース別に分けて投稿

```batch
REM ファイルを開く
notepad predictions\Saga_20260208_tweet.txt

REM レースごとに「==================================================」で区切られています
REM 投稿したいレースをコピーして、Twitter に貼り付け
```

### 全レース一括投稿（スレッド形式）

1. `Saga_20260208_tweet.txt` を開く
2. レース1を最初のツイートに投稿
3. 「返信」でレース2を投稿
4. 繰り返してスレッド形式で全レース投稿

---

## 🔧 カスタマイズ

### フォーマットを変更したい場合

編集対象ファイル：
```
scripts\phase6_betting\generate_distribution_tweet.py
```

主な編集箇所：

#### 1. レースヘッダーの変更（行 276-278）

```python
# 現在
lines.append(f"{formatted_date}{keibajo_name}{race_num}R")

# カスタマイズ例
lines.append(f"【{keibajo_name}】{formatted_date} 第{race_num}R")
```

#### 2. 購入推奨の見出し変更（行 150）

```python
# 現在
"📊 購入推奨",

# カスタマイズ例
"💰 本日の買い目",
```

#### 3. 馬単のフォーマット変更（行 169-174）

```python
# 現在
umatan_parts.extend([f"{h1}→{h2}", f"{h2}→{h1}"])

# カスタマイズ例（往復表記に変更）
umatan_parts.append(f"{h1}↔{h2}")
```

---

## 📊 3つのフォーマット比較

| 項目 | Note | Bookers | **Tweet** |
|------|------|---------|-----------|
| **用途** | Note投稿 | ブッカーズ投稿 | **Twitter投稿** |
| **文字数** | 多い（詳細） | 中程度 | **少ない（簡潔）** |
| **馬名** | 全頭表示 | トップ5 | **なし（番号のみ）** |
| **AIスコア** | 表示あり | 表示あり | **なし** |
| **ランク** | 表示あり | 表示あり | **なし** |
| **購入推奨** | 簡易版 | 詳細版 | **簡潔版** |
| **ハッシュタグ** | なし | あり | **手動追加推奨** |

---

## ✅ 毎日の運用フロー

```batch
cd E:\anonymous-keiba-ai

REM 1. Phase 0-5: データ取得と予測
run_all.bat 55 2026-02-08
run_all.bat 44 2026-02-08
run_all.bat 45 2026-02-08

REM 2. Phase 6: 配信用テキスト生成（Note, Bookers, Tweet）
scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-08

REM 3. ファイル確認
explorer predictions
```

### 生成ファイル一覧

```
predictions/
  ├── Saga_20260208_note.txt       ← Note投稿用
  ├── Saga_20260208_bookers.txt    ← ブッカーズ投稿用
  ├── Saga_20260208_tweet.txt      ← Twitter投稿用（NEW!）
  ├── Ooi_20260208_note.txt
  ├── Ooi_20260208_bookers.txt
  ├── Ooi_20260208_tweet.txt
  ├── Kawasaki_20260208_note.txt
  ├── Kawasaki_20260208_bookers.txt
  └── Kawasaki_20260208_tweet.txt
```

---

## 🚀 クイックスタート

### 最短3ステップ

```batch
REM 1. データ取得
cd E:\anonymous-keiba-ai && run_all.bat 55 2026-02-08

REM 2. テキスト生成
scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-08

REM 3. Twitter投稿用ファイルを開く
notepad predictions\Saga_20260208_tweet.txt
```

---

## 📝 投稿テンプレート

### パターン1: シンプル

```
【佐賀競馬AI予想】

（Saga_20260208_tweet.txt の内容をコピペ）

#佐賀競馬 #AI予想
```

### パターン2: 詳細版

```
🏇 本日の佐賀競馬AI予想

2/8（日）佐賀2R
📊 購入推奨
・単勝: 11番
・複勝: 11番、5番
・馬単: 11→5、5→11、11→12、12→11
・三連複: 11.5.12.6.3 BOX
・三連単: 11→5.12.6→5.12.6.3.1.8

⚠️ AI予想は参考情報です
馬券購入は自己責任でお願いします

#佐賀競馬 #AI予想 #地方競馬 #馬券予想
```

### パターン3: スレッド投稿

```
1/12 【佐賀競馬AI予想】2/8（日）

（レース1）

---

2/12 2R
📊 購入推奨
（以降、レースごとに返信で投稿）
```

---

## ❓ トラブルシューティング

### Q1: ファイルが生成されない

**A:** Phase 0-5 が完了しているか確認

```batch
REM Phase 5 の出力を確認
dir data\predictions\phase5\Saga_20260208_ensemble.csv

REM 存在しない場合は Phase 0-5 を再実行
run_all.bat 55 2026-02-08
```

### Q2: 文字化けする

**A:** メモ帳ではなく UTF-8 対応エディタで開く

- VS Code
- サクラエディタ
- TeraPad

### Q3: フォーマットをカスタマイズしたい

**A:** スクリプトを編集

```batch
notepad scripts\phase6_betting\generate_distribution_tweet.py
```

---

## 📞 サポート

質問や要望があれば、GitHub Issues で報告してください：
https://github.com/aka209859-max/anonymous-keiba-ai/issues

---

## 🎉 まとめ

Twitter投稿用のコピペフォーマットで、簡潔で分かりやすい予想を発信できます！

**特徴**
✅ 簡潔で読みやすい  
✅ コピペですぐ投稿可能  
✅ 全レース対応  
✅ 全14競馬場対応  

**次のステップ**
1. `BATCH_OPERATION.bat` を実行
2. `predictions\*_tweet.txt` を開く
3. Twitter に投稿！

Happy Posting! 🚀
