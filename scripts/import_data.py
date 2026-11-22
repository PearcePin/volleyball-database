"""Prepare auditable CSVs and import atomically with idempotent upserts."""
import argparse
import json
import unicodedata
import pandas as pd
from sqlalchemy import MetaData, Table, text
from sqlalchemy.dialects.mysql import insert
from common import ROOT, engine, statements

def normalized(value):
    return ' '.join(unicodedata.normalize('NFKC', str(value)).split()).casefold()

def prepare():
    raw, out = ROOT / 'data/raw', ROOT / 'data/processed'
    out.mkdir(parents=True, exist_ok=True)
    p, m, s, x = [pd.read_csv(raw / f'{n}.csv') for n in ['players','matches','sets','matchstats']]
    report = {'raw_rows': dict(zip(['players','matches','sets','matchstats'], map(len,[p,m,s,x]))),
              'missing_values': {n: d.isna().sum().to_dict() for n,d in zip(['players','matches','sets','matchstats'],[p,m,s,x])}}
    p['player_name'] = (p.firstname.str.strip() + ' ' + p.lastname.str.strip()).str.replace(r'\s+', ' ', regex=True)
    p['identity_key'] = p.apply(lambda r: '|'.join([normalized(r.gender), normalized(r.firstname), normalized(r.lastname),r.birthdate]),axis=1)
    ids = {key:i+1 for i,key in enumerate(sorted(p.identity_key.unique()))}
    p['new_player_id'] = p.identity_key.map(ids)
    p['new_season_id'] = p.season_id + p.league_gender.map({'Men':100000,'Women':200000})
    m['new_season_id'] = m.season_id + m.league_gender.map({'Men':100000,'Women':200000})
    season_rows = m[['new_season_id','league_gender','season_id']].drop_duplicates().sort_values('new_season_id')
    seasons = pd.DataFrame({'season_id':season_rows.new_season_id, 'league_id':season_rows.league_gender.map({'Men':1,'Women':2}), 'source_season_id':season_rows.season_id,
        'season_name':season_rows.season_id.map(lambda v:f'20{str(v)[:2]}–20{str(v)[2:]}')})
    league = pd.DataFrame([(1,'German Bundesliga Men','Germany'),(2,'German Bundesliga Women','Germany')],columns=['league_id','league_name','country'])
    # Stable source team IDs preserve sponsorship name changes and separate VCO genders.
    team = p.sort_values('season_id').drop_duplicates('team_id',keep='last')[['team_id','team_name']].sort_values('team_id')
    st = p[['new_season_id','team_id','team_name']].drop_duplicates().rename(columns={'new_season_id':'season_id','team_name':'season_team_name'})
    assert not st.duplicated(['season_id','team_id']).any(), 'Conflicting seasonal team names'
    player = p.sort_values(['season_id','team_id']).drop_duplicates('new_player_id',keep='last')[['new_player_id','identity_key','player_name','gender','birthdate']].rename(columns={'new_player_id':'player_id'}).sort_values('player_id')
    pts = p[['new_player_id','team_id','new_season_id','player_id','shirt_number','position']].rename(columns={'new_player_id':'player_id','new_season_id':'season_id','player_id':'source_player_id'})
    assert not pts.duplicated(['player_id','team_id','season_id']).any()
    # Same birthday with different names is an audit candidate, never an automatic merge.
    candidates = p[p.duplicated(['gender','birthdate'],False)].sort_values(['gender','birthdate','player_name'])
    candidates.to_csv(out/'identity_review.csv',index=False)
    p[['league_gender','season_id','team_id','player_id','new_player_id','player_name','birthdate','identity_key']].to_csv(out/'player_identity_map.csv',index=False)
    p[['league_gender','season_id','team_id','team_name']].drop_duplicates().to_csv(out/'team_aliases.csv',index=False)
    key = ['league_gender','season_id','match_id']
    h, a = m[m.match=='home'].copy(),m[m.match=='away'].copy()
    assert not m.duplicated(key+['match']).any()
    both = h.merge(a,on=key,suffixes=('_h','_a'),validate='one_to_one').sort_values(key).reset_index(drop=True)
    assert len(both)*2==len(m)
    match = pd.DataFrame({'match_id':range(1,len(both)+1),'season_id':both.new_season_id_h,'source_match_id':both.match_id,
       'home_team_id':both.team_id_h,'away_team_id':both.team_id_a,'match_date':both.date_time_h,
       'competition_stage':both.competition_stage_h,'home_sets_won':both.set_won_h,'away_sets_won':both.set_won_a})
    mapping = both[key].copy(); mapping['new_match_id']=match.match_id; mapping['new_season_id']=match.season_id
    sh = s[s.match=='home'].merge(s[s.match=='away'],on=key+['set'],suffixes=('_h','_a'),validate='one_to_one')
    assert len(sh)*2==len(s)
    sh=sh.merge(mapping,on=key,validate='many_to_one')
    ms = sh[['new_match_id','set','pt_set_h','pt_set_a']].rename(columns={'new_match_id':'match_id','set':'set_number','pt_set_h':'home_points','pt_set_a':'away_points'})
    duplicate = x.duplicated()
    x[duplicate].to_csv(out/'duplicate_stats.csv',index=False)
    report['exact_duplicate_stats_removed']=int(duplicate.sum())
    x=x[~duplicate].copy()
    pk=['league_gender','season_id','team_id','player_id']
    joined=x.merge(p[pk+['new_player_id']],on=pk,how='left',validate='many_to_one',indicator=True)
    unmatched=joined[joined._merge=='left_only'].copy()
    unmatched['reason']='No matching roster identity in source players table'
    unmatched.to_csv(out/'quarantine_stats.csv',index=False)
    good=joined[joined._merge=='both'].merge(mapping,on=key,validate='many_to_one')
    stat=good[['new_match_id','new_player_id','team_id','new_season_id','pt_tot','att_tot','att_pt','blo_pt','serv_pt','serv_err','serv_tot']].rename(columns={
        'new_match_id':'match_id','new_player_id':'player_id','new_season_id':'season_id','pt_tot':'total_points','att_tot':'attacks','att_pt':'attack_points','blo_pt':'blocks','serv_pt':'aces','serv_err':'serve_errors','serv_tot':'serves'})
    assert not stat.duplicated(['match_id','player_id','team_id']).any()
    tables={'League':league,'Season':seasons,'Team':team,'Player':player,'Season_Team':st,'Player_Team_Season':pts,'Match':match,'Match_Set':ms,'Player_Match_Stats':stat}
    report['quarantined_stats']=len(unmatched)
    report['table_rows']={n:len(d) for n,d in tables.items()}
    report['policy']='No invented records. Identity = normalized gender + first/last name + birthdate. Name changes remain separate unless reviewed. Missing stats are not zeros.'
    for n,d in tables.items():
        d.to_csv(out/f'{n}.csv',index=False)
    (out/'quality_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,default=int),encoding='utf-8')
    return tables

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--prepare-only',action='store_true'); args=parser.parse_args()
    tables=prepare()
    if args.prepare_only:
        print({n:len(d) for n,d in tables.items()}); return
    server=engine(False)
    # MySQL DDL commits implicitly. Schema creation precedes the data transaction.
    with server.connect() as conn:
        for sql in statements(ROOT/'sql/schema.sql'):
            conn.exec_driver_sql(sql)
        conn.commit()
    db=engine()
    with db.begin() as conn:
        for name,df in tables.items():
            table=Table(name,MetaData(),autoload_with=conn)
            for start in range(0,len(df),500):
                records=df.iloc[start:start+500].astype(object).where(pd.notna(df.iloc[start:start+500]),None).to_dict('records')
                stmt=insert(table).values(records)
                conn.execute(stmt.on_duplicate_key_update(**{c.name:stmt.inserted[c.name] for c in table.columns if not c.primary_key}))
        from validate_data import checks
        findings=checks(conn)
        if any(findings.values()):
            raise ValueError(f'Validation failed, rolling back: {findings}')
    counts={}
    with db.connect() as conn:
        for n in tables:
            counts[n]=conn.execute(text(f'SELECT COUNT(*) FROM `{n}`')).scalar_one()
            print(f'{n}: {counts[n]:,}')
    (ROOT/'docs/import_counts.json').write_text(json.dumps(counts,indent=2),encoding='utf-8')

if __name__=='__main__':
    main()
