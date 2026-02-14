# データ検証スクリプト 実行手順書

**作成日**: 2026-02-14  
**対象**: Eドライブのデータ完全性確認

---

## 📍 スクリプト保存場所

### 推奨保存先

```
E:\anonymous-keiba-ai\scripts_jra\validation\
```

このディレクトリに以下の2ファイルを保存してください：
- `check_data_completeness.bat`
- `check_data_completeness.ps1`

---

## 🚀 実行手順（3ステップ）

### Step 1: GitHubからスクリプトをダウンロード

#### 方法A: ブラウザでダウンロード（簡単）

1. ブラウザで以下のURLにアクセス：
   ```
   https://github.com/aka209859-max/anonymous-keiba-ai/tree/phase0_complete_fix_2026_02_07/scripts_jra/validation
   ```

2. `check_data_completeness.bat` をクリック

3. 右上の「Raw」ボタンをクリック

4. ページ全体を選択（Ctrl+A）してコピー（Ctrl+C）

5. メモ帳を開いて貼り付け（Ctrl+V）

6. 「名前を付けて保存」で以下に保存：
   ```
   E:\anonymous-keiba-ai\scripts_jra\validation\check_data_completeness.bat
   ```
   - **重要**: 「ファイルの種類」を「すべてのファイル」に変更
   - 「エンコード」は「ANSI」または「UTF-8」

7. 同様に `check_data_completeness.ps1` もダウンロード

#### 方法B: Git Clone（推奨）

```cmd
# Eドライブに移動
E:
cd \

# リポジトリをクローン
git clone https://github.com/aka209859-max/anonymous-keiba-ai.git

# ブランチ切り替え
cd anonymous-keiba-ai
git checkout phase0_complete_fix_2026_02_07
```

これで `E:\anonymous-keiba-ai\scripts_jra\validation\` にスクリプトが配置されます。

---

### Step 2: スクリプト実行

#### 簡易版（バッチファイル）

1. エクスプローラーで以下のフォルダを開く：
   ```
   E:\anonymous-keiba-ai\scripts_jra\validation\
   ```

2. `check_data_completeness.bat` をダブルクリック

3. コマンドプロンプトが開いて自動実行されます

4. 完了後、「レポートを開きますか？ (Y/N)」と表示されたら `Y` を入力

5. メモ帳でレポートが開きます

#### 詳細版（PowerShell）

1. エクスプローラーで以下のフォルダを開く：
   ```
   E:\anonymous-keiba-ai\scripts_jra\validation\
   ```

2. フォルダ内で `Shift + 右クリック` → 「PowerShell ウィンドウをここで開く」

3. 以下のコマンドを実行：
   ```powershell
   # 初回のみ実行ポリシー設定
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   
   # スクリプト実行
   .\check_data_completeness.ps1
   ```

4. 完了後、「レポートを開きますか？ (Y/N)」と表示されたら `y` を入力

5. メモ帳でレポートが開きます

---

### Step 3: レポート確認

#### 出力ファイル

- **バッチ版**: `E:\anonymous-keiba-ai\scripts_jra\validation\data_validation_report.txt`
- **PowerShell版**: `E:\anonymous-keiba-ai\scripts_jra\validation\data_validation_report_detailed.txt`

#### 確認ポイント

1. **JRA-VAN データ**
   ```
   === 1. JRA-VAN データ構造 ===
   ✓ E:\jra-keiba-data\jravan\raw が存在します
   
     総ファイル数: 42,350
     （推奨: 30,000-50,000 ファイル）
   ```
   
   - ✅ ファイル数が 30,000 以上 → データ完全
   - ⚠️ ファイル数が 10,000～30,000 → 部分的にデータあり
   - ❌ ファイル数が 10,000 未満 → データ不足

2. **JRDB データ**
   ```
   === 5. JRDB データ構造 ===
   ✓ E:\jrdb_data\raw が存在します
   
     総ファイル数: 48,920
     （推奨: 40,000-60,000 ファイル）
   ```
   
   - ✅ ファイル数が 40,000 以上 → データ完全
   - ⚠️ ファイル数が 15,000～40,000 → 部分的にデータあり
   - ❌ ファイル数が 15,000 未満 → データ不足

3. **TARGET frontier JV**
   ```
   === 8. TARGET frontier JV データベース確認 ===
   ✓ C:\TARGET\ が存在します
   📁 C:\TARGET\database\target.db (1,250 MB)
   ```
   
   - データベースファイルのパスをメモしておく

---

## ⚠️ トラブルシューティング

### エラー1: 「アクセスが拒否されました」

**原因**: 管理者権限が必要

**対処**:
1. `check_data_completeness.bat` を右クリック
2. 「管理者として実行」を選択

---

### エラー2: 「スクリプトの実行が無効です」（PowerShell）

**原因**: 実行ポリシーが制限されている

**対処**:
```powershell
# PowerShell を管理者として開く
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### エラー3: 「E:\jra-keiba-data が存在しません」

