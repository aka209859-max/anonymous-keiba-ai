# 🏇 地方競馬AI予想 - 毎日運用クイックスタート

## ⚡ 最短で始める

### 1. 基本的な実行（単一競馬場）

```batch
REM 佐賀競馬 2026年2月8日の予想を生成
cd E:\anonymous-keiba-ai
scripts\phase6_betting\DAILY_OPERATION.bat 55 2026-02-08
```

**これだけで以下が生成されます:**
- `predictions\佐賀_20260208_note.txt` ← Note用
- `predictions\佐賀_20260208_bookers.txt` ← ブッカーズ用

---

### 2. 複数競馬場の一括処理（土曜日）

```batch
REM 2026年2月8日（土曜日）のすべての競馬場を一括処理
cd E:\anonymous-keiba-ai
scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-08 sat
```

**自動的に開催中の競馬場を検出して処理します!**

---

## 📋 競馬場コード早見表

| コード | 競馬場 | 主な開催曜日 |
|--------|--------|--------------|
| **44** | **大井** | 水・金・月 |
| **45** | **川崎** | 水・金 |
| **43** | **船橋** | 木・金 |
| **55** | **佐賀** | 土・日 |
| 42 | 浦和 | 土・日 |
| 54 | 高知 | 土・日 |
| 50 | 園田 | 土・日 |
| 48 | 名古屋 | 土・日 |

---

## 🎯 典型的な1日の流れ

### 朝（レース前）

```batch
REM 1. 予想データの生成（Phase 0-5 を先に実行）
run_all.bat 55 2026-02-08

REM 2. 配信用テキストの生成
scripts\phase6_betting\DAILY_OPERATION.bat 55 2026-02-08

REM 3. ファイルを開いて確認
notepad predictions\佐賀_20260208_note.txt
notepad predictions\佐賀_20260208_bookers.txt
```

### Note投稿（コピペ）

1. `predictions\佐賀_20260208_note.txt` を開く
2. 全文をコピー（Ctrl+A → Ctrl+C）
3. Noteエディタにペースト（Ctrl+V）
4. プレビュー確認して公開

### ブッカーズ投稿（コピペ）

1. `predictions\佐賀_20260208_bookers.txt` を開く
2. 全文をコピー（Ctrl+A → Ctrl+C）
3. ブッカーズエディタにペースト（Ctrl+V）
4. プレビュー確認して公開

---

## 🚀 よくある使い方パターン

### パターン1: 平日ナイター競馬（大井・川崎）

```batch
REM 水曜日の大井・川崎を一括処理
scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-10 wed
```

### パターン2: 週末競馬（複数開催）

```batch
REM 土曜日のすべての競馬場を一括処理
scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-08 sat
```

### パターン3: 特定の競馬場のみ（手動指定）

```batch
REM 佐賀・高知・園田のみ処理
scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-08 custom "55 54 50"
```

---

## ⚠️ よくあるエラーと対処法

### エラー: 入力ファイルが見つかりません

**原因:** Phase 5 まで実行されていない

**対処法:**
```batch
REM まず Phase 0-5 を実行
run_all.bat 55 2026-02-08

REM その後、配信用テキスト生成
scripts\phase6_betting\DAILY_OPERATION.bat 55 2026-02-08
```

---

### エラー: 馬名が「未登録」になる

**原因:** raw データがない

**対処法:**
```batch
REM Phase 0 からやり直す
python scripts/phase0_data_acquisition/fetch_data.py 55 2026-02-08
```

---

## 📝 カスタマイズのヒント

### テンプレートを微調整したい

編集するファイル:
- `scripts\phase6_betting\generate_distribution_note.py` ← Note用
- `scripts\phase6_betting\generate_distribution_bookers.py` ← ブッカーズ用

よく変更する箇所:
```python
# ランク評価基準を変更
def assign_rank_label(score):
    if score >= 0.80:  # ← この閾値を調整
        return 'S'
```

---

## 🔍 トラブル時のチェックリスト

1. **[ ]** Phase 0-5 まで正常に完了しているか?
   ```batch
   dir data\predictions\phase5\佐賀_20260208_ensemble.csv
   ```

2. **[ ]** raw データが存在するか?
   ```batch
   dir data\raw\2026\02\佐賀_20260208_raw.csv
   ```

3. **[ ]** Python が正しくインストールされているか?
   ```batch
   python --version
   ```

4. **[ ]** pandas ライブラリがインストールされているか?
   ```batch
   pip list | findstr pandas
   ```

---

## 📚 詳細ドキュメント

詳しい説明は以下を参照:
- [詳細ガイド](./README_DAILY_OPERATION.md) - トラブルシューティング、カスタマイズ方法
- [開発レポート](../../DEVELOPMENT_REPORT_2026_02_08.md) - システム全体の仕様

---

## 💡 Pro Tips

### Tip 1: バッチファイルをデスクトップに置く

```batch
REM デスクトップにショートカット作成
mklink "%USERPROFILE%\Desktop\競馬予想生成.bat" "E:\anonymous-keiba-ai\scripts\phase6_betting\DAILY_OPERATION.bat"
```

### Tip 2: 履歴管理

```batch
REM 過去の予想を日付フォルダで整理
mkdir archive\2026-02
move predictions\*_20260208_*.txt archive\2026-02\
```

### Tip 3: 自動実行（タスクスケジューラ）

Windowsのタスクスケジューラで毎朝自動実行:
1. タスクスケジューラを開く
2. 「基本タスクの作成」をクリック
3. トリガー: 毎日 朝7時
4. 操作: `E:\anonymous-keiba-ai\scripts\phase6_betting\BATCH_OPERATION.bat`
5. 引数: `2026-02-08 sat`（日付は手動更新）

---

## 🎉 これで準備完了！

あとは毎日実行して、Note/ブッカーズに投稿するだけです！

**Happy Betting! 🏇✨**
