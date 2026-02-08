# 🎯 クイックリファレンス - 他AI調査依頼

## 📋 依頼文（コピペ用）

### パターン1: 完全版（推奨）

```
Anonymous Keiba AIプロジェクトのデータベーススキーマ不整合を調査してください。
ハルシネーションなしで、GitHubリポジトリとデータベースを実際に確認してください。

【重要リンク】
- GitHubリポジトリ: https://github.com/aka209859-max/anonymous-keiba-ai
- ブランチ: phase4_specialized_models
- プルリクエスト: https://github.com/aka209859-max/anonymous-keiba-ai/pull/3

【調査依頼書】
リポジトリの INSTRUCTION_FOR_OTHER_AI.md に完全な調査指示があります。
https://github.com/aka209859-max/anonymous-keiba-ai/blob/phase4_specialized_models/INSTRUCTION_FOR_OTHER_AI.md

【主な調査内容】
1. エラー: column s.seibetsu does not exist
   - ファイル: simulate_2026_hitrate_only.py (69行目)
   - 正しいカラム名は s.seibetsu_code か?

2. nvd_se テーブルの実際のカラム名を確認
   - seibetsu vs seibetsu_code

3. Phase 3学習スクリプトとの整合性確認
   - extract_training_data_v2.py では se.seibetsu_code を使用

4. 修正版SQLクエリを提案

【データベース情報】
- Host: 127.0.0.1:5432
- Database: pckeiba
- User: postgres
- Password: postgres123
- テーブル: nvd_se, nvd_ra

【期待する報告】
1. seibetsu カラムの正しい名前
2. 修正内容（69行目の修正方法）
3. 修正版SQLクエリ
4. その他の不整合があれば指摘

重要: 推測ではなく、実際のテーブル構造を確認してください。
```

---

### パターン2: 簡潔版

```
GitHubリポジトリを確認して、データベーススキーマ不整合を調査してください:

リポジトリ: https://github.com/aka209859-max/anonymous-keiba-ai
ブランチ: phase4_specialized_models
調査指示: INSTRUCTION_FOR_OTHER_AI.md を参照

エラー: column s.seibetsu does not exist (simulate_2026_hitrate_only.py の69行目)

質問:
1. nvd_se テーブルに seibetsu カラムは存在するか?
2. 正しいカラム名は seibetsu_code か?
3. 他に修正が必要なカラムはあるか?

データベース: pckeiba (127.0.0.1:5432)
テーブル: nvd_se, nvd_ra

推測ではなく、実際のスキーマを確認してください。
```

---

## 🔗 重要URL（すぐにアクセス可能）

### GitHubリポジトリ
https://github.com/aka209859-max/anonymous-keiba-ai

### プルリクエスト #3
https://github.com/aka209859-max/anonymous-keiba-ai/pull/3

### 調査指示書（完全版）
https://github.com/aka209859-max/anonymous-keiba-ai/blob/phase4_specialized_models/INSTRUCTION_FOR_OTHER_AI.md

### 現状サマリー
https://github.com/aka209859-max/anonymous-keiba-ai/blob/phase4_specialized_models/CURRENT_STATUS_SUMMARY.md

### 問題のファイル
https://github.com/aka209859-max/anonymous-keiba-ai/blob/phase4_specialized_models/simulate_2026_hitrate_only.py

### Phase 3学習スクリプト（参照）
https://github.com/aka209859-max/anonymous-keiba-ai/blob/phase4_specialized_models/extract_training_data_v2.py

---

## 📊 問題の詳細

### エラー内容
```
ERROR: column s.seibetsu does not exist
LINE 69: s.seibetsu,
         ^
HINT: Perhaps you meant to reference the column "s.seibetsu_code".
```

### 推測される修正
```diff
- s.seibetsu,
+ s.seibetsu_code,
```

### 根拠
Phase 3学習スクリプト (`extract_training_data_v2.py`) では:
- 95行目: `se.seibetsu_code,`
- 202行目: `tr.seibetsu_code,`
- 268行目: `tr.seibetsu_code,`

