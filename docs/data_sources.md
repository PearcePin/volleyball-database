# 資料來源與清理紀錄

## 來源與取得方式

- 主要來源：[bozhinvi/volleystat](https://github.com/bozhinvi/volleystat)。作者 Viktor Bozhinov；套件版本 0.2.0。
- 固定版本：`c38586571a6f0d3cc3f42ebb457410020eb8898b`，避免來源日後變動造成結果不同。
- 取得日期：2026-11-22（台灣時間）。上游 README、DESCRIPTION 與欄位文件均已保存在 `data/raw/source_*`。
- 上游 DESCRIPTION 宣告 **CC0**。這是上游對套件的授權聲明，不代表本專題另外調查或保證所有原始網站權利。
- 上游說明資料由德國 Volleyball Bundesliga 官網的公開 PDF 比賽報告與名冊整理而來。沒有重新抓取官網，也沒有另外補造資料。
- [上游欄位定義](https://github.com/bozhinvi/volleystat/blob/c38586571a6f0d3cc3f42ebb457410020eb8898b/R/data.R)、[上游授權聲明](https://github.com/bozhinvi/volleystat/blob/c38586571a6f0d3cc3f42ebb457410020eb8898b/DESCRIPTION)。
- 原始倉庫沒有這四張表的直接 CSV，因此下載 `data/players.rda`、`matches.rda`、`sets.rda`、`matchstats.rda`，使用 Python `rdata` 正確解讀後匯出 CSV。不需要安裝 R。
- R `Date` 是距 1970-01-01 的天數；R `POSIXct` 是 Unix 秒數。生日轉成日期，比賽時間由 UTC 轉為 **Europe/Berlin 當地時間**，含夏令時間處理，存入 DATETIME。不能直接把數字當成 YYYYMMDD。
- 每份 RDA 的來源 URL、SHA-256、原始欄位及列數見 `data/raw/manifest.json`。
- 備用來源 [volleydata](https://github.com/awosoga/volleydata) 與 [rvolleydata](https://github.com/awosoga/rvolleydata) 未使用，因主要來源足以支援全部查詢。沒有混合不同賽事的統計。

## 實際涵蓋內容

男女 Bundesliga 各包含 2013–2014、2014–2015、2015–2016、2016–2017、2017–2018、2018–2019 六季，合計 12 個聯賽賽季。下面是來源快照中的比賽數，並非宣稱已獨立核對官網所有賽事均完整。

| 賽季 | 男子場數 | 女子場數 |
|---|---:|---:|
| 2013–2014 | 113 | 134 |
| 2014–2015 | 134 | 154 |
| 2015–2016 | 130 | 179 |
| 2016–2017 | 135 | 154 |
| 2017–2018 | 130 | 126 |
| 2018–2019 | 155 | 152 |

原始名冊 1,853 列不是 1,853 個不同的人，而是「球員在某季某隊」的名冊紀錄。保守識別後有 940 個球員身分、32 個來源球隊 ID、137 個球隊賽季。姓名可能有上游拼字或字元損壞，原始名稱會保留。

## 清理決策

1. 比賽有主、客兩列，合併成一場；3,392 列變成 1,696 場。每局也有主、客兩列，12,660 列變成 6,330 局。合併使用聯賽、賽季、來源比賽 ID，局數再加上 set。
2. `matchstats` 的 4 筆完全重複列只保留第一筆，移除的副本存在 `duplicate_stats.csv`。不任意挑選互相矛盾的紀錄；若同一主鍵仍重複，程式停止。
3. 268 筆統計無法以「聯賽＋賽季＋球隊 ID＋來源球員 ID」對應名冊，放入 `quarantine_stats.csv`，註明原因，不製造假姓名或跨季套用球衣號碼。
4. 32,755 − 4 − 268 = **32,483** 筆統計匯入。因此球員排行榜與總分是「可識別且有紀錄的統計」，可能低估完整真實生涯數據。比賽勝負與五局比例不受這些隔離統計影響。
5. 名冊 2 筆缺來源球員 ID 與球衣號碼，保留 NULL，不補成 0。這兩人仍保留在球員及名冊資料表。
6. `vote` 有 12,764 筆缺值；`match_day` 有 524 筆缺值；`match_duration` 有 18 筆缺值；`set_duration` 有 66 筆缺值。這些欄位不支援本專題必要查詢，沒有納入分析 schema，但完整留在 raw CSV。
7. 球員身分使用 Unicode NFKC、去前後空白、連續空白合併與大小寫正規化後的「性別＋名＋姓＋生日」。採代理 ID；跨季或轉隊時相同身分沿用同一 ID。球衣號碼不能當全球 ID。
8. 不用「生日相同」就合併，因名冊包含同日出生、不同姓名的球員，甚至雙胞胎。`identity_review.csv` 保留人工檢查候選；`player_identity_map.csv` 提供每筆來源名冊的對照。沒有足夠證據的改姓或不同拼字保持分開，所以 940 是來源解析身分數，並非外部權威認證人數。
9. 球隊依上游保證跨季穩定的 team_id 識別，Team 使用最新名冊名稱作顯示名稱；Season_Team 保存當季名稱。贊助更名不會變成新球隊；男女 VCO Berlin 的來源 ID 不同，不會誤合併。完整別名見 `team_aliases.csv`。
10. 位置存於 Player_Team_Season，因球員不同賽季可能換位置。沒有把位置硬塞成永遠不變的 Player 屬性。

## 驗證與限制

外鍵由 InnoDB 強制執行。匯入在單一資料交易內完成，失敗回滾；DDL 是 MySQL 的隱含提交，與資料交易分開。使用 upsert，因此同一固定快照重跑不會增加列數；這不是任意不同來源快照的同步刪除工具。

每場局數、局號連續性、局勝場、最終比分、每局最低得分及兩分差、球員所屬賽季、是否為出賽球隊、得分組成均由驗證程式檢查。跨列規則不假裝能用一般 CHECK 完成。手動修改資料後應重新驗證。

核心實體與關聯接近 3NF。`Player_Match_Stats.season_id` 可由 match_id 推得，刻意保留以建立兩組複合外鍵，屬於**受外鍵約束的少量冗餘**，不是聲稱整份 schema 嚴格全部符合 3NF。姓名標準化 key 是解析用的候選鍵，姓名與生日仍屬來源資料，不能保證現實世界絕對唯一。

查詢 1 僅分析 Main round，以勝率及勝場排名，並列採 DENSE_RANK；**不是官方德甲積分榜**。查詢 2–5 包含來源中的所有階段（Main round、Pre-Playoff、Quarterfinal、Semifinal、Finale、Playdown）。
