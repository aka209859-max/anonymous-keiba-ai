# 🔍 レース数不足問題の診断ガイド

## 📊 現状

### 検出された問題
- **総レース数**: 545レース（予測データ）
- **複勝率が異常に低い**:
  - 1位Sランク: 58.2%（期待値: 80%以上）
  - 2位Sランク: 52.2%（期待値: 80%以上）

### 原因候補
1. **PC-KEIBAデータベースに2026年データが無い**
2. **kaisai_tsukihi（開催月日）のフォーマット不一致**
3. **レースがまだ実施されていない（未来のレース）**

---

## 🛠️ 診断手順

### ステップ1: PC-KEIBAデータベースを確認

Windows側で以下のコマンドを実行してください：

```cmd
REM PostgreSQL起動確認
psql -U postgres -d pckeiba -c "SELECT 1;"

REM 2026年のデータ件数確認
psql -U postgres -d pckeiba -c "SELECT COUNT(*) FROM nvd_se WHERE kaisai_nen = '2026';"

REM 2026年2月のデータ確認
psql -U postgres -d pckeiba -c "SELECT COUNT(*) FROM nvd_se WHERE kaisai_nen = '2026' AND kaisai_tsukihi LIKE '02%';"

REM 2026年3月のデータ確認
psql -U postgres -d pckeiba -c "SELECT COUNT(*) FROM nvd_se WHERE kaisai_nen = '2026' AND kaisai_tsukihi LIKE '03%';"

REM サンプルデータ確認（kaisai_tsukihiの形式確認）
psql -U postgres -d pckeiba -c "SELECT kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango FROM nvd_se WHERE kaisai_nen = '2026' LIMIT 5;"
```

---

### ステップ2: デバッグ版スクリプトで詳細確認

最新版スクリプトには詳細なデバッグログが追加されています。

#### 実行方法

```cmd
cd E:\anonymous-keiba-ai

REM デバッグログ付きで実行
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 > debug_log.txt 2>&1

REM ログ確認
type debug_log.txt
```

#### 確認すべきログ内容

1. **実績データサンプル**
```
🔍 実績データサンプル:
   kaisai_nen例: 2026
   kaisai_tsukihi例: 213 (桁数: 3)  ← ここが重要！
   keibajo_code例: 43
```

2. **マージ統計**
```
🔍 マージ統計:
   予測データ: 6500 行
   実績データ: 8000 行
   マージ後: 3200 行 (49.2%)  ← 80%未満なら問題あり
```

3. **警告メッセージ**
```
⚠️  警告: マッチ率が低い (49.2%)です
   原因候補:
   1. PC-KEIBAに2026年データが無い
   2. kaisai_tsukihiのフォーマット不一致
   3. レースがまだ実施されていない（未来のレース）
   
   予測データ例:
   2026-0213-43-01
   
   実績データ例:
   2026-213-43-01  ← 桁数が違う！
```

---

## 🔧 解決方法

### 問題1: PC-KEIBAに2026年データが無い

**症状**:
```sql
SELECT COUNT(*) FROM nvd_se WHERE kaisai_nen = '2026';
-- 結果: 0
```

**解決策**:
1. PC-KEIBAで2026年のデータを取り込む
2. または、2025年のデータで分析する：
```cmd
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2025
```

---

### 問題2: kaisai_tsukihiのフォーマット不一致

**症状**:
- 予測データ: `kaisai_tsukihi = '0213'`（4桁、先頭ゼロあり）
- 実績データ: `kaisai_tsukihi = '213'`（3桁、先頭ゼロなし）

**原因**:
- race_idから抽出: `race_id.str[4:8]` → `'0213'`
- DBの形式: `'213'`

**解決策A**: スクリプト修正（先頭ゼロを削除）

