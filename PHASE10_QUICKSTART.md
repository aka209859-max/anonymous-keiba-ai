# 🚀 Phase 10 クイックスタート

## 📋 Phase 10とは？

**Phase 10は、Phase 8で最適化されたモデルを使った日次予測システムです。**

- **Phase 7**: Boruta特徴量選択（完了済み）→ 29個の重要特徴量
- **Phase 8**: Optunaハイパーパラメータ最適化（完了済み）→ 平均AUC 0.76（優秀レベル）
- **Phase 10**: Phase 8モデルで予測 → 期待値ベースの購入推奨 ← ここ！

---

## ✅ 前提条件の確認

### 1. Phase 8完了確認
```batch
cd E:\anonymous-keiba-ai
dir data\models\tuned\*_tuned_model.txt
```
**期待される結果:** 14個のモデルファイル

### 2. Phase 7完了確認
```batch
dir data\features\selected\*_selected_features.csv
```
**期待される結果:** 14個の特徴量ファイル

---

## 🚀 今すぐ使える！3つの使用方法

### 方法1: 単一競馬場（最もシンプル）

```batch
REM 大井競馬（2026-02-11）
RUN_PHASE10_DAILY.bat 44 2026-02-11
```

**実行結果:**
- `data\predictions\phase10\ooi_20260211_predictions.csv`
- `data\predictions\phase10\ooi_20260211_recommended_bets.csv`
- `data\predictions\phase10\ooi_20260211_summary.txt`

---

### 方法2: 複数競馬場一括（最も効率的）

```batch
REM 大井・川崎・佐賀（2026-02-11）
RUN_PHASE10_ALL_VENUES.bat 2026-02-11 44 45 55
```

**実行結果:**
- 3競馬場分の予測結果・購入推奨・サマリーが一括生成

---

### 方法3: 完全版（予測→配信まで）

```batch
cd E:\anonymous-keiba-ai

REM Phase 10: 予測実行
RUN_PHASE10_ALL_VENUES.bat 2026-02-11 44 45 55

REM Phase 6: 配信用テキスト生成
scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-11

REM 確認
explorer predictions
notepad predictions\大井_20260211_note.txt
```

---

## 📊 出力ファイルの確認

### サマリーTXT（最も重要）
```batch
notepad data\predictions\phase10\ooi_20260211_summary.txt
```

**内容例:**
```
============================================================
Phase 10: 日次予測サマリー
============================================================
競馬場: 大井 (ooi)
対象日: 2026-02-11

【予測統計】
  - 総レース数: 144件
  - 平均予測確率: 0.1234
  
【購入推奨】
  - 推奨馬数: 12頭
  - 総推奨金額: 15,000円
  - 平均期待値: 0.1523

【トップ5推奨馬】
  馬番 3: 確率0.456 EV+0.234 推奨2,500円
  馬番 7: 確率0.389 EV+0.198 推奨2,200円
  ...
============================================================
```

### 購入推奨CSV
```batch
type data\predictions\phase10\ooi_20260211_recommended_bets.csv
```

### 予測結果CSV
```batch
type data\predictions\phase10\ooi_20260211_predictions.csv
```

---

## 📅 競馬場コード早見表

| コード | 競馬場 | コード | 競馬場 | コード | 競馬場 |
|--------|--------|--------|--------|--------|--------|
| 30 | 門別 | 35 | 盛岡 | 36 | 水沢 |
| 42 | 浦和 | 43 | 船橋 | **44** | **大井** |
| **45** | **川崎** | 46 | 金沢 | 47 | 笠松 |
| 48 | 名古屋 | 50 | 園田 | 51 | 姫路 |
| 54 | 高知 | **55** | **佐賀** | | |

---

## 🎯 毎日の運用フロー（3ステップ）

### ステップ1: Phase 10実行
```batch
RUN_PHASE10_ALL_VENUES.bat 2026-02-11 44 45 55
```

### ステップ2: Phase 6配信テキスト生成
```batch
scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-11
```

