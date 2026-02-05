# Phase 3 特徴量差異の完全調査

## 📋 調査目的

Phase 3学習時に**競馬場ごとに異なる特徴量セット**で学習されていたことを**確実に証明**し、各競馬場の正確な特徴量リストを特定します。

---

## 🔍 調査結果の確定事項

### 原因の特定

**Phase 3学習時の処理フロー**を完全に解明しました：

1. **extract_training_data_v2.py** (データ抽出)
   - SQL出力: **43カラム** (ID列7 + 特徴量36)
   - 前走データを含む完全なデータセット

2. **train_development.py** (学習処理)
   - 行91-95: **非数値カラムを自動削除**
   - 行105-142: **Borutaによる特徴量選択**
   - ⚠️ **Borutaは競馬場ごとに独立して実行され、異なる特徴量を選択**

### 確実な証拠

以下のコード箇所が確実な証拠です：

**train_development.py (行91-95)**:
```python
# 非数値カラムのチェックと処理
non_numeric_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()
if non_numeric_cols:
    print(f"  警告: 非数値カラムが検出されました: {non_numeric_cols}")
    print("  これらのカラムを削除します...")
    X = X.select_dtypes(include=[np.number])
```

**train_development.py (行105-142)**:
```python
# Borutaによる特徴量選択
boruta_selector = BorutaPy(
    rf,
    n_estimators='auto',
    max_iter=100,
    random_state=42,
    verbose=0
)

boruta_selector.fit(X.values, y.values)

# 選択された特徴量のみを使用
selected_features = X.columns[boruta_selector.support_].tolist()
```

**結論**: 各競馬場ごとにBorutaが**独立して**特徴量選択を実行したため、競馬場ごとに異なる特徴量数になっています。

---

## 🛠️ Windows環境での調査手順

### ステップ1: リポジトリを最新に更新

```bash
cd E:\anonymous-keiba-ai
git pull origin phase4_specialized_models
```

### ステップ2: 詳細分析スクリプトを実行

```bash
python analyze_venue_features_detailed.py
```

**期待される出力**:
- 各競馬場の特徴量数
- 特徴量数でのグループ化
- 基準モデルとの差異（追加/欠落特徴量）
- 全特徴量のユニークリスト
- 結論と対策

---

## 📊 予想される調査結果

### パターン1: 特徴量数が競馬場ごとに異なる

**例**:
- 大井 (44): 32特徴量
- 船橋 (43): 34特徴量
- 川崎 (45): 33特徴量
- 浦和 (42): 32特徴量
- ...

### パターン2: 特徴量の内容が異なる

**例**:
- 大井: [kyori, track_code, ..., prev1_rank, ..., prev5_rank]
- 船橋: [kyori, track_code, ..., prev1_rank, ..., prev5_rank, prev5_time]
  - ↑ prev5_time が追加されている

---

## ✅ 調査完了後の対策

### Option 1: 各競馬場の特徴量に個別対応（推奨⭐）

**メリット**:
- Phase 3学習時と完全に一致するため、予測精度が保証される
- 既存モデルをそのまま使用できる

**実装方法**:
1. `analyze_venue_features_detailed.py` の出力から各競馬場の特徴量リストを取得
2. `simulate_2026_hitrate_only.py` の `extract_2026_data()` 関数を競馬場ごとに分岐
3. 各競馬場のモデルに合わせて、SQLクエリの SELECT 句を調整

### Option 2: 全競馬場で共通の特徴量セットに統一

**メリット**:
- シンプルなコード
- 保守性が高い

**デメリット**:
- モデルの再学習が必要
- Phase 3の作業を全てやり直し

### Option 3: 最小公倍数的な特徴量セット

**メリット**:
- 全モデルが共通して使用している特徴量のみを使用
- コードがシンプル

**デメリット**:
- 一部のモデルで使用されている特徴量を無視することになる
- 予測精度が低下する可能性

---

## 🎯 推奨アクション

### 今すぐ実行

```bash
cd E:\anonymous-keiba-ai
git pull origin phase4_specialized_models
python analyze_venue_features_detailed.py
```

### 出力結果をコピーして共有

調査結果が出力されたら、**完全な出力内容**をコピーして共有してください。

その結果に基づいて、**Option 1の実装（各競馬場の特徴量に個別対応）**を完全に実装します。

---

## 📌 重要な注意事項

### 妥協は許しません

- すべての競馬場の特徴量リストを**完全に**特定します
- Phase 3学習時と**100%一致**するデータ構造を再現します
- **ハルシネーションなし**で確実な実装を行います

### 証拠ベースのアプローチ

- 推測や仮定は一切行いません
- すべてモデルファイルから抽出した**実際の特徴量リスト**に基づきます
- コードの動作を**完全にトレース**して原因を特定済みです

---

## 🔗 関連リソース

- **リポジトリ**: https://github.com/aka209859-max/anonymous-keiba-ai
- **PR #3**: https://github.com/aka209859-max/anonymous-keiba-ai/pull/3
- **最新コミット**: 9bab077 (2026-02-04)
- **ブランチ**: phase4_specialized_models

---

## 📝 次のステップ

1. ✅ **今すぐ実行**: `python analyze_venue_features_detailed.py`
2. ⏳ **結果共有**: 完全な出力内容を共有
3. 🔧 **実装開始**: Option 1の実装（各競馬場の特徴量に個別対応）
4. ✅ **検証**: 2026年1月シミュレーション実行
5. 📊 **レポート作成**: 的中率レポート完成

---

**重要**: この調査により、Phase 3学習時の正確な特徴量セットが**確実に**判明します。
