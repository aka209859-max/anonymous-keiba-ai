# Phase 4.5 実データ検証計画書

**作成日**: 2026-02-05  
**期間**: 2026-02-06 ~ 2026-02-07  
**目的**: Phase 4 完成モデルの実戦性能を2026年1月データで検証

---

## 📋 検証の目的

Phase 4 で完成した全14競馬場・42モデルを実際の2026年1月データで検証し、以下を明確化：

1. **各モデルの実戦精度**: 学習データと実データでの精度差
2. **モデル間の性能比較**: 二値分類 vs ランキング vs 回帰
3. **競馬場ごとの特性**: どの競馬場で予測精度が高いか
4. **アンサンブル重みの最適化**: 3モデルの最適な重み配分を決定
5. **買い目生成の準備**: Phase 5 に向けた実戦データの蓄積

---

## 📊 検証対象

### 対象期間
- **2026年1月1日 ~ 2026年1月31日**
- 全14競馬場の1月開催データ

### 推定データ量
- **レース数**: 約500~800レース
- **出走数**: 約5,000~10,000件
- **競馬場**: 全14場（開催状況による）

### 検証モデル
- **Phase 3 (二値分類)**: 14モデル
- **Phase 4 (ランキング)**: 14モデル
- **Phase 4 (回帰)**: 14モデル
- **合計**: 42モデル

---

## 🔧 実施手順

### Step 1: 2026年1月データの抽出

#### 1.1 データベース確認
```sql
-- 2026年1月のデータ件数を確認
SELECT 
    keibajo_code,
    COUNT(*) as race_count,
    COUNT(DISTINCT kaisai_nengappi || TO_CHAR(race_bango, 'FM00')) as race_count_distinct
FROM jvd_race
WHERE kaisai_nengappi >= '2026-01-01'
  AND kaisai_nengappi <= '2026-01-31'
GROUP BY keibajo_code
ORDER BY keibajo_code;
```

#### 1.2 SQLファイルの準備

既存のPhase 2 SQLファイルを参考に、2026年1月専用のSQLを作成：

```bash
# 例: 大井競馬場 2026年1月
cd E:\anonymous-keiba-ai\sql

# ベースSQLをコピー
cp ooi_2023-2025_v3.sql ooi_2026_jan_test.sql

# 期間を修正
# WHERE r.kaisai_nengappi >= '2026-01-01' AND r.kaisai_nengappi <= '2026-01-31'
```

#### 1.3 テストデータCSV作成

```bash
cd E:\anonymous-keiba-ai

# 各競馬場のテストデータを作成
psql -h localhost -U postgres -d keiba -f sql/ooi_2026_jan_test.sql -o csv/ooi_2026_jan_test.csv
# 以下同様に全14競馬場分を作成
```

---

### Step 2: 予測実行スクリプトの作成

#### 2.1 予測スクリプト: `predict_phase3.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 二値分類モデルで予測を実行
"""

import sys
import pandas as pd
import lightgbm as lgb
import numpy as np
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score

def predict_binary_classification(test_csv, model_path, output_path):
    """
    二値分類モデルで予測を実行
    
    Parameters
    ----------
    test_csv : str
        テストデータCSV
    model_path : str
        学習済みモデルパス
    output_path : str
        予測結果の出力先
    """
    # テストデータ読み込み
    print(f"テストデータ読み込み: {test_csv}")
    df = pd.read_csv(test_csv)
    print(f"データ件数: {len(df)}")
    
    # target列を確保（正解ラベル）
    if 'target' not in df.columns:
        raise ValueError("target列が見つかりません")
    
    y_true = df['target']
    
    # 不要列を除外
    exclude_cols = ['target', 'kakutei_chakujun', 'race_id', 'umaban']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    X_test = df[feature_cols]
    
    # モデル読み込み
    print(f"モデル読み込み: {model_path}")
    model = lgb.Booster(model_file=model_path)
    
    # 予測
    print("予測実行中...")
    y_pred_proba = model.predict(X_test, num_iteration=model.best_iteration)
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    # 評価
    auc = roc_auc_score(y_true, y_pred_proba)
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    # 結果を出力
    results = {
        'AUC': auc,
        'Accuracy': accuracy,
        'Precision': precision,
        'Recall': recall,
        'F1-Score': f1
    }
    
    print("\n=== 評価結果 ===")
    for metric, value in results.items():
        print(f"{metric}: {value:.4f}")
    
    # 予測結果をCSVに保存
    df['predicted_proba'] = y_pred_proba
    df['predicted'] = y_pred
    df.to_csv(output_path, index=False)
    print(f"\n予測結果を保存: {output_path}")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("使用法: python predict_phase3.py <test_csv> <model_path> <output_csv>")
        sys.exit(1)
    
    test_csv = sys.argv[1]
    model_path = sys.argv[2]
    output_path = sys.argv[3]
    
    predict_binary_classification(test_csv, model_path, output_path)
```

#### 2.2 予測スクリプト: `predict_phase4_ranking.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4 ランキングモデルで予測を実行
"""

