# Phase 4 完了レポート: 3つの特化モデルとアンサンブル統合

**作成日**: 2026-02-04  
**プロジェクト**: Anonymous Keiba AI - 地方競馬特化機械学習予想システム

---

## 📊 実施概要

Phase 4 では、Phase 3 で構築した二値分類モデル（3着以内予測）を基に、3つの特化モデルを作成し、アンサンブル統合を実現しました。

### 目的
- 同じデータセットで異なる「正解」を学習する3つのモデルを構築
- 各モデルの予測を統合して最終判断を行うアンサンブルシステムの実装
- 多角的な予測による精度向上

### 期間
- 2026年2月4日（Phase 3 完了後、即日実装）

---

## ✅ 実装した3つの特化モデル

### 1. ランキング学習モデル（LightGBM Ranker）

**ファイル**: `train_ranking_model.py`

#### 目的
レース内の相対順位を学習し、「A馬はB馬より強いか？」という相対評価を行う。

#### 技術仕様
```python
params = {
    'objective': 'lambdarank',    # LambdaRankアルゴリズム
    'metric': 'ndcg',             # NDCG（Normalized Discounted Cumulative Gain）
    'ndcg_eval_at': [1, 3, 5, 10], # NDCG@1, @3, @5, @10を評価
    'boosting_type': 'gbdt'
}
```

#### 主な特徴
- **GroupShuffleSplit**: レース単位でデータ分割
- **group情報**: 各レースの出走頭数を指定
- **race_id カラム必須**: レースを一意に識別

#### train_development.py からの主な変更点
1. `objective='binary'` → `'lambdarank'`
2. `metric='auc'` → `'ndcg'`
3. データセット作成時に `group` パラメータを追加
4. Boruta特徴量選択は使用せず、二値分類で選定した特徴量リストを使用

#### 期待効果
- 上位入線確率の高い馬を順位付け
- 相対的な強さの評価
- 本命・対抗・穴馬の識別

---

### 2. 回帰分析モデル（LightGBM Regressor）

**ファイル**: `train_regression_model.py`

#### 目的
走破タイムを予測し、能力指数の代替として数値化する。

#### 技術仕様
```python
params = {
    'objective': 'regression',  # 回帰分析
    'metric': 'rmse',           # RMSE（二乗平均平方根誤差）
    'boosting_type': 'gbdt'
}
```

#### 評価指標
- **RMSE**: 二乗平均平方根誤差
- **MAE**: 平均絶対誤差
- **R²**: 決定係数
- **相対誤差**: 平均値に対する誤差の割合

#### train_development.py からの主な変更点
1. `objective='binary'` → `'regression'`
2. `metric='auc'` → `'rmse'`
3. 評価指標を回帰用に変更
4. 目的変数を「走破タイム（秒）」に変更

#### 期待効果
- 能力値の数値化
- タイム予測による穴馬の発見
- 距離適性の評価

---

### 3. アンサンブル統合

**ファイル**: `ensemble_model.py`

#### 目的
3つのモデル（二値分類・ランキング・回帰）の予測を統合し、最終的な買い目候補を決定する。

#### アンサンブル戦略

##### 1. 各予測値の正規化
```python
# 二値分類: 既に0-1の確率値
binary_norm = binary_proba

# ランキング: Min-Max正規化
ranking_norm = (ranking_score - min) / (max - min)

# 回帰: 小さい方が良いので反転してMin-Max正規化
regression_norm = 1 - ((regression_time - min) / (max - min))
```

##### 2. 加重平均で総合スコアを計算
```python
ensemble_score = (
    0.3 * binary_norm +      # 二値分類: 3着以内の確率
    0.5 * ranking_norm +     # ランキング: 相対的な強さ（重視）
    0.2 * regression_norm    # 回帰: タイム予測
)
```

##### 3. 推奨度の割り当て
```python
if binary_proba < 0.4:
    recommendation = '消去'       # 二値分類の確率が低い
elif ensemble_score >= 0.7:
    recommendation = '◎ 本命'     # 総合スコアが高い
elif ensemble_score >= 0.6:
    recommendation = '○ 対抗'
elif ensemble_score >= 0.5:
    recommendation = '▲ 単穴'
elif ensemble_score >= 0.4:
    recommendation = '△ 連下'
else:
    recommendation = '× 評価低'
```

#### 機能
- **柔軟な重み調整**: コマンドライン引数で重みを変更可能
- **閾値設定**: 二値分類の閾値を調整可能（デフォルト: 0.4）
- **詳細な出力**: 各モデルの予測値、正規化スコア、総合スコア、推奨度

#### 使用法
```bash
python ensemble_model.py <csvファイル> \
    <binary_model.txt> \
    <ranking_model.txt> \
    <regression_model.txt> \
    --binary-weight 0.3 \
    --ranking-weight 0.5 \
    --regression-weight 0.2 \
    --threshold 0.4 \
    --output ensemble_predictions.csv
```

#### 期待効果
- 各モデルの強みを組み合わせ
- 多角的な評価による精度向上
- 戦略に応じた柔軟な調整

---

## 🔬 技術仕様まとめ

### 共通技術スタック

| 項目 | 使用技術 |
|------|---------|
| **プログラミング言語** | Python 3.14 |
| **機械学習ライブラリ** | LightGBM |
| **ハイパーパラメータ最適化** | Optuna（optuna-integration） |
| **評価・可視化** | scikit-learn, matplotlib, pandas |
| **データ形式** | CSV（Shift-JIS / UTF-8自動判定） |

### モデル別の技術仕様

| モデル | Objective | Metric | 特記事項 |
|--------|-----------|--------|----------|
| **二値分類** | binary | auc | Phase 3で実装済み |
| **ランキング** | lambdarank | ndcg | group情報が必要 |
| **回帰** | regression | rmse | 連続値を予測 |
| **アンサンブル** | - | - | 3モデルの統合 |

