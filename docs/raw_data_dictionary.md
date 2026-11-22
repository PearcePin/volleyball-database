# 原始資料完整欄位字典

依固定版本上游 R/data.R 與實際 RDA/CSV 核對。下列是全部原始欄位，並非每個欄位都匯入分析 schema；未匯入欄位仍保留在 raw CSV。

缺值與重複數見 data/processed/quality_report.json。

## players：1,853 列，13 欄

| 欄位 | 意義 | 缺值數 |
|---|---|---:|
| season_id | 來源四位季別，例如 1314＝2013/2014；只在聯賽內唯一 | 0 |
| league_gender | Men / Women，男子或女子聯賽 | 0 |
| team_id | 來源跨賽季穩定球隊識別 | 0 |
| team_name | 來源球隊顯示名稱，可能隨贊助更名 | 0 |
| lastname | 姓 | 0 |
| firstname | 名 | 0 |
| height | 身高（公分） | 0 |
| gender | 球員性別 male / female | 0 |
| birthdate | 出生日期；R Date 原為距 Unix epoch 天數，CSV 已轉 YYYY-MM-DD | 0 |
| shirt_number | 球衣號碼，可缺失，不一定在隊內唯一 | 2 |
| position | 當季專長位置 | 0 |
| nationality | 來源國籍文字 | 0 |
| player_id | 來源球員編號，只在某季某隊唯一，不是全球球員 ID | 2 |

## matches：3,392 列，12 欄

| 欄位 | 意義 | 缺值數 |
|---|---|---:|
| league_gender | Men / Women，男子或女子聯賽 | 0 |
| season_id | 來源四位季別，例如 1314＝2013/2014；只在聯賽內唯一 | 0 |
| competition_stage | 賽事階段（例行賽或各階段季後賽） | 0 |
| match_id | 來源比賽編號，必須連同聯賽及賽季識別 | 0 |
| match | home / away；這列從主隊或客隊角度記錄 | 0 |
| match_day | 例行賽輪次；非例行賽可缺值 | 524 |
| date_time | R POSIXct 秒數；CSV 已轉德國 Europe/Berlin 當地日期時間 | 0 |
| spectators | 現場觀眾數 | 0 |
| match_duration | 比賽時間（分鐘） | 18 |
| team_id | 來源跨賽季穩定球隊識別 | 0 |
| team_name | 來源球隊顯示名稱，可能隨贊助更名 | 0 |
| set_won | 該隊贏的局數 | 0 |

## sets：12,660 列，9 欄

| 欄位 | 意義 | 缺值數 |
|---|---|---:|
| league_gender | Men / Women，男子或女子聯賽 | 0 |
| season_id | 來源四位季別，例如 1314＝2013/2014；只在聯賽內唯一 | 0 |
| match_id | 來源比賽編號，必須連同聯賽及賽季識別 | 0 |
| match | home / away；這列從主隊或客隊角度記錄 | 0 |
| team_id | 來源跨賽季穩定球隊識別 | 0 |
| team_name | 來源球隊顯示名稱，可能隨贊助更名 | 0 |
| set | 第幾局 | 0 |
| set_duration | 該局時間（分鐘） | 66 |
| pt_set | 該隊該局得分 | 0 |

## matchstats：32,755 列，23 欄

| 欄位 | 意義 | 缺值數 |
|---|---|---:|
| league_gender | Men / Women，男子或女子聯賽 | 0 |
| season_id | 來源四位季別，例如 1314＝2013/2014；只在聯賽內唯一 | 0 |
| match_id | 來源比賽編號，必須連同聯賽及賽季識別 | 0 |
| team_id | 來源跨賽季穩定球隊識別 | 0 |
| player_id | 來源球員編號，只在某季某隊唯一，不是全球球員 ID | 0 |
| shirt_number | 球衣號碼，可缺失，不一定在隊內唯一 | 0 |
| vote | DataVolley 設定計算的評分，來源未提供數字時為缺值 | 12764 |
| pt_tot | 總得分（攻擊得分＋攔網得分＋Ace） | 0 |
| pt_bp | Break points 得分 | 0 |
| pt_profloss | 得失分差：serv_pt＋att_pt＋blo_pt－serv_err－rec_err－att_err－att_blo，可為負數 | 0 |
| serv_tot | 發球次數 | 0 |
| serv_err | 發球失誤次數；上游 R 文件誤拼為 ser_err，實際欄位為 serv_err | 0 |
| serv_pt | 發球直接得分（Ace） | 0 |
| rec_tot | 接發球次數 | 0 |
| rec_err | 接發球失誤次數 | 0 |
| rec_pos | 正向接發球百分比，來源以 0–100 記錄 | 0 |
| rec_per | 完美接發球百分比，來源以 0–100 記錄 | 0 |
| att_tot | 攻擊嘗試次數 | 0 |
| att_err | 攻擊失誤次數 | 0 |
| att_blo | 攻擊被攔死次數 | 0 |
| att_pt | 攻擊得分次數 | 0 |
| att_per | 攻擊成功百分比，來源以 0–100 記錄 | 0 |
| blo_pt | 攔網得分次數 | 0 |

## 匯入欄位對照

matchstats.pt_tot → total_points；att_tot → attacks；att_pt → attack_points；blo_pt → blocks；serv_pt → aces；serv_err → serve_errors；serv_tot → serves。

matches 的 home、away 列合併成 Match；sets 的 pt_set 合併成 home_points、away_points。來源 player_id 另存為 source_player_id，來源 match_id 另存為 source_match_id；新 player_id 與 match_id 是專題內部的代理鍵。
