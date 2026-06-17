# Phase 3-5 は削除されていません！

**重要**: Phase 3-5のスクリプトは **すべて残っています**。`run_all.bat` の中で実行されなくなっただけです。

---

## ✅ Phase 3-5 のスクリプトは健在

### 確認方法

```batch
dir scripts\phase3_binary\predict_phase3_inference.py
dir scripts\phase4_ranking\predict_phase4_ranking_inference.py
dir scripts\phase4_regression\predict_phase4_regression_inference.py
dir scripts\phase5_ensemble\ensemble_predictions.py
```

**すべて存在します！** ✅

---

## 🔄 何が変わったのか？

### run_all.bat の変更

| 項目 | 旧版 | 新版 |
|------|------|------|
| Phase 3 | **実行** | スキップ |
| Phase 4 | **実行** | スキップ |
| Phase 5 | **実行** | スキップ |
| Phase 8 | なし | **実行** |
| Phase 3-5スクリプト | 存在 | **存在（変更なし）** |

**Phase 3-5は実行されないだけで、削除されていません！**

---

## 💡 なぜ Phase 8 を使うのか？

### 性能比較

| モデル | AUC | 的中率 | 特徴量 | 学習時間 |
|--------|-----|--------|--------|---------|
| Phase 3-5 | ~0.70 | ~70% | 50個 | 約10分 |
| **Phase 8** | **0.7637** | **~76%** | **29個** | 約3時間 |

**Phase 8は Phase 3-5より6%高精度！**

---

## 🎯 使い分けガイド

### Phase 8を使う場合（推奨）

```batch
run_all.bat 43 2026-02-11
```

**利点**:
- ✅ 高精度（的中率 ~76%）
- ✅ 最適化された特徴量（29個）
- ✅ Optuna最適化（200試行）

**前提条件**:
- Phase 7完了（Boruta特徴量選択）
- Phase 8完了（Optunaモデル最適化）

---

### Phase 3-5を使う場合

```batch
run_all_phase35.bat 43 2026-02-11
```

**利点**:
- ✅ Phase 7-8不要（すぐ使える）
- ✅ デフォルトモデルで動作
- ✅ 比較検証に使える

**欠点**:
- ❌ 精度が低い（的中率 ~70%）

---

## 📊 実行フロー比較

### Phase 8版（run_all.bat）

```
Phase 0-1: データ取得 + 特徴量生成
    ↓
Phase 8: 最適化モデルで予測（29特徴量）
    ↓
Phase 6: 配信テキスト生成
```

**的中率**: ~76%

---

### Phase 3-5版（run_all_phase35.bat）

```
Phase 0-1: データ取得 + 特徴量生成
    ↓
Phase 3: 二値分類予測
    ↓
Phase 4: ランキング + 回帰予測
    ↓
Phase 5: アンサンブル統合
    ↓
Phase 6: 配信テキスト生成
```

**的中率**: ~70%

---

## 🔧 Phase 3-5 を個別に実行

### 手動で Phase 3-5 を実行

```batch
REM Phase 3: 二値分類
python scripts\phase3_binary\predict_phase3_inference.py data\features\2026\02\船橋_20260211_features.csv models\binary output_phase3.csv

REM Phase 4-1: ランキング
python scripts\phase4_ranking\predict_phase4_ranking_inference.py data\features\2026\02\船橋_20260211_features.csv models\ranking output_phase4_rank.csv

REM Phase 4-2: 回帰
python scripts\phase4_regression\predict_phase4_regression_inference.py data\features\2026\02\船橋_20260211_features.csv models\regression output_phase4_reg.csv

REM Phase 5: アンサンブル
python scripts\phase5_ensemble\ensemble_predictions.py output_phase3.csv output_phase4_rank.csv output_phase4_reg.csv output_phase5_ensemble.csv
```

**Phase 3-5のスクリプトは完全に機能します！**

---

## 📁 ファイル構成

```
E:\anonymous-keiba-ai\
├── run_all.bat                          ← Phase 8使用（推奨）
├── run_all_phase35.bat                  ← Phase 3-5使用（旧版）
├── RUN_PHASE8_TO_PHASE6.bat             ← Phase 8使用（明示的）
├── RUN_PHASE8_TO_PHASE6_MULTI.bat       ← Phase 8使用（複数会場）
├── scripts\
│   ├── phase3_binary\                   ← 存在（削除されていない）
│   │   └── predict_phase3_inference.py
│   ├── phase4_ranking\                  ← 存在（削除されていない）
│   │   └── predict_phase4_ranking_inference.py
│   ├── phase4_regression\               ← 存在（削除されていない）
│   │   └── predict_phase4_regression_inference.py
│   ├── phase5_ensemble\                 ← 存在（削除されていない）
│   │   └── ensemble_predictions.py
│   └── phase8_prediction\               ← 新規追加
│       └── predict_phase8.py
└── ...
```

---

## 🎯 コマンド一覧

| コマンド | Phase | 的中率 | 使い分け |
|---------|-------|--------|---------|
| `run_all.bat 43 2026-02-11` | Phase 8 | ~76% | **推奨**（高精度） |
| `run_all_phase35.bat 43 2026-02-11` | Phase 3-5 | ~70% | 旧版（比較用） |
| `RUN_PHASE8_TO_PHASE6.bat 43 2026-02-11` | Phase 8 | ~76% | 明示的 |

---

## ✅ よくある質問

### Q1: Phase 3-5は削除されたの？

**A**: いいえ！Phase 3-5のスクリプトは **すべて残っています**。`run_all.bat` で実行されなくなっただけです。

---

### Q2: Phase 3-5を使いたい場合は？

**A**: `run_all_phase35.bat 43 2026-02-11` を実行してください。

---

### Q3: なぜ Phase 8 を推奨するの？

**A**: Phase 8は Phase 3-5より **6%高精度** だからです（70% → 76%）。

---

### Q4: Phase 3-5と Phase 8 の両方を実行できる？

**A**: はい！両方実行して結果を比較できます：

```batch
REM Phase 3-5で実行
run_all_phase35.bat 43 2026-02-11

REM Phase 8で実行
run_all.bat 43 2026-02-11

REM 結果を比較
fc predictions\船橋_20260211_note.txt predictions\船橋_20260211_note.txt
```

---

### Q5: Phase 3-5を完全に削除したい場合は？

**A**: 以下のフォルダを削除できます（ただし非推奨）：

```batch
rmdir /s /q scripts\phase3_binary
rmdir /s /q scripts\phase4_ranking
rmdir /s /q scripts\phase4_regression
rmdir /s /q scripts\phase5_ensemble
```

**ただし、削除は推奨しません。** Phase 3-5は以下の用途で有用です：
- Phase 8との比較検証
- Phase 7-8が未完了の場合のフォールバック
- デバッグ用

---

## 📋 まとめ

| 項目 | 状態 |
|------|------|
| **Phase 3-5スクリプト** | ✅ 存在（削除されていない） |
| **run_all.bat** | Phase 8を使用（変更） |
| **run_all_phase35.bat** | Phase 3-5を使用（新規追加） |
| **Phase 3-5の個別実行** | ✅ 可能 |
| **推奨** | Phase 8使用（高精度） |

---

**Phase 3-5は削除されていません！必要に応じて `run_all_phase35.bat` または個別スクリプトで使用できます。** ✅
