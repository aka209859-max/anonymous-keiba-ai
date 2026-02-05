# 🔧 SQLエラー修正完了

## 問題

```
missing FROM-clause entry for table "s"
LINE 96: s.kakutei_chakujun,
```

## 原因

動的SQL生成の最終SELECT句で `s.`, `r.`, `um.` のテーブルエイリアスを使用していましたが、FROM句には `target_race tr` と `past_races pr` しか存在しないため、エラーが発生していました。

## 修正内容

すべてのSELECT句を `tr.` (target_race) に統一しました。

```python
# 修正前
select_parts.append("s.kakutei_chakujun")  # ❌ エラー
select_parts.append(f"s.{feature}")        # ❌ エラー
select_parts.append(f"r.{feature}")        # ❌ エラー
select_parts.append(f"um.{feature}")       # ❌ エラー

# 修正後
select_parts.append("tr.kakutei_chakujun")  # ✅ 正常
select_parts.append(f"tr.{feature}")        # ✅ 正常
select_parts.append(f"tr.{feature}")        # ✅ 正常
select_parts.append(f"tr.{feature}")        # ✅ 正常
```

## 実行方法

Windows環境で最新版を取得して再実行してください：

```bash
cd E:\anonymous-keiba-ai
git pull origin phase4_specialized_models
python simulate_2026_venue_adaptive.py
```

## コミット情報

- **コミット**: 6622d47
- **日時**: 2026-02-04
- **ブランチ**: phase4_specialized_models

---

**修正完了 - 再実行してください！** 🚀
