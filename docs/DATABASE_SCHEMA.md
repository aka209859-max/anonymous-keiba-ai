# JRA AI予測システム データベーススキーマ設計書

**作成日**: 2026-02-14  
**対象**: anonymous-keiba-ai-jra プロジェクト  
**データソース**: JRA-VAN Data Lab + JRDB  
**DBMS**: PostgreSQL 14+ / SQLite 3.36+

---

## 📋 目次

1. [概要](#概要)
2. [テーブル設計方針](#テーブル設計方針)
3. [マスターテーブル](#マスターテーブル)
4. [トランザクションテーブル](#トランザクションテーブル)
5. [統合テーブル（AI学習用）](#統合テーブルai学習用)
6. [インデックス戦略](#インデックス戦略)
7. [SQL DDL](#sql-ddl)

---

## 概要

### 設計原則

1. **正規化と非正規化のバランス**
   - マスターデータ（馬、騎手、調教師）は正規化
   - 学習用テーブルは非正規化（結合コスト削減）

2. **データソース明示**
   - カラム名に `jv_` (JRA-VAN) / `jrdb_` (JRDB) プレフィックス付与
   - データの出所を明確化

3. **時系列対応**
   - 全テーブルに `created_at`, `updated_at` カラム
   - 過去データの追跡可能性

4. **AI最適化**
   - 統合テーブルは1行=1馬の1レース分
   - 特徴量生成用のウィンドウ関数に最適化

---

## テーブル設計方針

### ER図（概念レベル）

```
[馬マスター] ━━━┓
              ┃
[騎手マスター]━━━╋━━━> [統合レース結果]  →  [AI学習用View]
              ┃            ↑
[調教師マスター]━┛            ┃
                          ┃
[レースマスター] ━━━━━━━━━━┛
```

### テーブル一覧

| テーブル名 | 種別 | 用途 |
|-----------|------|------|
| `horses_master` | マスター | 馬の基本情報 |
| `jockeys_master` | マスター | 騎手の基本情報 |
| `trainers_master` | マスター | 調教師の基本情報 |
| `races_master` | マスター | レースの基本情報 |
| `race_entries` | トランザクション | 出馬表 |
| `race_results` | トランザクション | レース結果 |
| `jrdb_sed` | トランザクション | JRDB成績データ |
| `jrdb_kyi` | トランザクション | JRDB騎手・調教師データ |
| `training_records` | トランザクション | 調教データ |
| `unified_race_data` | 統合 | AI学習用統合テーブル |

---

## マスターテーブル

### 1. horses_master（馬マスター）

```sql
CREATE TABLE horses_master (
    horse_id VARCHAR(20) PRIMARY KEY,  -- 統合馬ID（JRA-VAN bloodline_id or JRDB horse_id）
    jv_bloodline_id VARCHAR(10),       -- JRA-VAN血統登録番号
    jrdb_horse_id VARCHAR(10),         -- JRDB馬ID
    horse_name VARCHAR(50) NOT NULL,   -- 馬名
    birthday DATE,                     -- 生年月日
    sex VARCHAR(1),                    -- 1=牡, 2=牝, 3=セン
    hair_color VARCHAR(2),             -- 毛色コード
    sire_id VARCHAR(20),               -- 父馬ID（外部キー）
    dam_id VARCHAR(20),                -- 母馬ID
    breeder VARCHAR(50),               -- 生産者
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sire_id) REFERENCES horses_master(horse_id),
    FOREIGN KEY (dam_id) REFERENCES horses_master(horse_id)
);

CREATE INDEX idx_horses_name ON horses_master(horse_name);
CREATE INDEX idx_horses_birthday ON horses_master(birthday);
CREATE INDEX idx_horses_sire ON horses_master(sire_id);
```

### 2. jockeys_master（騎手マスター）

```sql
CREATE TABLE jockeys_master (
    jockey_id VARCHAR(10) PRIMARY KEY,  -- 騎手コード（JRA-VAN/JRDB共通化）
    jockey_name VARCHAR(30) NOT NULL,   -- 騎手名
    license_type VARCHAR(1),            -- 1=平地, 2=障害, 3=両方
    debut_date DATE,                    -- 初騎乗日
    is_active BOOLEAN DEFAULT TRUE,     -- 現役フラグ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_jockeys_name ON jockeys_master(jockey_name);
```

### 3. trainers_master（調教師マスター）

```sql
CREATE TABLE trainers_master (
    trainer_id VARCHAR(10) PRIMARY KEY,  -- 調教師コード
    trainer_name VARCHAR(30) NOT NULL,   -- 調教師名
    training_center VARCHAR(1),          -- 1=美浦, 2=栗東
    debut_date DATE,                     -- 初免許日
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trainers_name ON trainers_master(trainer_name);
CREATE INDEX idx_trainers_center ON trainers_master(training_center);
```

---

## トランザクションテーブル

### 4. races_master（レースマスター）

```sql
CREATE TABLE races_master (
    race_id VARCHAR(20) PRIMARY KEY,    -- 統合レースID（YYYYMMDD_PP_RR）
    race_date DATE NOT NULL,            -- 開催日
    place_code VARCHAR(2) NOT NULL,     -- 競馬場コード（01-10）
    race_no INT NOT NULL,               -- レース番号
    race_name VARCHAR(100),             -- レース名
    grade VARCHAR(1),                   -- 1=G1, 2=G2, 3=G3, NULL=平場
    distance INT NOT NULL,              -- 距離（メートル）
    surface_type VARCHAR(1),            -- 1=芝, 2=ダート, 3=障害
    turn_direction VARCHAR(1),          -- 1=右, 2=左, 3=直線
    weather_code VARCHAR(2),            -- 天候コード
    track_condition VARCHAR(2),         -- 馬場状態コード
    field_size INT,                     -- 出走頭数
    prize_1st INT,                      -- 1着賞金（千円）
    prize_2nd INT,
    prize_3rd INT,
    prize_4th INT,
    prize_5th INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (race_date, place_code, race_no)
);

CREATE INDEX idx_races_date ON races_master(race_date);
CREATE INDEX idx_races_place ON races_master(place_code);
CREATE INDEX idx_races_grade ON races_master(grade);
```

### 5. race_entries（出馬表）

```sql
CREATE TABLE race_entries (
    entry_id SERIAL PRIMARY KEY,
    race_id VARCHAR(20) NOT NULL,
    horse_no INT NOT NULL,
    horse_id VARCHAR(20) NOT NULL,
    jockey_id VARCHAR(10),
    trainer_id VARCHAR(10),
    bracket_no INT,                     -- 枠番
    weight FLOAT,                       -- 斤量（kg）
    horse_weight INT,                   -- 馬体重（kg）
    horse_weight_diff INT,              -- 馬体重増減
    blinker VARCHAR(1),                 -- 1=無, 2=有
    odds_win FLOAT,                     -- 単勝オッズ
    popularity INT,                     -- 人気順
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races_master(race_id),
    FOREIGN KEY (horse_id) REFERENCES horses_master(horse_id),
    FOREIGN KEY (jockey_id) REFERENCES jockeys_master(jockey_id),
    FOREIGN KEY (trainer_id) REFERENCES trainers_master(trainer_id),
    UNIQUE (race_id, horse_no)
);

CREATE INDEX idx_entries_race ON race_entries(race_id);
CREATE INDEX idx_entries_horse ON race_entries(horse_id);
```

### 6. race_results（レース結果）

```sql
CREATE TABLE race_results (
    result_id SERIAL PRIMARY KEY,
    race_id VARCHAR(20) NOT NULL,
    horse_no INT NOT NULL,
    horse_id VARCHAR(20) NOT NULL,
    finish_order INT,                   -- 着順
    irregularity VARCHAR(1),            -- 0=正常, 1=取消, 2=除外, 3=中止
    finish_time_sec FLOAT,              -- 走破タイム（秒）
    margin FLOAT,                       -- 着差（馬身）
    last_3f_time FLOAT,                 -- 上がり3F（秒）
    corner1_position INT,               -- コーナー通過順1
    corner2_position INT,
    corner3_position INT,
    corner4_position INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races_master(race_id),
    FOREIGN KEY (horse_id) REFERENCES horses_master(horse_id),
    UNIQUE (race_id, horse_no)
);

CREATE INDEX idx_results_race ON race_results(race_id);
CREATE INDEX idx_results_horse ON race_results(horse_id);
CREATE INDEX idx_results_order ON race_results(finish_order);
```

### 7. jrdb_sed（JRDB成績データ）

```sql
CREATE TABLE jrdb_sed (
    sed_id SERIAL PRIMARY KEY,
    race_id VARCHAR(20) NOT NULL,
    horse_no INT NOT NULL,
    horse_id VARCHAR(20),
    idm INT,                            -- IDMスピード指数
    pace_idx INT,                       -- ペース指数
    track_idx INT,                      -- 馬場指数
    up_idx INT,                         -- 上がり指数
    position_idx INT,                   -- 位置取り指数
    tenkai_idx INT,                     -- 展開指数
    tenkai_mark VARCHAR(1),             -- 展開記号 A-H
    distance_suitability INT,           -- 距離適性
    surface_suitability INT,            -- 芝ダ適性
    jockey_idx INT,                     -- 騎手指数
    trainer_idx INT,                    -- 調教師指数
    stable_idx INT,                     -- 厩舎指数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races_master(race_id),
    UNIQUE (race_id, horse_no)
);

CREATE INDEX idx_jrdb_sed_race ON jrdb_sed(race_id);
CREATE INDEX idx_jrdb_sed_idm ON jrdb_sed(idm);
```

### 8. jrdb_kyi（JRDB騎手・調教師データ）

```sql
CREATE TABLE jrdb_kyi (
    kyi_id SERIAL PRIMARY KEY,
    race_id VARCHAR(20) NOT NULL,
    horse_no INT NOT NULL,
    horse_id VARCHAR(20),
    training_idx INT,                   -- 調教指数
    training_course_type VARCHAR(1),    -- 1=坂路, 2=ウッド, 等
    training_intensity VARCHAR(1),      -- 1=強め, 2=一杯
    training_time_4f FLOAT,             -- 4F調教タイム（秒）
    training_time_3f FLOAT,
    training_time_1f FLOAT,
    paddock_comment TEXT,               -- パドックコメント
    expert_comment TEXT,                -- 記者コメント
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races_master(race_id),
    UNIQUE (race_id, horse_no)
);

CREATE INDEX idx_jrdb_kyi_race ON jrdb_kyi(race_id);
```

### 9. training_records（調教データ）

```sql
CREATE TABLE training_records (
    training_id SERIAL PRIMARY KEY,
    horse_id VARCHAR(20) NOT NULL,
    training_date DATE NOT NULL,
    training_type VARCHAR(1),           -- 1=坂路, 2=ウッド, 等
    training_intensity VARCHAR(1),      -- 1=強め, 2=一杯, 3=馬なり
    time_4f FLOAT,                      -- 4Fタイム
    time_3f FLOAT,
    time_last_1f FLOAT,
    assistant_type VARCHAR(1),          -- 助手種別
    training_comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (horse_id) REFERENCES horses_master(horse_id)
);

CREATE INDEX idx_training_horse ON training_records(horse_id);
CREATE INDEX idx_training_date ON training_records(training_date);
```

---

## 統合テーブル（AI学習用）

### 10. unified_race_data（AI学習用統合テーブル）

```sql
CREATE TABLE unified_race_data (
    unified_id SERIAL PRIMARY KEY,
    
    -- レース情報
    race_id VARCHAR(20) NOT NULL,
    race_date DATE NOT NULL,
    place_code VARCHAR(2),
    race_no INT,
    race_name VARCHAR(100),
    grade VARCHAR(1),
    distance INT,
    surface_type VARCHAR(1),
    turn_direction VARCHAR(1),
    weather_code VARCHAR(2),
    track_condition VARCHAR(2),
    field_size INT,
    
    -- 馬情報
    horse_no INT NOT NULL,
    horse_id VARCHAR(20) NOT NULL,
    horse_name VARCHAR(50),
    horse_age INT,                      -- 馬齢（レース当日時点）
    sex VARCHAR(1),
    
    -- 人的情報
    jockey_id VARCHAR(10),
    jockey_name VARCHAR(30),
    trainer_id VARCHAR(10),
    trainer_name VARCHAR(30),
    
    -- 出馬表情報
    bracket_no INT,
    weight FLOAT,
    horse_weight INT,
    horse_weight_diff INT,
    blinker VARCHAR(1),
    odds_win FLOAT,
    popularity INT,
    
    -- 結果情報（正解ラベル）
    finish_order INT,
    finish_time_sec FLOAT,
    margin FLOAT,
    last_3f_time FLOAT,
    corner1_position INT,
    corner2_position INT,
    corner3_position INT,
    corner4_position INT,
    
    -- JRDB指数（特徴量）
    jrdb_idm INT,
    jrdb_pace_idx INT,
    jrdb_track_idx INT,
    jrdb_up_idx INT,
    jrdb_position_idx INT,
    jrdb_tenkai_idx INT,
    jrdb_tenkai_mark VARCHAR(1),
    jrdb_distance_suitability INT,
    jrdb_surface_suitability INT,
    jrdb_jockey_idx INT,
    jrdb_trainer_idx INT,
    jrdb_stable_idx INT,
    jrdb_training_idx INT,
    jrdb_training_time_4f FLOAT,
    jrdb_training_time_3f FLOAT,
    jrdb_training_time_1f FLOAT,
    jrdb_paddock_comment TEXT,
    jrdb_expert_comment TEXT,
    
    -- メタデータ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (race_id) REFERENCES races_master(race_id),
    FOREIGN KEY (horse_id) REFERENCES horses_master(horse_id),
    UNIQUE (race_id, horse_no)
);

CREATE INDEX idx_unified_race ON unified_race_data(race_id);
CREATE INDEX idx_unified_horse ON unified_race_data(horse_id);
CREATE INDEX idx_unified_date ON unified_race_data(race_date);
CREATE INDEX idx_unified_place ON unified_race_data(place_code);
CREATE INDEX idx_unified_finish ON unified_race_data(finish_order);
```

---

## インデックス戦略

### パフォーマンスクリティカルなクエリ

1. **馬の過去成績取得**
   ```sql
   SELECT * FROM unified_race_data
   WHERE horse_id = '2019001234'
   AND race_date < '2026-02-14'
   ORDER BY race_date DESC
   LIMIT 10;
   ```
   → `idx_unified_horse`, `idx_unified_date` が効く

2. **レース別の成績一覧**
   ```sql
   SELECT * FROM unified_race_data
   WHERE race_id = '20260214_05_11'
   ORDER BY finish_order;
   ```
   → `idx_unified_race`, `idx_unified_finish` が効く

3. **競馬場別の集計**
   ```sql
   SELECT place_code, AVG(finish_order) as avg_order
   FROM unified_race_data
   WHERE horse_id = '2019001234'
   GROUP BY place_code;
   ```
   → `idx_unified_horse`, `idx_unified_place` が効く

---

## SQL DDL

### データベース作成

```sql
-- PostgreSQL
CREATE DATABASE jra_keiba_ai
    WITH ENCODING='UTF8'
    LC_COLLATE='ja_JP.UTF-8'
    LC_CTYPE='ja_JP.UTF-8'
    TEMPLATE=template0;

-- SQLite
-- ファイル作成のみ: jra_keiba_ai.db
```

### 全テーブル作成スクリプト

上記DDLをまとめた完全版は以下のファイルに格納：
- `scripts_jra/database/create_schema.sql`

---

## パーティショニング戦略（大規模データ向け）

15年分（30,000レース、450,000出走頭数）の場合、パーティショニングを検討：

```sql
-- PostgreSQL範囲パーティショニング（年単位）
CREATE TABLE unified_race_data (
    ...
) PARTITION BY RANGE (race_date);

CREATE TABLE unified_race_data_2010 PARTITION OF unified_race_data
    FOR VALUES FROM ('2010-01-01') TO ('2011-01-01');

CREATE TABLE unified_race_data_2011 PARTITION OF unified_race_data
    FOR VALUES FROM ('2011-01-01') TO ('2012-01-01');

-- 以下2024年まで同様
```

---

## データ整合性チェック

### 統合テーブル作成後の検証SQL

```sql
-- JRA-VANデータのみ存在（JRDBなし）
SELECT COUNT(*) as jv_only
FROM unified_race_data
WHERE finish_order IS NOT NULL
AND jrdb_idm IS NULL;

-- JRDBデータのみ存在（JRA-VANなし）
SELECT COUNT(*) as jrdb_only
FROM unified_race_data
WHERE jrdb_idm IS NOT NULL
AND finish_order IS NULL;

-- 両方存在（理想的）
SELECT COUNT(*) as both_exist
FROM unified_race_data
WHERE finish_order IS NOT NULL
AND jrdb_idm IS NOT NULL;
```

---

**更新履歴**:
- 2026-02-14: 初版作成（Phase 0 データベース設計）