---

## ✅ 修正済みの問題（参考）

1. **shusso_tosu** (コミット 8f918fb)
   - `s.shusso_tosu` → `r.shusso_tosu`
   - 理由: nvd_ra テーブルに存在

2. **馬場状態** (コミット a963ca9)
   - `r.baba_jotai_code` → `r.babajotai_code_shiba`, `r.babajotai_code_dirt`
   - 理由: 芝とダートで別カラム

3. **対象期間** (コミット cc91feb)
   - 2026-01-01 ～ 2026-02-03 → 2026-01-01 ～ 2026-01-31
   - 理由: 2月のデータが不完全

---

## 🎯 期待される調査結果

### 最低限
1. ✅ `nvd_se.seibetsu` は存在するか？
2. ✅ `nvd_se.seibetsu_code` が正しいか？
3. ✅ 69行目を `s.seibetsu_code` に修正すべきか？

### 理想的
4. ✅ 修正版SQLクエリ
5. ✅ 2026年1月データ件数（10競馬場別）
6. ✅ その他の潜在的な問題

---

## 🔧 調査手順（推奨）

### Step 1: リポジトリ確認
```bash
git clone https://github.com/aka209859-max/anonymous-keiba-ai.git
cd anonymous-keiba-ai
git checkout phase4_specialized_models
```

### Step 2: ファイル比較
```bash
# シミュレーションスクリプト
grep -n "seibetsu" simulate_2026_hitrate_only.py

# Phase 3学習スクリプト
grep -n "seibetsu" extract_training_data_v2.py
```

### Step 3: データベース確認（Windows環境で）
```bash
python check_db_schema.py
```

または直接SQL:
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'nvd_se'
  AND column_name LIKE '%seibetsu%';
```

---

## 📝 報告形式

```markdown
【調査結果】

1. nvd_se テーブルのカラム名
   - [ ] seibetsu が存在する
   - [ ] seibetsu_code が存在する
   - [ ] その他: _________

2. 推奨修正
   69行目: s.seibetsu → s.seibetsu_code

3. 修正版SQLクエリ
   ```sql
   SELECT 
       s.kaisai_nen,
       s.kaisai_tsukihi,
       ...
       s.seibetsu_code,  -- ← 修正
       s.barei,
       ...
   ```

4. その他の発見
   - (あれば記載)
```

---

## ⚠️ 注意事項

### 他AIに伝えるべきこと
1. **ハルシネーション厳禁**
   - GitHubの実際のコードを確認
   - データベーススキーマを推測しない

2. **Phase 3との整合性**
   - 学習時と予測時で同じカラム名を使用すべき

3. **Windows環境の制約**
   - データベースはローカル（127.0.0.1:5432）

---

## 📞 次のアクション

### 1. 他AIに依頼 ← **今ここ**
- 上記のパターン1またはパターン2をコピペ
- GitHubリポジトリを確認してもらう

### 2. 調査結果を受け取る
- seibetsu vs seibetsu_code の確認
- 修正版SQLクエリを取得

### 3. 修正を適用
- simulate_2026_hitrate_only.py の69行目を修正
- コミット＆プッシュ
- PR #3 を更新

### 4. Windows環境で実行
```cmd
cd E:\anonymous-keiba-ai
git pull origin phase4_specialized_models
python simulate_2026_hitrate_only.py
```

### 5. 成功確認
- simulation_2026_hitrate_results.csv 生成
- simulation_2026_hitrate_summary.csv 生成
- simulation_2026_hitrate_summary.txt 生成

---

## 🎯 最終目標

**2026年1月シミュレーション実行の成功**
- 10競馬場で約9,922件のデータ
- 印別的中率の算出（◎○▲△×）
- Note/X/Discord用レポートの作成

---

**準備完了！上記の依頼文を他AIにコピペしてください！** 🚀
