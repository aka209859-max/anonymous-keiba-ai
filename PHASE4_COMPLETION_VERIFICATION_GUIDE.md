# Phase 4 完了確認ガイド

**作成日**: 2026-02-04  
**目的**: Phase 4の実行結果を効率的に確認する方法

---

## 📊 Phase 4 で生成されるファイル

### 各競馬場ごとに以下のファイルが生成されます

#### データファイル（中間生成物）
```
ooi_2023-2024_v3_with_race_id.csv       # race_id追加後のデータ
ooi_2023-2024_v3_time.csv               # target変換後のデータ
```

#### モデルファイル（重要）
```
ooi_2023-2024_v3_model.txt                       # 二値分類（Phase 3）
ooi_2023-2024_v3_with_race_id_ranking_model.txt  # ランキング（Phase 4）
ooi_2023-2024_v3_time_regression_model.txt       # 回帰（Phase 4）
```

#### 評価ファイル（重要）
```
ooi_2023-2024_v3_score.txt                      # 二値分類評価
ooi_2023-2024_v3_with_race_id_ranking_score.txt # ランキング評価
ooi_2023-2024_v3_time_regression_score.txt      # 回帰評価
```

#### 特徴量重要度グラフ（参考）
```
ooi_2023-2024_v3_model.png
ooi_2023-2024_v3_with_race_id_ranking_model.png
ooi_2023-2024_v3_time_regression_model.png
```

### 全競馬場の合計
- データファイル: 20個（10競馬場 × 2種類）
- モデルファイル: 30個（10競馬場 × 3種類）
- 評価ファイル: 30個（10競馬場 × 3種類）
- グラフファイル: 30個（10競馬場 × 3種類）
- **合計: 110個のファイル**

---

## 🎯 推奨方法1: サマリーファイルを作成してGitHubにプッシュ

### Step 1: サマリーファイル作成スクリプト

以下のスクリプトを作成して実行：

```python
# create_phase4_summary.py
import os
import glob

def create_summary():
    """Phase 4の実行結果サマリーを作成"""
    
    summary = []
    summary.append("=" * 80)
    summary.append("Phase 4 実行結果サマリー")
    summary.append("=" * 80)
    summary.append("")
    
    # 各競馬場の評価ファイルを読み込み
    venues = [
        ('44', '大井', 'ooi_2023-2024_v3'),
        ('43', '船橋', 'funabashi_2020-2025_v3'),
        ('45', '川崎', 'kawasaki_2020-2025_v3'),
        ('42', '浦和', 'urawa_2020-2025_v3'),
        ('48', '名古屋', 'nagoya_2022-2025_v3'),
        ('50', '園田', 'sonoda_2020-2025_v3'),
        ('47', '笠松', 'kasamatsu_2020-2025_v3'),
        ('55', '佐賀', 'saga_2020-2025_v3'),
        ('54', '高知', 'kochi_2020-2025_v3'),
        ('51', '姫路', 'himeji_2020-2025_v3'),
    ]
    
    for code, name, base in venues:
        summary.append(f"\n{'='*80}")
        summary.append(f"【{name}（コード: {code}）】")
        summary.append(f"{'='*80}")
        
        # ランキング評価
        ranking_score_file = f"{base}_with_race_id_ranking_score.txt"
        if os.path.exists(ranking_score_file):
            summary.append(f"\n■ ランキングモデル評価")
            summary.append(f"  ファイル: {ranking_score_file}")
            with open(ranking_score_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 評価指標部分を抽出
                if '【評価指標】' in content:
                    eval_section = content.split('【評価指標】')[1].split('【')[0]
                    summary.append(eval_section.strip())
        else:
            summary.append(f"\n■ ランキングモデル評価: ファイルなし")
        
        # 回帰評価
        regression_score_file = f"{base}_time_regression_score.txt"
        if os.path.exists(regression_score_file):
            summary.append(f"\n■ 回帰モデル評価")
            summary.append(f"  ファイル: {regression_score_file}")
            with open(regression_score_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 評価指標部分を抽出
                if '【評価指標】' in content:
                    eval_section = content.split('【評価指標】')[1].split('【')[0]
                    summary.append(eval_section.strip())
        else:
            summary.append(f"\n■ 回帰モデル評価: ファイルなし")
    
    # ファイルカウント
    summary.append(f"\n\n{'='*80}")
    summary.append("ファイル生成状況")
    summary.append(f"{'='*80}")
    
    ranking_models = glob.glob('*_ranking_model.txt')
    regression_models = glob.glob('*_regression_model.txt')
    ranking_scores = glob.glob('*_ranking_score.txt')
    regression_scores = glob.glob('*_regression_score.txt')
    
    summary.append(f"\nランキングモデル: {len(ranking_models)}個")
    summary.append(f"回帰モデル: {len(regression_models)}個")
    summary.append(f"ランキング評価: {len(ranking_scores)}個")
    summary.append(f"回帰評価: {len(regression_scores)}個")
    
    summary.append(f"\n合計: {len(ranking_models) + len(regression_models)}個のモデル")
    
    # サマリーを保存
    summary_file = 'PHASE4_EXECUTION_SUMMARY.txt'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(summary))
    
    print(f"✓ サマリーファイル作成完了: {summary_file}")
    return summary_file

if __name__ == "__main__":
    create_summary()
```

