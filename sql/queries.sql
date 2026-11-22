USE volleyball_db;
-- Change these four example parameters to explore other records.
SET @season_id = 101819;
SET @player_id = 848;
SET @team_a = 1002;
SET @team_b = 1016;

-- Q1: regular-season win-rate rankings, NOT official Bundesliga points standings.
WITH appearances AS (
 SELECT season_id, home_team_id AS team_id,
        (home_sets_won>away_sets_won) AS won
 FROM `Match` WHERE competition_stage='Main round'
 UNION ALL
 SELECT season_id, away_team_id, (away_sets_won>home_sets_won)
 FROM `Match` WHERE competition_stage='Main round'
), totals AS (
 SELECT st.team_id, st.season_team_name, COUNT(a.team_id) AS played,
        COALESCE(SUM(a.won),0) AS wins,
        COUNT(a.team_id)-COALESCE(SUM(a.won),0) AS losses,
        ROUND(100*AVG(a.won),2) AS win_pct
 FROM Season_Team st LEFT JOIN appearances a
 ON a.season_id=st.season_id AND a.team_id=st.team_id
 WHERE st.season_id=@season_id GROUP BY st.team_id, st.season_team_name
)
SELECT DENSE_RANK() OVER (ORDER BY win_pct DESC,wins DESC) AS team_rank,
       season_team_name,played,wins,losses,win_pct
FROM totals ORDER BY team_rank,season_team_name;

-- Q2: totals and weighted attack success for one source-resolved player, all stages.
SELECT l.league_name,s.season_name,p.player_name,
       COUNT(*) AS recorded_matches, SUM(x.total_points) AS points,
       SUM(x.attacks) AS attacks, SUM(x.attack_points) AS attack_points,
       ROUND(100*SUM(x.attack_points)/NULLIF(SUM(x.attacks),0),2) AS attack_success_pct,
       SUM(x.blocks) AS blocks,SUM(x.aces) AS aces,SUM(x.serve_errors) AS serve_errors,
       ROUND(AVG(x.total_points),2) AS points_per_recorded_match
FROM Player_Match_Stats x JOIN Player p USING(player_id)
JOIN Season s ON s.season_id=x.season_id JOIN League l USING(league_id)
WHERE x.player_id=@player_id
GROUP BY l.league_id,l.league_name,s.season_id,s.season_name,p.player_id,p.player_name
ORDER BY s.source_season_id;

-- Q3: both home/away orientations are included, all stages and all seasons.
SELECT s.season_name,m.match_date,m.competition_stage,
       h.season_team_name AS home_team,a.season_team_name AS away_team,
       CONCAT(m.home_sets_won,'-',m.away_sets_won) AS final_score,
       CASE WHEN m.home_sets_won>m.away_sets_won
            THEN h.season_team_name ELSE a.season_team_name END AS winner
FROM `Match` m JOIN Season s USING(season_id)
JOIN Season_Team h ON h.season_id=m.season_id AND h.team_id=m.home_team_id
JOIN Season_Team a ON a.season_id=m.season_id AND a.team_id=m.away_team_id
WHERE (m.home_team_id=@team_a AND m.away_team_id=@team_b)
   OR (m.home_team_id=@team_b AND m.away_team_id=@team_a)
ORDER BY m.match_date,m.match_id;

-- Q4: attack-points leaders with block and ace ranks, all stages.
WITH totals AS (
 SELECT p.player_id,p.player_name,COUNT(*) AS recorded_matches,
        SUM(x.attack_points) AS attack_points,SUM(x.blocks) AS blocks,SUM(x.aces) AS aces
 FROM Player_Match_Stats x JOIN Player p USING(player_id)
 WHERE x.season_id=@season_id GROUP BY p.player_id,p.player_name
), ranked AS (
 SELECT *,DENSE_RANK() OVER(ORDER BY attack_points DESC) AS attack_rank,
          DENSE_RANK() OVER(ORDER BY blocks DESC) AS block_rank,
          DENSE_RANK() OVER(ORDER BY aces DESC) AS ace_rank FROM totals
)
SELECT * FROM ranked ORDER BY attack_rank,player_id LIMIT 10;

-- Q5a: detailed five-set matches. Score order is always home-away.
SELECT s.season_name,m.match_date,h.season_team_name AS home_team,
       a.season_team_name AS away_team,
       GROUP_CONCAT(CONCAT(ms.home_points,'-',ms.away_points)
                    ORDER BY ms.set_number SEPARATOR ', ') AS set_scores,
       CONCAT(m.home_sets_won,'-',m.away_sets_won) AS final_score,
       CASE WHEN m.home_sets_won=3 THEN h.season_team_name ELSE a.season_team_name END AS winner
FROM `Match` m JOIN Season s USING(season_id)
JOIN Match_Set ms USING(match_id)
JOIN Season_Team h ON h.season_id=m.season_id AND h.team_id=m.home_team_id
JOIN Season_Team a ON a.season_id=m.season_id AND a.team_id=m.away_team_id
WHERE m.home_sets_won+m.away_sets_won=5
GROUP BY m.match_id,s.season_name,m.match_date,h.season_team_name,a.season_team_name,
         m.home_sets_won,m.away_sets_won
ORDER BY m.match_date,m.match_id;

-- Q5b: denominator includes every recorded match in that league-season, all stages.
SELECT l.league_name,s.season_name,COUNT(*) AS total_matches,
       SUM(m.home_sets_won+m.away_sets_won=5) AS five_set_matches,
       ROUND(100*AVG(m.home_sets_won+m.away_sets_won=5),2) AS five_set_pct
FROM `Match` m JOIN Season s USING(season_id) JOIN League l USING(league_id)
GROUP BY l.league_id,l.league_name,s.season_id,s.season_name
ORDER BY l.league_id,s.source_season_id;
