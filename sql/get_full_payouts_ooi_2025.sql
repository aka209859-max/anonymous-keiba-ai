-- 大井2025年 払戻金データ完全版取得
-- すべての券種の払戻金を含む完全版

SELECT 
    -- レース識別情報
    hr.kaisai_nen,
    hr.kaisai_tsukihi,
    hr.keibajo_code,
    hr.race_bango,
    
    -- 単勝払戻
    hr.haraimodoshi_tansho_1a AS tansho_umaban,
    hr.haraimodoshi_tansho_1b AS tansho_haraimodoshi,
    hr.haraimodoshi_tansho_1c AS tansho_ninkijun,
    
    -- 複勝払戻（1～5着）
    hr.haraimodoshi_fukusho_1a AS fukusho_1_umaban,
    hr.haraimodoshi_fukusho_1b AS fukusho_1_haraimodoshi,
    hr.haraimodoshi_fukusho_2a AS fukusho_2_umaban,
    hr.haraimodoshi_fukusho_2b AS fukusho_2_haraimodoshi,
    hr.haraimodoshi_fukusho_3a AS fukusho_3_umaban,
    hr.haraimodoshi_fukusho_3b AS fukusho_3_haraimodoshi,
    hr.haraimodoshi_fukusho_4a AS fukusho_4_umaban,
    hr.haraimodoshi_fukusho_4b AS fukusho_4_haraimodoshi,
    hr.haraimodoshi_fukusho_5a AS fukusho_5_umaban,
    hr.haraimodoshi_fukusho_5b AS fukusho_5_haraimodoshi,
    
    -- 馬連払戻
    hr.haraimodoshi_umaren_1a AS umaren_kumiban,
    hr.haraimodoshi_umaren_1b AS umaren_haraimodoshi,
    hr.haraimodoshi_umaren_1c AS umaren_ninkijun,
    
    -- ワイド払戻（1～7通り）
    hr.haraimodoshi_wide_1a AS wide_1_kumiban,
    hr.haraimodoshi_wide_1b AS wide_1_haraimodoshi,
    hr.haraimodoshi_wide_2a AS wide_2_kumiban,
    hr.haraimodoshi_wide_2b AS wide_2_haraimodoshi,
    hr.haraimodoshi_wide_3a AS wide_3_kumiban,
    hr.haraimodoshi_wide_3b AS wide_3_haraimodoshi,
    hr.haraimodoshi_wide_4a AS wide_4_kumiban,
    hr.haraimodoshi_wide_4b AS wide_4_haraimodoshi,
    hr.haraimodoshi_wide_5a AS wide_5_kumiban,
    hr.haraimodoshi_wide_5b AS wide_5_haraimodoshi,
    hr.haraimodoshi_wide_6a AS wide_6_kumiban,
    hr.haraimodoshi_wide_6b AS wide_6_haraimodoshi,
    hr.haraimodoshi_wide_7a AS wide_7_kumiban,
    hr.haraimodoshi_wide_7b AS wide_7_haraimodoshi,
    
    -- 馬単払戻
    hr.haraimodoshi_umatan_1a AS umatan_kumiban,
    hr.haraimodoshi_umatan_1b AS umatan_haraimodoshi,
    hr.haraimodoshi_umatan_1c AS umatan_ninkijun,
    
    -- 三連複払戻
    hr.haraimodoshi_sanrenpuku_1a AS sanrenpuku_kumiban,
    hr.haraimodoshi_sanrenpuku_1b AS sanrenpuku_haraimodoshi,
    hr.haraimodoshi_sanrenpuku_1c AS sanrenpuku_ninkijun,
    
    -- 三連単払戻
    hr.haraimodoshi_sanrentan_1a AS sanrentan_kumiban,
    hr.haraimodoshi_sanrentan_1b AS sanrentan_haraimodoshi,
    hr.haraimodoshi_sanrentan_1c AS sanrentan_ninkijun

FROM nvd_hr hr
WHERE hr.keibajo_code = '44'      -- 大井競馬場
  AND hr.kaisai_nen = '2025'       -- 2025年
ORDER BY hr.kaisai_nen, hr.kaisai_tsukihi, hr.race_bango;