### データ要件

#### ランキング学習モデル
- ✅ **race_id カラム**: レースを一意に識別するID（必須）
- ✅ **target カラム**: 着順（1位=1, 2位=2, ...）
- ✅ GroupShuffleSplit でレース単位にデータ分割

#### 回帰分析モデル
- ✅ **target カラム**: 走破タイム（秒）またはタイム指数
- ✅ 連続値（数値）である必要あり

#### アンサンブル統合
- ✅ 3つのモデルファイル（.txt形式）
- ✅ 予測対象データ（特徴量を含むCSV）

---

## 📈 実装の成果

### 作成ファイル一覧

| ファイル | 説明 | 行数 | 実行権限 |
|---------|------|------|---------|
| `train_ranking_model.py` | ランキング学習モデル | 377行 | ✅ |
| `train_regression_model.py` | 回帰分析モデル | 379行 | ✅ |
| `ensemble_model.py` | アンサンブル統合 | 392行 | ✅ |
| `docs/phase4_implementation_guide.md` | 実装ガイド | 320行 | - |

**合計**: 4ファイル、約1,470行のコード＋ドキュメント

### Git管理

#### コミット履歴
1. `feat(phase4): 3つの特化モデルを実装（ランキング・回帰・アンサンブル）`
   - 3 files changed, 928 insertions(+)
   
2. `docs: Phase 4実装ガイドとセッションログを追加`
   - 2 files changed, 324 insertions(+)

#### ブランチ
- **ブランチ名**: `phase4_specialized_models`
- **分岐元**: `main`（Phase 3 マージ後）
- **状態**: GitHub にプッシュ済み

---

## 📚 ドキュメント整備

### Phase 4 実装ガイド

`docs/phase4_implementation_guide.md` を作成し、以下の内容を記載：

1. **各モデルの目的と特徴**
2. **使用法とコマンド例**
3. **データ準備の注意点**
4. **実行フロー（全体像）**
5. **トラブルシューティング**
6. **期待される効果**

### セッションログ更新

`docs/session_log.md` を更新し、Phase 4 の作業履歴を記録。

---

## 🎯 Phase 4 で実現したこと

### 1. 多角的な予測の実現

| モデル | 得意な予測 | アプローチ |
|--------|-----------|-----------|
| **二値分類** | 3着以内か否か | 絶対評価（確率） |
| **ランキング** | 相対的な強さ | 相対評価（順位） |
| **回帰** | 走破タイム | 数値化（能力） |

### 2. アンサンブルによる精度向上

- 各モデルの強みを組み合わせ
- 弱点を補完
- 柔軟な戦略調整

### 3. 実用的な推奨システム

- ◎本命 / ○対抗 / ▲単穴 / △連下 / ×評価低 / 消去
- 買い目の優先順位を明確化
- 実戦投入可能な形式

---

## 🚧 今後の課題と改善点

### 1. データ準備の効率化

**現状**: 各モデルで異なるデータ形式が必要
- ランキング: race_id が必要
- 回帰: target をタイムに変更

**改善案**:
- データ抽出スクリプトの拡張
- 複数形式の一括出力機能

### 2. 実データでのテスト

**現状**: 実装完了、テスト未実施

**必要な作業**:
1. 14競馬場のデータでランキング学習を実行
2. 回帰分析モデルの学習
3. アンサンブル予測の実行
4. 精度評価

### 3. ハイパーパラメータの最適化

**現状**: デフォルト重み（二値0.3 / ランキング0.5 / 回帰0.2）

**改善案**:
- 実データで最適な重みを探索
- 競馬場ごとに重みを調整
- Optunaでアンサンブル重みも最適化

---

## 🎊 Phase 5 への展望

Phase 4 で構築したアンサンブルシステムを基に、以下の発展が可能：

### 1. 実戦投入
- 当日レースでの予測実行
- 買い目の自動生成
- 的中率・回収率の検証

### 2. モデルの精緻化
- 特徴量エンジニアリングの追加
- 競馬場ごとのアンサンブル重み最適化
- 時系列クロスバリデーション

### 3. システム化
- Web UIの構築
- 自動予測システム
- リアルタイム予測

---

## 🏆 結論

Phase 4 では、**3つの特化モデルとアンサンブル統合**を実装し、多角的な予測システムを構築することに成功しました。

### 主な成果

1. ✅ ランキング学習モデルの実装（LambdaRank）
2. ✅ 回帰分析モデルの実装（走破タイム予測）
3. ✅ アンサンブル統合の実装（3モデルの統合）
4. ✅ 実装ガイドの作成（使用法・注意点を網羅）
5. ✅ Git管理の完了（コミット・プッシュ済み）

### 技術的な達成
- LightGBMの3つの異なるobjectiveを活用
- Optunaによる自動最適化を各モデルで実現
- 柔軟なアンサンブル戦略の実装

### 次のステップ
- 実データでのテスト実行（ユーザー側）
- Phase 4 PRのマージ
- Phase 5 の検討開始

---

**Phase 4 完了日**: 2026年2月4日  
**次のフェーズ**: Phase 5 - 実戦投入とシステム化

---

## 📚 参考ドキュメント

- [Phase 1 完了レポート](phase1_completion_report.md)
- [Phase 2 完了レポート](phase2_completion_report.md)
- [Phase 3 完了レポート](phase3_completion_report.md)
- [Phase 4 実装ガイド](phase4_implementation_guide.md)
- [開発ロードマップ](../docs/roadmap.md)
- [プロンプト集](../docs/prompts.md)

---

**作成者**: Anonymous Keiba AI Development Team  
**ライセンス**: MIT
