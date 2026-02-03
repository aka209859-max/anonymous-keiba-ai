# PC-KEIBA環境情報

## インストールパス
- **PC-KEIBA**: \C:\Users\ihaji\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\pc-keiba.com\
- **作業ディレクトリ**: \E:\anonymous-keiba-ai\

## データベース接続情報
- **サーバー名**: 127.0.0.1
- **ポート番号**: 5432
- **データベース名**: pckeiba
- **ユーザー名**: postgres
- **パスワード**: postgres123

## 競馬場コード（正式版）

| コード | 競馬場名 |
|--------|----------|
| 30 | 門別 |
| 33 | 帯広 |
| 35 | 盛岡 |
| 36 | 水沢 |
| 42 | 浦和 |
| 43 | 船橋 |
| 44 | 大井 |
| 45 | 川崎 |
| 46 | 金沢 |
| 47 | 笠松 |
| 48 | 名古屋 |
| 50 | 園田 |
| 51 | 姫路 |
| 54 | 高知 |
| 55 | 佐賀 |

## 主要テーブル
- **nvd_ra**: レース情報 (80,415件)
- **nvd_se**: 出馬表 (1,036,822件)
- **nvd_um**: 馬情報 (118,336件)
- **nvd_kj**: 騎手情報 (9,416件)
- **nvd_ch**: 調教師情報 (4,168件)

## 重要カラム
- **kaisai_nen**: 開催年
- **kaisai_tsukihi**: 開催月日 (MMDD形式)
- **keibajo_code**: 競馬場コード
- **race_bango**: レース番号
- **kyori**: 距離
- **track_code**: トラックコード

## 除外すべきカラム（当日変動要素）
- **tansho_ninki**: 単勝人気
- **tansho_odds**: 単勝オッズ
- **bataiju**: 当日馬体重
- **zougen**: 馬体重増減

## 使用可能カラム（前日まで確定）
- **zensou_bataiju**: 前走馬体重
- **kishu_code**: 騎手コード
- **chokyoshi_code**: 調教師コード
- **umaban**: 馬番
- **wakuban**: 枠番
