# Phase 10: 個人用購入判断ツール

**注意**: Phase 10は配信には使用しません。個人的な購入判断にのみ使用してください。

---

## 🎯 Phase 10の位置づけ

### Phase 8（配信用）
```
RUN_PHASE8_TO_PHASE6.bat 43 2026-02-11
→ 配信テキスト生成（Note/X/Bookers）
```

### Phase 10（個人用）
```
RUN_PHASE10_DAILY.bat 43 2026-02-11
→ 予測確率CSV生成
→ レース直前にオッズ確認
→ 期待値計算 → 購入判断
```

---

## 📁 Phase 10関連ファイル

### メインスクリプト
- `scripts/phase10_daily_prediction/run_daily_prediction.py`

### バッチファイル
- `RUN_PHASE10_DAILY.bat`
- `RUN_PHASE10_ALL_VENUES.bat`

### ドキュメント
- `PHASE10_README.md`
- `PHASE10_QUICKSTART.md`
- `PHASE10_COMPLETION_REPORT.md`
- `PHASE10_SUMMARY.txt`

---

## 🚀 使い方

### 基本コマンド
```batch
RUN_PHASE10_DAILY.bat 43 2026-02-11
```

### 出力ファイル
- `data/predictions/phase10/funabashi_20260211_predictions.csv`
- `data/predictions/phase10/funabashi_20260211_summary.txt`

---

## 💡 将来の拡張可能性

### オッズAPI連携
```python
# 将来的にNetkeibaのオッズAPIが利用可能になった場合
odds = fetch_odds_from_api(race_id)
ev = (predicted_prob * odds) - 1
if ev > 0.05:
    recommended_bets.append({
        'horse': horse_id,
        'bet_amount': kelly_bet(ev, odds, bankroll)
    })
```

### 自動購入
```python
# さらに将来的にJRA-VANなどの購入APIが利用可能になった場合
if ev > 0.10:  # 期待値10%以上
    auto_place_bet(horse_id, bet_amount)
```

---

## ⚠️ 注意事項

- Phase 10は配信には使用しない
- オッズはリアルタイムで変動するため、事前配信不可
- 個人的な購入判断にのみ使用
- Phase 8の予測確率 + 実際のオッズ で期待値を計算

---

## ✅ 推奨フロー

### 朝（配信用）
```batch
RUN_PHASE8_TO_PHASE6.bat 43 2026-02-11
→ Note/X/Bookersで配信
```

### レース前（個人用）
```batch
RUN_PHASE10_DAILY.bat 43 2026-02-11
→ 予測確率を確認
→ Netkeibaでオッズを確認
→ 期待値計算
→ 購入判断
```

---

**Phase 10は削除せず、個人用ツールとして保管してください。**
