# 🚀 完全修正版 クイックスタートガイド

## 📥 Windows へのダウンロード（最速）

```powershell
# PowerShell で実行
cd E:\anonymous-keiba-ai

# GitHub から最新版を取得
$url1 = "https://raw.githubusercontent.com/aka209859-max/anonymous-keiba-ai/phase0_complete_fix_2026_02_07/run_all_optimized.bat"
$url2 = "https://raw.githubusercontent.com/aka209859-max/anonymous-keiba-ai/phase0_complete_fix_2026_02_07/run_all.bat"
Invoke-WebRequest -Uri $url1 -OutFile "run_all_optimized.bat"
Invoke-WebRequest -Uri $url2 -OutFile "run_all.bat"
```

## 🎯 即座に実行

```cmd
cd E:\anonymous-keiba-ai

REM 新モデル (Phase 7-8-5) で船橋を実行
run_all_optimized.bat 43 2026-02-13

REM 出力確認
notepad predictions\船橋_20260213_note.txt
```

## 🏇 競馬場コード一覧

```
43 = 船橋    48 = 名古屋    51 = 姫路    55 = 佐賀
30 = 門別    35 = 盛岡      36 = 水沢    42 = 浦和
44 = 大井    45 = 川崎      46 = 金沢    47 = 笠松
50 = 園田    54 = 高知
```

## 📊 主要な修正点

- ✅ エンコーディング問題を完全解決
- ✅ 年パス形式を修正 (`%YEAR:~-2%` → `%YEAR%`)
- ✅ 全14競馬場の日本語名マッピング
- ✅ Phase 7-8-5 新モデル完全対応
- ✅ Phase 6 への ensemble_optimized.csv 渡し

## 🔍 修正確認コマンド

```cmd
cd E:\anonymous-keiba-ai

REM 日本語名が正しいか確認
findstr "KEIBAJO_NAME=船橋" run_all_optimized.bat

REM Phase 6 呼び出しが正しいか確認
findstr "OUTPUT_ENSEMBLE" run_all_optimized.bat | findstr "DAILY_OPERATION"
```

## 📖 詳細ガイド

完全な修正内容と詳細手順は以下を参照:
- `COMPLETE_BATCH_FIX_GUIDE.md`

## 🆘 トラブル時

エラーが出たら:
1. ファイルを再ダウンロード (上記 PowerShell コマンド)
2. `E:\anonymous-keiba-ai` から実行しているか確認
3. 競馬場コードが正しいか確認

## 📞 サポート

問題報告時は以下を提供:
- 実行したコマンド
- エラーメッセージ
- `dir run_all_optimized.bat` の結果

---

**完全修正版準備完了！**

GitHub: https://github.com/aka209859-max/anonymous-keiba-ai/tree/phase0_complete_fix_2026_02_07
