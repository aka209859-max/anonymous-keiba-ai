-- 2026年1月データの存在確認
-- PostgreSQLで実行してください

-- 1. 全体のデータ件数確認
SELECT 
    '全データ' as category,
    COUNT(*) as record_count,
    MIN(kaisai_nengappi) as min_date,
    MAX(kaisai_nengappi) as max_date
FROM jvd_race;

-- 2. 2026年1月のレース数を競馬場別に確認
SELECT 
    CASE keibajo_code
        WHEN '30' THEN '門別'
        WHEN '35' THEN '盛岡'
        WHEN '36' THEN '水沢'
        WHEN '42' THEN '浦和'
        WHEN '43' THEN '船橋'
        WHEN '44' THEN '大井'
        WHEN '45' THEN '川崎'
        WHEN '46' THEN '金沢'
        WHEN '47' THEN '笠松'
        WHEN '48' THEN '名古屋'
        WHEN '50' THEN '園田'
        WHEN '51' THEN '姫路'
        WHEN '54' THEN '高知'
        WHEN '55' THEN '佐賀'
        ELSE keibajo_code
    END as venue_name,
    keibajo_code,
    COUNT(DISTINCT kaisai_nengappi || TO_CHAR(race_bango, 'FM00')) as race_count,
    COUNT(*) as horse_count,
    MIN(kaisai_nengappi) as first_race_date,
    MAX(kaisai_nengappi) as last_race_date
FROM jvd_race
WHERE kaisai_nengappi >= '2026-01-01'
  AND kaisai_nengappi <= '2026-01-31'
GROUP BY keibajo_code
ORDER BY keibajo_code;

-- 3. 2026年1月の日別レース数
SELECT 
    kaisai_nengappi,
    COUNT(DISTINCT keibajo_code) as venue_count,
    COUNT(DISTINCT kaisai_nengappi || keibajo_code || TO_CHAR(race_bango, 'FM00')) as race_count,
    COUNT(*) as horse_count
FROM jvd_race
WHERE kaisai_nengappi >= '2026-01-01'
  AND kaisai_nengappi <= '2026-01-31'
GROUP BY kaisai_nengappi
ORDER BY kaisai_nengappi;

-- 4. 2026年データ全体の確認（1月以外も含む）
SELECT 
    TO_CHAR(kaisai_nengappi, 'YYYY-MM') as year_month,
    COUNT(DISTINCT keibajo_code) as venue_count,
    COUNT(DISTINCT kaisai_nengappi || keibajo_code || TO_CHAR(race_bango, 'FM00')) as race_count,
    COUNT(*) as horse_count
FROM jvd_race
WHERE kaisai_nengappi >= '2026-01-01'
  AND kaisai_nengappi <= '2026-12-31'
GROUP BY TO_CHAR(kaisai_nengappi, 'YYYY-MM')
ORDER BY year_month;
