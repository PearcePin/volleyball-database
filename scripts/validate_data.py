import json
from sqlalchemy import text
from common import ROOT, engine

CHECKS={
'orphan_seasons': 'SELECT COUNT(*) FROM Season s LEFT JOIN League l USING(league_id) WHERE l.league_id IS NULL',
'orphan_season_teams': 'SELECT COUNT(*) FROM Season_Team st LEFT JOIN Season s USING(season_id) LEFT JOIN Team t USING(team_id) WHERE s.season_id IS NULL OR t.team_id IS NULL',
'orphan_rosters': 'SELECT COUNT(*) FROM Player_Team_Season p LEFT JOIN Player r USING(player_id) LEFT JOIN Season_Team st USING(season_id,team_id) WHERE r.player_id IS NULL OR st.team_id IS NULL',
'orphan_match_teams': 'SELECT COUNT(*) FROM `Match` m LEFT JOIN Season_Team h ON h.season_id=m.season_id AND h.team_id=m.home_team_id LEFT JOIN Season_Team a ON a.season_id=m.season_id AND a.team_id=m.away_team_id WHERE h.team_id IS NULL OR a.team_id IS NULL',
'orphan_sets':'SELECT COUNT(*) FROM Match_Set s LEFT JOIN `Match` m USING(match_id) WHERE m.match_id IS NULL',
'orphan_stats': 'SELECT COUNT(*) FROM Player_Match_Stats x LEFT JOIN `Match` m ON m.match_id=x.match_id AND m.season_id=x.season_id LEFT JOIN Player_Team_Season p ON p.player_id=x.player_id AND p.team_id=x.team_id AND p.season_id=x.season_id WHERE m.match_id IS NULL OR p.player_id IS NULL',
'stats_wrong_team': 'SELECT COUNT(*) FROM Player_Match_Stats x JOIN `Match` m USING(match_id) WHERE x.team_id NOT IN (m.home_team_id,m.away_team_id)',
'set_result_mismatch': '''SELECT COUNT(*) FROM (SELECT m.match_id FROM `Match` m LEFT JOIN Match_Set s USING(match_id)
 GROUP BY m.match_id,m.home_sets_won,m.away_sets_won
 HAVING COUNT(s.set_number) <> m.home_sets_won+m.away_sets_won
 OR SUM(s.home_points>s.away_points)<>m.home_sets_won OR SUM(s.away_points>s.home_points)<>m.away_sets_won
 OR MIN(s.set_number)<>1 OR MAX(s.set_number)<>COUNT(s.set_number)) bad''',
'invalid_set_score': '''SELECT COUNT(*) FROM Match_Set WHERE
 GREATEST(home_points,away_points)<IF(set_number=5,15,25)
 OR ABS(home_points-away_points)<2
 OR (GREATEST(home_points,away_points)>IF(set_number=5,15,25) AND ABS(home_points-away_points)<>2)''',
'stats_point_components': 'SELECT COUNT(*) FROM Player_Match_Stats WHERE total_points<>attack_points+blocks+aces'
}

def checks(conn):
    return {name:int(conn.execute(text(sql)).scalar_one()) for name,sql in CHECKS.items()}

def main():
    with engine().connect() as conn:
        result={'mysql_version':conn.execute(text('SELECT VERSION()')).scalar_one(),'violations':checks(conn)}
    (ROOT/'docs/validation_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    if any(result['violations'].values()):
        raise SystemExit('Validation failed. Inspect original data before changing it.')
    print('PASS: all integrity checks returned zero violations.')

if __name__=='__main__':
    main()