**原因**: データの保存場所が異なる

**対処方法1**: スクリプトを編集してパスを変更

1. `check_data_completeness.bat` をメモ帳で開く

2. 以下の行を探す：
   ```bat
   set "JRAVAN_BASE=E:\jra-keiba-data\jravan\raw"
   ```

3. 実際のパスに変更（例）：
   ```bat
   set "JRAVAN_BASE=D:\競馬データ\jravan\raw"
   ```

4. 保存して再実行

**対処方法2**: データを推奨パスに移動

```
実際の場所: D:\競馬データ\
推奨場所: E:\jra-keiba-data\jravan\raw\

→ D:\競馬データ\ を E:\jra-keiba-data\jravan\raw\ にコピー
```

---

### エラー4: 「文字化けしています」

**原因**: 文字エンコーディングの問題

**対処**:
1. レポートファイルを右クリック → 「プログラムから開く」 → 「メモ帳」
2. メモ帳で「ファイル」→「名前を付けて保存」
3. 「エンコード」を「UTF-8」に変更して保存

---

## 📊 レポートの見方

### 判定基準

| 判定 | 意味 | 次のアクション |
|------|------|---------------|
| ✅ | データ完全（15年分揃っている） | Phase 0 スキップ可能 |
| ⚠️ | データ部分的（5-10年程度） | 不足期間を追加取得 |
| ❌ | データ不足（ほぼ空） | Phase 0 フルダウンロード必要 |

### サマリー例（理想的なケース）

```
=== 9. 統合サマリー ===

【JRA-VAN データ状況】
  ✓ データあり
  ファイル数: 42,350
  データサイズ: 35.6 GB
  判定: ✅ 15年分のデータが揃っている可能性が高い

【JRDB データ状況】
  ✓ データあり
  ファイル数: 48,920
  データサイズ: 22.3 GB
  判定: ✅ 15年分のデータが揃っている可能性が高い

【TARGET frontier JV】
  ✓ データベースファイル検出
  ファイル数: 1
  📁 C:\TARGET\database\target.db (1,250 MB)
  
  次のステップ:
  1. DB Browser for SQLite でスキーマ確認
  2. テーブル構造解析
  3. Python で読み込みテスト
```

このレポートなら **Phase 0（データ取得）をスキップして Phase 1（特徴量生成）に直行できます！**

---

## 🎯 レポート確認後の次のステップ

### ケース1: ✅ データ完全

1. レポートをコピーして新セッションに貼り付け
2. 「データ完全、Phase 0 スキップして Phase 1 へ」と指示
3. ETL スクリプト作成（既存データを統合テーブルへ投入）

### ケース2: ⚠️ データ部分的

1. 不足している年度をレポートから特定
2. その年度のみ JRA-VAN/JRDB から追加取得
3. 既存データとマージ

### ケース3: ❌ データなし

1. Phase 0 フルダウンロード実行
2. JRA-VAN: 約30時間
3. JRDB: 数時間

---

## 📝 メモ

レポート実行後、以下の情報を新セッションに提供してください：

```
【データ検証結果】
- JRA-VAN: ✅/⚠️/❌
- JRDB: ✅/⚠️/❌
- TARGET DB: 検出/未検出
- 総ファイル数: [数値]
- 総データサイズ: [数値] GB

【レポート添付】
data_validation_report.txt の全文
```

---

**更新履歴**:
- 2026-02-14: 初版作成（実行手順書）