import sys
import pandas as pd
import lightgbm as lgb
import numpy as np
from sklearn.metrics import ndcg_score

def predict_ranking(test_csv, model_path, output_path):
    """
    ランキングモデルで予測を実行
    
    Parameters
    ----------
    test_csv : str
        テストデータCSV (race_id必須)
    model_path : str
        学習済みモデルパス
    output_path : str
        予測結果の出力先
    """
    # テストデータ読み込み
    print(f"テストデータ読み込み: {test_csv}")
    df = pd.read_csv(test_csv)
    print(f"データ件数: {len(df)}")
    
    # race_idが必須
    if 'race_id' not in df.columns:
        raise ValueError("race_id列が見つかりません")
    
    # target列を確保（正解ラベル）
    if 'target' not in df.columns:
        raise ValueError("target列が見つかりません")
    
    y_true = df['target']
    race_ids = df['race_id']
    
    # 不要列を除外
    exclude_cols = ['target', 'kakutei_chakujun', 'race_id', 'umaban']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    X_test = df[feature_cols]
    
    # モデル読み込み
    print(f"モデル読み込み: {model_path}")
    model = lgb.Booster(model_file=model_path)
    
    # 予測
    print("予測実行中...")
    y_pred_score = model.predict(X_test, num_iteration=model.best_iteration)
    
    # レースごとにNDCGを計算
    unique_races = df['race_id'].unique()
    ndcg_at_k = {k: [] for k in [1, 3, 5, 10]}
    
    for race_id in unique_races:
        race_mask = df['race_id'] == race_id
        y_true_race = y_true[race_mask].values
        y_pred_race = y_pred_score[race_mask]
        
        # NDCGを計算
        for k in [1, 3, 5, 10]:
            if len(y_true_race) >= k:
                ndcg = ndcg_score([y_true_race], [y_pred_race], k=k)
                ndcg_at_k[k].append(ndcg)
    
    # 平均NDCG
    results = {}
    for k, values in ndcg_at_k.items():
        results[f'NDCG@{k}'] = np.mean(values) if values else 0.0
    
    print("\n=== 評価結果 ===")
    for metric, value in results.items():
        print(f"{metric}: {value:.4f}")
    
    # 予測結果をCSVに保存
    df['predicted_score'] = y_pred_score
    df.to_csv(output_path, index=False)
    print(f"\n予測結果を保存: {output_path}")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("使用法: python predict_phase4_ranking.py <test_csv> <model_path> <output_csv>")
        sys.exit(1)
    
    test_csv = sys.argv[1]
    model_path = sys.argv[2]
    output_path = sys.argv[3]
    
    predict_ranking(test_csv, model_path, output_path)
