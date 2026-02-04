# 🔧 ローカル環境の修正手順

## 問題の確認

### ✅ データ抽出は成功！
- 大井2023-2024年: 27,219件
- 全地方2020-2024年: 671,702件

### ❌ Borutaモジュールが見つからない
```
ModuleNotFoundError: No module named 'boruta'
```

---

## 📝 修正手順

### ステップ1: 最新のコードを取得
```bash
cd E:\anonymous-keiba-ai
git pull origin genspark_ai_developer
```

### ステップ2: Borutaパッケージのインストール

以前のログを見ると、`pip install -r requirements.txt` で Boruta がインストールされているはずですが、念のため再度インストールしてください。

```bash
# 方法1: requirements.txtから再インストール
pip install -r requirements.txt

# 方法2: Borutaを直接インストール
pip install boruta

# インストール確認
python -c "from boruta import BorutaPy; print('Boruta OK')"
```

### ステップ3: 学習を実行

#### 小規模データでテスト（大井2023-2024年、27,219件）
```bash
python train_development.py ooi_2023-2024.csv
```

**予想される実行時間:**
- Borutaの特徴量選択: 10-30分
- Optunaのハイパーパラメータ最適化: 5-15分
- **合計: 15-45分程度**

**期待される出力:**
```
================================================================================
地方競馬AI学習プログラム (LightGBM + Boruta + Optuna)
================================================================================
CSVファイル: ooi_2023-2024.csv

[1/7] データ読み込み中...
  - データ件数: 27,219件
  - カラム数: 36個
  - 目的変数 'target' の分布:
    クラス 0: 20,450件 (75.1%)
    クラス 1: 6,769件 (24.9%)

[2/7] Borutaによる特徴量選択中...
  （この処理には数分〜数十分かかる場合があります）
  - 選択された特徴量数: X個 / 18個
  - 選択率: XX.X%

[3/7] データ分割中...
  - 訓練データ: 21,775件
  - テストデータ: 5,444件

[4/7] LightGBM Datasetを作成中...
  - Dataset作成完了

[5/7] LightGBM + Optunaによる学習中...
  （ハイパーパラメータ自動最適化を実行します）
  - 学習完了

[6/7] モデル評価中...
  - AUC:       0.XXXX
  - Accuracy:  0.XXXX
  - Precision: 0.XXXX
  - Recall:    0.XXXX
  - F1-Score:  0.XXXX

[7/7] 結果を保存中...
  - モデル保存: ooi_2023-2024_model.txt
  - 重要度グラフ保存: ooi_2023-2024_model.png
  - 評価指標保存: ooi_2023-2024_score.txt

================================================================================
学習完了！
================================================================================
```

---

## 🚀 成功したら次のステップ

### オプションA: 2025年データも含めて再抽出
```bash
# 大井競馬場、2020-2025年
python extract_training_data.py --keibajo 44 --start-date 2020 --end-date 2025 --output ooi_2020-2025.csv

# 学習実行
python train_development.py ooi_2020-2025.csv
```

### オプションB: 全地方競馬場で学習（時間がかかる）
```bash
# 警告: Borutaの処理に数時間かかる可能性があります
python train_development.py all_2020-2024.csv
```

---

## ⚠️ トラブルシューティング

### 問題1: Borutaのインポートエラー
```
ModuleNotFoundError: No module named 'boruta'
```

**対処法:**
```bash
# 現在のPython環境を確認
python --version
where python

# pipでBorutaをインストール
pip install boruta

# 別の方法: Condaの場合
conda install -c conda-forge boruta_py
```

### 問題2: メモリ不足エラー
```
MemoryError: Unable to allocate array
```

**対処法:**
- より小規模なデータで実行（1競馬場、2-3年分）
- `train_development.py` のBorutaの `max_depth` を減らす

### 問題3: 実行時間が長すぎる
Borutaの処理が1時間以上かかる場合

**対処法:**
- `train_development.py` のBorutaの `max_iter` を減らす（100 → 50）
- `n_estimators` を減らす（100 → 50）

---

## 📊 出力ファイルの確認

学習が完了したら、以下のファイルが生成されます:

### 1. モデルファイル
```
ooi_2023-2024_model.txt
```
LightGBMのテキスト形式モデル

### 2. 特徴量重要度グラフ
```
ooi_2023-2024_model.png
```
重要な特徴量のTop 20を可視化

### 3. 評価指標ログ
```
ooi_2023-2024_score.txt
```
AUC、Accuracy、Precision、Recall、F1-Scoreなど

**このファイルの内容を確認してください！**

---

## 📝 次の報告内容

学習が完了したら、以下を報告してください:

1. ✅ 学習が正常に完了したか
2. 📊 評価指標（AUC、Accuracyなど）
3. 🎯 選択された特徴量数
4. ⏱️ 実行時間

これらの情報をもとに、次のステップ（フェーズ3: 過去走データ統合またはモデル派生）を決定します！