修正箇所（216行目付近）:
```python
# 修正前
df_predictions['kaisai_tsukihi'] = df_predictions['race_id'].astype(str).str[4:8]

# 修正後（先頭ゼロを削除）
df_predictions['kaisai_tsukihi'] = df_predictions['race_id'].astype(str).str[4:8].str.lstrip('0')
```

**解決策B**: データベースのkaisai_tsukihiを4桁に変換

SQLで確認:
```sql
SELECT 
    kaisai_tsukihi,
    LPAD(kaisai_tsukihi, 4, '0') as kaisai_tsukihi_4digit
FROM nvd_se 
WHERE kaisai_nen = '2026' 
LIMIT 5;
```

---

### 問題3: 未来のレース

**症状**:
- 予測CSV: 2026年3月13日までのデータ
- 実績DB: 2026年2月28日までのデータ
- → 3月分がマッチしない

**解決策**:
月範囲を指定して実行：
```cmd
REM 2月のみ分析
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 --month 02-02
```

---

## 📝 診断チェックリスト

### □ ステップ1: PostgreSQL確認
```cmd
psql -U postgres -d pckeiba -c "SELECT COUNT(*) FROM nvd_se WHERE kaisai_nen = '2026';"
```
- [ ] 結果が0より大きい
- [ ] 2月・3月のデータが存在する

### □ ステップ2: kaisai_tsukihi形式確認
```cmd
psql -U postgres -d pckeiba -c "SELECT kaisai_tsukihi, LENGTH(kaisai_tsukihi) FROM nvd_se WHERE kaisai_nen = '2026' LIMIT 5;"
```
- [ ] 桁数を確認（3桁 or 4桁）

### □ ステップ3: デバッグログ確認
```cmd
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 > debug.txt 2>&1
type debug.txt
```
- [ ] 実績データ取得件数を確認
- [ ] マージ率を確認（80%以上が正常）
- [ ] 警告メッセージを確認

### □ ステップ4: 月範囲限定で再実行
```cmd
REM 実績データがある月のみ
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 --month 02-02
```
- [ ] マージ率が改善されるか確認

---

## 💡 最も可能性が高い原因

### kaisai_tsukihiのフォーマット不一致

**根拠**:
1. 予測データは545レース読み込み成功
2. 実績データ取得も成功しているはず
3. マージ後のレコード数が少ない → フォーマット不一致の可能性

**即効修正**:

```python
# scripts/evaluation/analyze_rank_fukusho_rate_from_db.py の216行目を修正
df_predictions['kaisai_tsukihi'] = df_predictions['race_id'].astype(str).str[4:8].str.lstrip('0')
```

または

```python
# 実績データ側を4桁にパディング（264行目を修正）
df_actuals['kaisai_tsukihi'] = df_actuals['kaisai_tsukihi'].astype(str).str.zfill(4)
```

---

## 🚀 推奨アクション

### 1. まず診断
```cmd
cd E:\anonymous-keiba-ai
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 > debug.txt 2>&1
type debug.txt
```

### 2. ログを確認
- `kaisai_tsukihi例`の桁数を確認
- マージ統計のマッチ率を確認

### 3. 結果を報告
以下の情報を共有してください：
1. PC-KEIBAの2026年データ件数
2. `kaisai_tsukihi`の桁数（3桁 or 4桁）
3. デバッグログの「マージ統計」部分

---

## 📞 サポート依頼テンプレート

```
【問題】
レース数が少なすぎる（545レース中、複勝率計算は一部のみ）

【実行環境】
- Python: (バージョン)
- PostgreSQL: (バージョン)
- PC-KEIBA: (バージョン)

【診断結果】
1. PostgreSQLの2026年データ件数: (件数)
2. kaisai_tsukihiの形式: (3桁 or 4桁)
3. デバッグログ:
   ```
   （マージ統計の部分を貼り付け）
   ```

【その他】
- 未来のレースを含むか: (はい/いいえ)
- 実施済みレースの日付範囲: (例: 2/1～2/28)
```

---

**次のステップ**: デバッグログを確認して、原因を特定してください！