```

#### 2.3 予測スクリプト: `predict_phase4_regression.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4 回帰モデルで予測を実行
"""

import sys
import pandas as pd
import lightgbm as lgb
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

def predict_regression(test_csv, model_path, output_path):
    """
    回帰モデルで予測を実行
    
    Parameters
    ----------
    test_csv : str
        テストデータCSV (target=走破タイム)
    model_path : str
        学習済みモデルパス
    output_path : str
        予測結果の出力先
    """
    # テストデータ読み込み
    print(f"テストデータ読み込み: {test_csv}")
    df = pd.read_csv(test_csv)
    print(f"データ件数: {len(df)}")
    
    # target列を確保（正解ラベル: 走破タイム）
    if 'target' not in df.columns:
        raise ValueError("target列が見つかりません")
    
    y_true = df['target']
    
    # 不要列を除外
    exclude_cols = ['target', 'kakutei_chakujun', 'race_id', 'umaban']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    X_test = df[feature_cols]
    
    # モデル読み込み
    print(f"モデル読み込み: {model_path}")
    model = lgb.Booster(model_file=model_path)
    
    # 予測
    print("予測実行中...")
    y_pred = model.predict(X_test, num_iteration=model.best_iteration)
    
    # 評価
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    # 相対誤差（平均走破タイムに対する割合）
    mean_time = y_true.mean()
    relative_error = (mae / mean_time) * 100
    
    results = {
        'RMSE': rmse,
        'MAE': mae,
        'R²': r2,
        '相対誤差(%)': relative_error
    }
    
    print("\n=== 評価結果 ===")
    for metric, value in results.items():
        print(f"{metric}: {value:.4f}")
    
    # 予測結果をCSVに保存
    df['predicted_time'] = y_pred
    df['time_error'] = y_pred - y_true
    df.to_csv(output_path, index=False)
    print(f"\n予測結果を保存: {output_path}")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("使用法: python predict_phase4_regression.py <test_csv> <model_path> <output_csv>")
        sys.exit(1)
    
    test_csv = sys.argv[1]
    model_path = sys.argv[2]
    output_path = sys.argv[3]
    
    predict_regression(test_csv, model_path, output_path)
```

---

### Step 3: 一括予測実行

#### 3.1 一括予測スクリプト: `run_phase45_verification.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4.5 検証: 全14競馬場・3モデルで2026年1月データを予測
"""

import os
import subprocess
import pandas as pd
from pathlib import Path

# 競馬場リスト
VENUES = [
    'funabashi', 'himeji', 'kanazawa', 'kasamatsu', 'kawasaki',
    'kochi', 'mizusawa', 'monbetsu', 'morioka', 'nagoya',
    'ooi', 'saga', 'sonoda', 'urawa'
]

# モデルタイプ
MODEL_TYPES = {
    'binary': {
        'script': 'predict_phase3.py',
        'model_suffix': '_v3_model.txt',
        'output_suffix': '_2026_jan_binary_prediction.csv'
    },
    'ranking': {
        'script': 'predict_phase4_ranking.py',
        'model_suffix': '_v3_with_race_id_ranking_model.txt',
        'output_suffix': '_2026_jan_ranking_prediction.csv'
    },
    'regression': {
        'script': 'predict_phase4_regression.py',
        'model_suffix': '_v3_time_regression_model.txt',
        'output_suffix': '_2026_jan_regression_prediction.csv'
    }
}

