# 🔧 Boruta インストール問題の解決方法

## 問題の診断

Borutaが `pip install` では成功しているように見えるが、実際には使えない状態です。
これは **複数のPython環境が存在している** 可能性があります。

---

## 解決方法

### 方法1: 正しいpipを使ってインストール

```bash
# 現在使っているPythonのpipを確認
python -m pip --version

# このpipを使ってBorutaをインストール
python -m pip install boruta

# 確認
python -c "from boruta import BorutaPy; print('Boruta OK')"
```

### 方法2: requirements.txtから再インストール

```bash
# Python経由でpipを実行
python -m pip install -r requirements.txt

# 確認
python -c "from boruta import BorutaPy; print('Boruta OK')"
```

### 方法3: pipのパスを確認

```bash
# pipのパスを確認
where pip
where python

# 出力例:
# C:\Users\ihaji\AppData\Local\Programs\Python\Python312\python.exe
# C:\Users\ihaji\AppData\Local\Programs\Python\Python312\Scripts\pip.exe
```

もし複数のパスが表示される場合、正しいPython環境のpipを使ってください。

---

## 別の解決方法: 仮想環境を使う（推奨）

Pythonの仮想環境を作成すれば、パッケージの競合を避けられます。

```bash
# E:\anonymous-keiba-aiに移動
cd E:\anonymous-keiba-ai

# 仮想環境を作成
python -m venv venv

# 仮想環境を有効化（Windows）
venv\Scripts\activate

# プロンプトが (venv) E:\anonymous-keiba-ai> に変わる

# requirements.txtからインストール
pip install -r requirements.txt

# 確認
python -c "from boruta import BorutaPy; print('Boruta OK')"

# 学習実行
python train_development.py ooi_2023-2024.csv
```

### 仮想環境を終了する場合
```bash
deactivate
```

---

## 方法4: Borutaを直接ダウンロードしてインストール

```bash
# GitHubから直接インストール
python -m pip install git+https://github.com/scikit-learn-contrib/boruta_py.git
```

---

## トラブルシューティング

### エラー1: pip not found
```bash
# pipをインストール
python -m ensurepip --upgrade
```

### エラー2: Permission denied
```bash
# 管理者権限で実行、または --user オプションを使用
python -m pip install --user boruta
```

### エラー3: SSL certificate error
```bash
# 信頼できるホストとして追加
python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org boruta
```

---

## 推奨手順（最も確実）

### ステップ1: 仮想環境を作成
```bash
cd E:\anonymous-keiba-ai
python -m venv venv
```

### ステップ2: 仮想環境を有効化
```bash
venv\Scripts\activate
```

プロンプトが `(venv) E:\anonymous-keiba-ai>` に変わることを確認

### ステップ3: pipをアップグレード
```bash
python -m pip install --upgrade pip
```

### ステップ4: requirements.txtからインストール
```bash
pip install -r requirements.txt
```

### ステップ5: Borutaの確認
```bash
python -c "from boruta import BorutaPy; print('Boruta OK')"
```

**「Boruta OK」と表示されれば成功！**

### ステップ6: 学習実行
```bash
python train_development.py ooi_2023-2024.csv
```

---

## 仮想環境を使う理由

### メリット
1. ✅ パッケージの競合を避けられる
2. ✅ プロジェクトごとに独立した環境
3. ✅ 複数のPython環境の混乱を防げる

### デメリット
- 毎回 `venv\Scripts\activate` で有効化する必要がある

---

## 次のステップ

上記のいずれかの方法でBorutaをインストールできたら:

```bash
# 学習実行
python train_development.py ooi_2023-2024.csv
```

### 期待される出力
```
================================================================================
地方競馬AI学習プログラム (LightGBM + Boruta + Optuna)
================================================================================
CSVファイル: ooi_2023-2024.csv

[1/7] データ読み込み中...
...
```

---

## まとめ: 最も簡単な方法

```bash
# これだけ実行してください
cd E:\anonymous-keiba-ai
python -m pip install boruta
python -c "from boruta import BorutaPy; print('Boruta OK')"
python train_development.py ooi_2023-2024.csv
```

**これで動かなければ、仮想環境を使う方法（方法3）をお試しください。**