### ステップ3: 配信
```batch
explorer predictions
REM note/Bookers/X用テキストを確認
notepad predictions\大井_20260211_note.txt
notepad predictions\大井_20260211_bookers.txt
```

---

## 💡 よくある質問（FAQ）

### Q1: Phase 0-4（run_all.bat）は不要？
**A:** Phase 10は既存の出走表データを使用します。Phase 0-4が実行されていない場合は、先に実行してください。

```batch
REM Phase 0-4を実行
run_all.bat 44 2026-02-11

REM その後、Phase 10を実行
RUN_PHASE10_DAILY.bat 44 2026-02-11
```

### Q2: オッズはどうやって取得する？
**A:** 現在はダミーオッズを使用しています。今後の改善で、netkeiba APIからリアルタイムオッズを取得する予定です。

### Q3: 期待値が正の馬が見つからない場合は？
**A:** サマリーに「⚠️ 期待値が正の馬が見つかりませんでした」と表示されます。その日は購入を見送ることを推奨します。

### Q4: 資金管理のパラメータを変更したい
**A:** Python直接実行で変更可能です。

```batch
python scripts\phase10_daily_prediction\run_daily_prediction.py --venue-code 44 --date 2026-02-11 --bankroll 200000 --kelly-fraction 0.5
```

---

## ⚠️ トラブルシューティング

### エラー: モデルファイルが見つかりません
```
❌ モデルファイルが見つかりません: data/models/tuned/monbetsu_tuned_model.txt
```

**原因:** Phase 8が未完了  
**解決策:**
```batch
REM Phase 8を実行
RUN_PHASE8_ALL_VENUES.bat
```

### エラー: レースデータが見つかりません
```
❌ レースデータが見つかりません: 44 2026-02-11
```

**原因:** Phase 0-4が未実行  
**解決策:**
```batch
REM Phase 0-4を実行
run_all.bat 44 2026-02-11
```

---

## 🎉 Phase 10完了後にやること

### 1. 毎日の予測配信
- Phase 10で予測実行
- Phase 6で配信テキスト生成
- note/Bookers/Xで配信

### 2. 本当の改善策に着手（Phase 10完了後）
以下の改善で、AUC 0.76 → 0.80+ を目指します:

#### 改善1: データ期間拡張（最優先）
```
現状: 2020-2025（5年間）
改善: 2010-2025（15年間）
期待効果: AUC +0.02～0.03
```

#### 改善2: 特徴量追加
```
現状: 36個の特徴量から29個を選択
改善: 血統データ、調教タイム、馬場状態を追加
期待効果: AUC +0.03～0.05
```

#### 改善3: オッズAPI連携
```
現状: ダミーオッズ
改善: netkeiba APIからリアルタイムオッズを取得
期待効果: 実用性向上
```

#### 改善4: Phase 7再実行（より多くの特徴量を保持）
```
現状: 削減率19%（7個削除）
改善: alpha=0.15、two-step=True で35-40特徴量を保持
期待効果: AUC +0.02～0.03
```

#### 改善5: Phase 8再実行（より多くの試行）
```
現状: n_trials=100
改善: n_trials=300、timeout=14400
期待効果: AUC +0.01～0.02
```

#### 改善6: アンサンブルモデル
```
現状: LightGBM単体
改善: LightGBM + XGBoost + CatBoost のアンサンブル
期待効果: AUC +0.02～0.04
```

---

## 📞 サポート

問題が発生した場合は、以下を確認してください:

1. **Phase 8完了状況**
   ```batch
   dir data\models\tuned\*_tuned_model.txt
   ```

2. **Phase 7完了状況**
   ```batch
   dir data\features\selected\*_selected_features.csv
   ```

3. **Phase 0-4実行状況**
   ```batch
   dir data\predictions\phase4\*20260211*.csv
   ```

---

**Phase 10で毎日の予測・配信、頑張ってください！** 🏇✨

詳細ドキュメント: [PHASE10_README.md](PHASE10_README.md)