def run_prediction(venue, model_type, test_csv_dir, model_dir, output_dir):
    """
    指定された競馬場・モデルタイプで予測を実行
    
    Parameters
    ----------
    venue : str
        競馬場名（例: ooi, funabashi）
    model_type : str
        モデルタイプ（binary, ranking, regression）
    test_csv_dir : str
        テストデータCSVのディレクトリ
    model_dir : str
        学習済みモデルのディレクトリ
    output_dir : str
        予測結果の出力先ディレクトリ
    
    Returns
    -------
    dict or None
        評価結果の辞書、または失敗時None
    """
    config = MODEL_TYPES[model_type]
    script = config['script']
    model_suffix = config['model_suffix']
    output_suffix = config['output_suffix']
    
    # 競馬場名の表記揺れ対応
    venue_variations = [venue]
    if venue == 'monbetsu':
        venue_variations.append('mombetsu')
    
    # テストCSVを探す
    test_csv = None
    for var in venue_variations:
        test_csv_candidate = os.path.join(test_csv_dir, f"{var}_2026_jan_test.csv")
        if os.path.exists(test_csv_candidate):
            test_csv = test_csv_candidate
            break
    
    if not test_csv:
        print(f"❌ テストCSVが見つかりません: {venue}")
        return None
    
    # モデルパスを探す
    model_path = None
    for var in venue_variations:
        model_path_candidate = os.path.join(model_dir, f"{var}{model_suffix}")
        if os.path.exists(model_path_candidate):
            model_path = model_path_candidate
            break
    
    if not model_path:
        print(f"❌ モデルが見つかりません: {venue} - {model_type}")
        return None
    
    # 出力パス
    output_path = os.path.join(output_dir, f"{venue}{output_suffix}")
    
    # 予測実行
    print(f"\n{'='*60}")
    print(f"🏇 競馬場: {venue} | モデル: {model_type}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            ['python', script, test_csv, model_path, output_path],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return {'venue': venue, 'model_type': model_type, 'status': 'success'}
    except subprocess.CalledProcessError as e:
        print(f"❌ エラー発生: {e}")
        print(e.stderr)
        return {'venue': venue, 'model_type': model_type, 'status': 'failed', 'error': str(e)}

def main():
    """
    Phase 4.5 検証を一括実行
    """
    # ディレクトリ設定
    test_csv_dir = 'csv/2026_jan_test'
    model_dir = 'models'
    output_dir = 'predictions/2026_jan'
    
    # 出力ディレクトリ作成
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("Phase 4.5 実データ検証 - 2026年1月")
    print("=" * 60)
    print(f"競馬場数: {len(VENUES)}")
    print(f"モデル数: {len(MODEL_TYPES)}")
    print(f"総予測数: {len(VENUES) * len(MODEL_TYPES)}")
    print("=" * 60)
    
    results = []
    
    # 全競馬場・全モデルで予測実行
    for venue in VENUES:
        for model_type in MODEL_TYPES.keys():
            result = run_prediction(venue, model_type, test_csv_dir, model_dir, output_dir)
            if result:
                results.append(result)
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("Phase 4.5 検証完了")
    print("=" * 60)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] == 'failed')
    
    print(f"成功: {success_count}/{len(results)}")
    print(f"失敗: {failed_count}/{len(results)}")
    
    # 失敗した予測を表示
    if failed_count > 0:
        print("\n❌ 失敗した予測:")
        for r in results:
            if r['status'] == 'failed':
                print(f"  - {r['venue']} - {r['model_type']}")
    
    # 結果をCSVに保存
    results_df = pd.DataFrame(results)
    results_df.to_csv(os.path.join(output_dir, 'verification_summary.csv'), index=False)
    print(f"\n検証結果を保存: {output_dir}/verification_summary.csv")

if __name__ == "__main__":
    main()
```

---

### Step 4: 評価レポート生成

#### 4.1 評価集計スクリプト: `generate_phase45_report.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4.5 検証レポート生成
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def collect_results(predictions_dir):
    """
    予測結果CSVから評価指標を収集
    
    Parameters
    ----------
    predictions_dir : str
        予測結果CSVのディレクトリ
    
    Returns
    -------
    pd.DataFrame
        全競馬場・全モデルの評価指標
    """
    results = []
    
    # 全予測結果CSVをスキャン
    for csv_file in Path(predictions_dir).glob('*_prediction.csv'):
        # ファイル名から競馬場とモデルタイプを抽出
        filename = csv_file.stem  # 拡張子を除いたファイル名
        parts = filename.split('_')
        
        venue = parts[0]
        model_type = None
        if 'binary' in filename:
            model_type = 'binary'
        elif 'ranking' in filename:
            model_type = 'ranking'
        elif 'regression' in filename:
            model_type = 'regression'
        
        if not model_type:
            continue
        
        # 予測結果を読み込み
        df = pd.read_csv(csv_file)
        
        # 評価指標を計算
        if model_type == 'binary':
            # 二値分類の評価指標はCSVに含まれている想定
            # 実際には予測スクリプト側で別途保存が必要
            pass
        
        results.append({
            'venue': venue,
            'model_type': model_type,
            'data_count': len(df)
        })
    
    return pd.DataFrame(results)