### Step 2: サマリーファイルをGitHubにプッシュ

```bash
cd E:\anonymous-keiba-ai

# サマリー作成
python create_phase4_summary.py

# GitHubにプッシュ
git add PHASE4_EXECUTION_SUMMARY.txt
git commit -m "feat: Phase 4実行結果サマリーを追加

10競馬場のランキング学習・回帰分析の評価結果をまとめたサマリーファイル

内容:
- 各競馬場のランキングモデル評価（NDCG@1, @3, @5, @10）
- 各競馬場の回帰モデル評価（RMSE, MAE, R²）
- ファイル生成状況（モデル数、評価ファイル数）

期間: 2026-02-04
ステータス: Phase 4完了"

git push origin phase4_specialized_models
```

---

## 🎯 推奨方法2: スクリーンショット + 重要ファイルのみアップロード

### アップロードすべき重要ファイル（優先度高）

#### 1. 評価サマリー（最重要）
```bash
# サマリーファイル作成（上記のスクリプト）
PHASE4_EXECUTION_SUMMARY.txt

# または手動で作成
PHASE4_RESULTS.md
```

#### 2. 各競馬場の評価ファイル（各3KB程度）
```bash
# テキストファイルなので軽い
*_ranking_score.txt   (10ファイル)
*_regression_score.txt (10ファイル)

# 合計20ファイル、約60KB
```

#### 3. 実行ログ（あれば）
```bash
training_log.txt
run_phase4_training_log.txt
```

### GitHubにアップロード

```bash
cd E:\anonymous-keiba-ai

# 評価ファイルのみを追加
git add *_ranking_score.txt
git add *_regression_score.txt
git add PHASE4_EXECUTION_SUMMARY.txt

git commit -m "feat: Phase 4実行結果の評価ファイルを追加

10競馬場のランキング・回帰モデルの評価結果

ランキングモデル:
- 評価指標: NDCG@1, @3, @5, @10
- 10競馬場の評価完了

回帰モデル:
- 評価指標: RMSE, MAE, R²
- 10競馬場の評価完了

期間: 2026-02-04"

git push origin phase4_specialized_models
```

---

## 🎯 推奨方法3: .gitignore でモデルファイルを除外

### モデルファイルは大きいので除外

```bash
# .gitignore に追加
echo "*_model.txt" >> .gitignore
echo "*_model.png" >> .gitignore
echo "*.csv" >> .gitignore

# 評価ファイルのみをコミット
git add .gitignore
git add *_score.txt
git add PHASE4_EXECUTION_SUMMARY.txt

git commit -m "chore: モデルファイルをgitignoreに追加

大容量ファイルを除外:
- *_model.txt (モデルファイル: 10～100MB)
- *_model.png (グラフ: 各数百KB)
- *.csv (データファイル: 各10～100MB)

コミット対象:
- *_score.txt (評価ファイル: 各3KB)
- PHASE4_EXECUTION_SUMMARY.txt (サマリー)"

git push origin phase4_specialized_models
```

