# PC-KEIBA データ抽出SQL設計書

## 概要
PC-KEIBA Databaseから地方競馬の学習データを抽出するSQLクエリの設計書です。

## データ抽出の基本方針

### 目的変数
- **target**: 3着以内なら `1`、それ以外は `0`

### 説明変数の分類

#### 1. レース情報（nvd_ra）
- 開催年月日（kaisai_nen, kaisai_tsukihi）
- 競馬場コード（keibajo_code）
- レース番号（race_bango）
- 距離（kyori）
- トラックコード（track_code）
- 馬場状態コード（baba_jotai_code）
- 天候コード（tenkou_code）
- 頭数（tosu）
- グレード（grade_code）

#### 2. 出馬情報（nvd_se）
- 馬番（umaban）
- 枠番（wakuban）
- 性別コード（seibetsu_code）
- 年齢（barei）
- 負担重量（futan_juryo）
- 騎手コード（kishu_code）
- 調教師コード（chokyoshi_code）
- ブリンカー（blinker）
- 所属（zokusho）
- **着順（chakujun）** ← 目的変数の元データ

#### 3. 馬情報（nvd_um）
- 毛色コード（keiro_code）
- 種牡馬コード（sire_code）
- 母父馬コード（broodmare_sire_code）

#### 4. 過去走データ
- 前走1〜5走前のデータ
  - 着順（zensou1_chakujun, zensou2_chakujun, ...）
  - タイム差（zensou1_time_sa, zensou2_time_sa, ...）
  - 上がり3F（zensou1_agari_3f, zensou2_agari_3f, ...）
  - 通過順位（zensou1_tsukarei, zensou2_tsukarei, ...）
  - 距離（zensou1_kyori, zensou2_kyori, ...）
  - 競馬場コード（zensou1_keibajo, zensou2_keibajo, ...）
  - 馬場状態（zensou1_baba, zensou2_baba, ...）
  - 前走馬体重（zensou1_bataiju, zensou2_bataiju, ...）

### 除外項目（絶対に含めない）
- ❌ **tansho_ninki**: 単勝人気
- ❌ **tansho_odds**: 単勝オッズ
- ❌ **bataiju**: 当日馬体重
- ❌ **zougen**: 馬体重増減
- ❌ **fukusho_ninki**: 複勝人気
- ❌ **fukusho_odds**: 複勝オッズ

### フィルタリング条件
- **地方競馬のみ**: keibajo_code IN (30, 33, 35, 36, 42, 43, 44, 45, 46, 47, 48, 50, 51, 54, 55)
- **平地レースのみ**: track_code != '障害' （具体的なコード値は要確認）
- **除外: 取消・除外馬**: chakujun NOT IN ('取消', '除外', '中止') OR chakujun IS NOT NULL

## SQLクエリテンプレート（基本版）