def generate_report(predictions_dir, output_path):
    """
    Phase 4.5 検証レポートを生成
    
    Parameters
    ----------
    predictions_dir : str
        予測結果CSVのディレクトリ
    output_path : str
        レポート出力先（Markdown）
    """
    # 結果収集
    results_df = collect_results(predictions_dir)
    
    # Markdownレポート生成
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Phase 4.5 実データ検証レポート\n\n")
        f.write(f"**作成日**: 2026-02-07\n\n")
        f.write("---\n\n")
        
        f.write("## 📊 検証サマリー\n\n")
        f.write(f"- **検証期間**: 2026年1月1日 ~ 2026年1月31日\n")
        f.write(f"- **競馬場数**: {results_df['venue'].nunique()}\n")
        f.write(f"- **モデル数**: {len(results_df)}\n")
        f.write(f"- **総データ件数**: {results_df['data_count'].sum()}\n\n")
        
        f.write("---\n\n")
        
        # TODO: 詳細な評価指標を追加
    
    print(f"レポート生成完了: {output_path}")

if __name__ == "__main__":
    predictions_dir = 'predictions/2026_jan'
    output_path = 'docs/phase4.5_verification_report.md'
    
    generate_report(predictions_dir, output_path)
```

---

## 📅 実施スケジュール

### 2026-02-06 (Day 1)

#### 午前
- [ ] 2026年1月データの確認とSQL準備
- [ ] テストデータCSVの作成（全14競馬場）
- [ ] 予測スクリプトの実装と動作確認

#### 午後
- [ ] 一括予測実行（Phase 3 二値分類）
- [ ] 一括予測実行（Phase 4 ランキング）
- [ ] 一括予測実行（Phase 4 回帰）

### 2026-02-07 (Day 2)

#### 午前
- [ ] 予測結果の集計と分析
- [ ] 評価レポートの作成
- [ ] アンサンブル重みの最適化実験

#### 午後
- [ ] Phase 4.5 検証レポートの完成
- [ ] GitHubへのコミット・プッシュ
- [ ] Phase 5 への移行準備

---

## 🎯 成功基準

### 最低限の成功基準
- [ ] 全14競馬場で2026年1月データの予測が完了
- [ ] 各モデル（42モデル）の評価指標が算出できる
- [ ] 学習データとの精度差が明確になる

### 理想的な成功基準
- [ ] Phase 3 二値分類: AUC 0.75以上
- [ ] Phase 4 ランキング: NDCG@10 0.80以上
- [ ] Phase 4 回帰: 相対誤差 0.5%以下
- [ ] アンサンブル重みの最適値が決定できる

---

## 📈 期待される成果

### 1. モデルの実戦性能の把握

学習データと実データでの精度差を定量的に評価し、過学習の有無を確認。

### 2. モデル間の比較

3モデル（二値分類・ランキング・回帰）の強み・弱みを明確化：
- 二値分類: 入線確率の精度
- ランキング: 着順予測の精度
- 回帰: タイム予測の精度

### 3. 競馬場ごとの特性分析

どの競馬場で予測精度が高いか、低いかを把握：
- 精度が高い競馬場: 買い目生成で積極的に活用
- 精度が低い競馬場: モデル改善の優先度を上げる

### 4. アンサンブル重みの最適化

現在の重み `[0.3, 0.5, 0.2]` が最適か検証：
- Optunaを使った自動最適化の実施
- 検証データで最高精度を出す重み配分を決定

### 5. Phase 5 への準備完了

買い目生成ロジックの構築に必要な実データと知見が揃う。

---

## 🚨 リスクと対策

### リスク1: 2026年1月データが不足

**対策**: 2025年12月データも追加で検証する。

### リスク2: 予測精度が著しく低い

**対策**: 特徴量の見直し、ハイパーパラメータの再調整を検討。

### リスク3: モデルファイルが見つからない

**対策**: ファイル名の表記揺れ（monbetsu/mombetsu）に対応したスクリプトを用意済み。

---

## 📞 関連ドキュメント

- [Phase 4 完全達成レポート](phase4_final_completion_report.md)
- [Phase 4 実装ガイド](phase4_implementation_guide.md)
- [プロジェクトロードマップ](roadmap.md)

---

**作成者**: AI開発アシスタント  
**最終更新**: 2026-02-05  
**ステータス**: Phase 4.5 計画策定完了