---

## 📋 私に確認してもらう際の手順

### 方法A: GitHubリンクを共有（推奨）

```
1. 上記の方法で評価ファイルをGitHubにプッシュ
2. PRのURLを共有: https://github.com/aka209859-max/anonymous-keiba-ai/pull/3
3. 私がGitHubで確認
```

### 方法B: サマリーファイルの内容をコピペ

```
1. PHASE4_EXECUTION_SUMMARY.txt を作成
2. 内容を私に直接貼り付け
3. 私が内容を確認
```

### 方法C: 重要な評価指標だけを報告

各競馬場の以下の情報だけを教えてください：

```
【大井】
ランキングモデル:
  - データ件数: 27,219件
  - レース数: 1,234件
  - NDCG@1: 0.XXXX
  - NDCG@3: 0.XXXX

回帰モデル:
  - データ件数: 27,219件
  - RMSE: XX.XX秒
  - MAE: XX.XX秒
  - R²: 0.XXXX

... (他9競馬場も同様)
```

---

## 🎯 最も簡単な方法（超推奨）

### スクリーンショット + 簡易レポート

```bash
cd E:\anonymous-keiba-ai

# 実行結果を確認
dir *_ranking_score.txt
dir *_regression_score.txt

# 各ファイルの内容を確認（例: 大井）
type ooi_2023-2024_v3_with_race_id_ranking_score.txt
type ooi_2023-2024_v3_time_regression_score.txt
```

以下の情報を私に教えてください：

1. **実行成功の確認**
   - ランキングモデル: 何個生成されましたか？
   - 回帰モデル: 何個生成されましたか？

2. **代表的な1競馬場の結果**（例: 大井）
   - ランキング評価: NDCG@1, @3, @5
   - 回帰評価: RMSE, MAE, R²

3. **全体的な感想**
   - エラーは発生しましたか？
   - 学習時間はどのくらいかかりましたか？

---

## 📝 テンプレート: Phase 4完了報告

以下のテンプレートをコピーして、結果を記入してください：

```
# Phase 4 実行完了報告

## 実行環境
- 実行日: 2026-02-XX
- 実行場所: E:\anonymous-keiba-ai
- 実行方法: python run_phase4_training.py

## 実行結果

### ファイル生成状況
- ランキングモデル: [ ]個 / 10個
- 回帰モデル: [ ]個 / 10個
- ランキング評価ファイル: [ ]個 / 10個
- 回帰評価ファイル: [ ]個 / 10個

### 代表例: 大井競馬場

#### ランキングモデル
- データ件数: [    ]件
- レース数: [    ]件
- NDCG@1: 0.[    ]
- NDCG@3: 0.[    ]
- NDCG@5: 0.[    ]

#### 回帰モデル
- データ件数: [    ]件
- RMSE: [  ]秒
- MAE: [  ]秒
- R²: 0.[    ]

### エラー・問題
- [ ] エラーなし
- [ ] エラーあり: [エラー内容]

### 学習時間
- 全体: 約[  ]時間

## その他コメント
[自由記入]
```

---

## 🎯 結論: あなたにおすすめの方法

### 最もシンプルな方法

1. **評価ファイルをGitHubにプッシュ**
   ```bash
   git add *_ranking_score.txt *_regression_score.txt
   git commit -m "feat: Phase 4実行結果"
   git push origin phase4_specialized_models
   ```

2. **PRのリンクを私に共有**
   - https://github.com/aka209859-max/anonymous-keiba-ai/pull/3

3. **または、上記のテンプレートを記入して私に報告**

---

**作成者**: Anonymous Keiba AI Development Team  
**最終更新**: 2026-02-04  
**ステータス**: 準備完了 ✅