```sql
-- 地方競馬 学習データ抽出クエリ（基本版）
SELECT 
    -- 目的変数
    CASE 
        WHEN se.chakujun::INTEGER <= 3 THEN 1
        ELSE 0
    END AS target,
    
    -- レースID（識別用、学習には使わない）
    ra.kaisai_nen || '-' || ra.kaisai_tsukihi || '-' || 
    ra.keibajo_code || '-' || ra.race_bango AS race_id,
    
    -- 馬ID（識別用、学習には使わない）
    se.uma_code AS uma_id,
    
    -- === レース情報 ===
    ra.kaisai_nen,
    ra.kaisai_tsukihi,
    ra.keibajo_code,
    ra.race_bango,
    ra.kyori,
    ra.track_code,
    ra.baba_jotai_code,
    ra.tenkou_code,
    ra.tosu,
    ra.grade_code,
    
    -- === 出馬情報 ===
    se.umaban,
    se.wakuban,
    se.seibetsu_code,
    se.barei,
    se.futan_juryo,
    se.kishu_code,
    se.chokyoshi_code,
    se.blinker,
    se.zokusho,
    
    -- === 馬情報 ===
    um.keiro_code,
    um.sire_code,
    um.broodmare_sire_code,
    
    -- === 過去走データ（前走1） ===
    se.zensou1_chakujun,
    se.zensou1_time_sa,
    se.zensou1_agari_3f,
    se.zensou1_tsukarei,
    se.zensou1_kyori,
    se.zensou1_keibajo,
    se.zensou1_baba,
    se.zensou1_bataiju,
    
    -- === 過去走データ（前走2） ===
    se.zensou2_chakujun,
    se.zensou2_time_sa,
    se.zensou2_agari_3f,
    se.zensou2_tsukarei,
    se.zensou2_kyori,
    se.zensou2_keibajo,
    se.zensou2_baba,
    se.zensou2_bataiju,
    
    -- === 過去走データ（前走3） ===
    se.zensou3_chakujun,
    se.zensou3_time_sa,
    se.zensou3_agari_3f,
    se.zensou3_tsukarei,
    se.zensou3_kyori,
    se.zensou3_keibajo,
    se.zensou3_baba,
    se.zensou3_bataiju,
    
    -- === 過去走データ（前走4） ===
    se.zensou4_chakujun,
    se.zensou4_time_sa,
    se.zensou4_agari_3f,
    se.zensou4_tsukarei,
    se.zensou4_kyori,
    se.zensou4_keibajo,
    se.zensou4_baba,
    se.zensou4_bataiju,
    
    -- === 過去走データ（前走5） ===
    se.zensou5_chakujun,
    se.zensou5_time_sa,
    se.zensou5_agari_3f,
    se.zensou5_tsukarei,
    se.zensou5_kyori,
    se.zensou5_keibajo,
    se.zensou5_baba,
    se.zensou5_bataiju

FROM 
    nvd_ra ra
    INNER JOIN nvd_se se ON (
        ra.kaisai_nen = se.kaisai_nen 
        AND ra.kaisai_tsukihi = se.kaisai_tsukihi
        AND ra.keibajo_code = se.keibajo_code
        AND ra.race_bango = se.race_bango
    )
    LEFT JOIN nvd_um um ON (
        se.uma_code = um.uma_code
    )

WHERE 
    -- 地方競馬のみ
    ra.keibajo_code IN ('30', '33', '35', '36', '42', '43', '44', '45', '46', '47', '48', '50', '51', '54', '55')
    
    -- 着順が確定している（取消・除外を除く）
    AND se.chakujun IS NOT NULL
    AND se.chakujun NOT IN ('取消', '除外', '中止', '失格')
    AND se.chakujun ~ '^[0-9]+$'  -- 数字のみ
    
    -- 平地レースのみ（障害除外）
    -- AND ra.track_code NOT IN ('障害コード')  -- 実際のコード値で要確認
    
ORDER BY 
    ra.kaisai_nen DESC,
    ra.kaisai_tsukihi DESC,
    ra.keibajo_code,
    ra.race_bango,
    se.umaban;
```

## 拡張版: 騎手・調教師統計を含む

上記の基本版に加えて、以下の集計データを追加できます：

### 騎手統計
- 直近30日の勝率
- 直近30日の連対率
- 直近30日の複勝率
- 該当競馬場での勝率

### 調教師統計
- 直近30日の勝率
- 直近30日の連対率
- 該当競馬場での勝率

### 血統統計
- 種牡馬の勝率
- 母父馬の勝率

これらの統計は、サブクエリやWITH句を使って計算します。

## データ抽出の注意点

### 1. カラム名の確認
PC-KEIBAの実際のテーブル定義を確認し、カラム名を正確に指定する必要があります。

### 2. データ型の確認
- 数値として扱うべきカラムが文字列型の場合、`::INTEGER` や `::NUMERIC` でキャストする
- NULL値の扱いを適切に処理する

### 3. パフォーマンス
- 大量データの場合、WHERE句で期間を限定する（例: 直近2年分）
- インデックスが適切に設定されているか確認する

### 4. テストデータでの確認
- 最初は小規模データ（1競馬場、1ヶ月分）で実行してエラーがないか確認
- 出力CSVのカラム数、レコード数、NULL値の割合を確認

## 次のステップ

1. 実際のPC-KEIBAデータベースでカラム名を確認
2. SQLクエリを実行して動作確認
3. CSV出力用のPythonスクリプトを作成
4. 特徴量エンジニアリング（統計量の追加）を実装
