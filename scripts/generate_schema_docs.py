"""Generate a schema reference and visual from the actual MySQL metadata."""
import json
import re
from html import escape
from sqlalchemy import inspect
from common import ROOT, engine

TABLES = ['League', 'Season', 'Team', 'Player', 'Season_Team',
          'Player_Team_Season', 'Match', 'Match_Set', 'Player_Match_Stats']
DESCRIPTIONS = {
    'League': ('保存男子與女子聯賽。', 'league_id 是穩定編號，不依賴可修改的名稱。'),
    'Season': ('保存各聯賽的賽季。', '來源季別在男女聯賽重複，因此使用全域 season_id，並對 league_id＋source_season_id 設唯一約束。'),
    'Team': ('保存跨季球隊身分與最新顯示名稱。', '沿用來源跨季穩定 team_id，球隊贊助更名不會產生另一支球隊。'),
    'Player': ('保存依來源解析的球員身分、姓名、性別與生日。', 'player_id 是獨立代理鍵；來源球衣號碼只在某季某隊有效，不能識別全球球員。'),
    'Season_Team': ('保存球隊參與賽季與當季名稱，解決球隊與賽季的多對多關係。', '同一隊可參加多季，一季有多隊，所以 season_id＋team_id 合起來才唯一。'),
    'Player_Team_Season': ('保存球員當季所屬球隊、來源編號、球衣與位置，保留轉隊歷史。', 'player_id＋team_id＋season_id 識別一次季別名冊關聯，允許同一球員同季出現在不同隊。'),
    'Match': ('保存比賽日期、階段、主客隊與最終局勝負；時間為德國當地時間。', '來源比賽編號跨季可能重複，所以使用全域 match_id，同時保留 source_match_id。'),
    'Match_Set': ('保存每場比賽依序排列的每局比分。', '每場都有第一局，所以必須用 match_id＋set_number 才能唯一識別一局。'),
    'Player_Match_Stats': ('保存一名球員代表一隊在一場比賽中的攻擊、攔網及發球統計。', 'match_id＋player_id＋team_id 唯一識別球員代表該隊的單場紀錄。'),
}

def type_name(column):
    value = str(column['type']).upper().split(' COLLATE ')[0]
    return 'INT' if value == 'INTEGER' else value

def collect():
    inspector = inspect(engine())
    sql = (ROOT/'sql/schema.sql').read_text(encoding='utf-8')
    result = {}
    for name in TABLES:
        columns = inspector.get_columns(name)
        pk = inspector.get_pk_constraint(name)['constrained_columns']
        fks = inspector.get_foreign_keys(name)
        for fk in fks:
            fk['referred_table'] = next(t for t in TABLES if t.casefold() == fk['referred_table'].casefold())
        uniques = inspector.get_unique_constraints(name)
        checks = inspector.get_check_constraints(name)
        # Compare the diagram/document fields and types with the checked-in DDL.
        block = re.search(r'CREATE TABLE IF NOT EXISTS `?' + name + r'`? \((.*?)\n\) ENGINE', sql, re.S).group(1)
        declared = re.findall(r'^ (\w+) (INT|DATETIME|DATE|VARCHAR\(\d+\))(?=\s|,|$)', block, re.M)
        actual = [(c['name'], type_name(c)) for c in columns]
        if declared != actual:
            raise ValueError(f'Schema SQL and live MySQL differ: {name}: {declared} vs {actual}')
        result[name] = dict(columns=[dict(name=c['name'], type=type_name(c), nullable=c['nullable']) for c in columns],
                            pk=pk, fks=fks, uniques=uniques, checks=checks)
    return result

def reference(tables):
    lines = ['# Database Schema — 排球資料庫結構說明', '',
        '此文件與圖表依實際 MySQL metadata 產生，並核對 `sql/schema.sql` 的欄位名稱、順序與型別。資料庫名稱：`volleyball_db`。', '',
        '![Database Schema](../diagrams/database_schema.png)', '',
        '[開啟可放大 SVG](../diagrams/database_schema.svg) · [完整 ER 關聯圖](../diagrams/er_diagram.md) · [可執行建表 SQL](../sql/schema.sql)', '',
        '**PK**＝主鍵；**FK**＝外鍵；**UK**＝唯一約束；**NULL**＝允許來源缺值。複合鍵必須整組閱讀，不能拆成各自獨立的鍵。', '']
    for i,(name,t) in enumerate(tables.items(),1):
        fkcols = {c for f in t['fks'] for c in f['constrained_columns']}
        attributes = ', '.join(c['name'] for c in t['columns'])
        lines += [f'## {i}. {name}', '', DESCRIPTIONS[name][0], '',
                  '```text', f'{name}({attributes})', 'PK: (' + ', '.join(t['pk']) + ')', '```', '',
                  '| 欄位 | MySQL 型別 | 鍵 | 允許 NULL |', '|---|---|---|---|']
        for c in t['columns']:
            keys = [k for k,yes in [('PK',c['name'] in t['pk']),('FK',c['name'] in fkcols)] if yes]
            if any(u['column_names']==[c['name']] for u in t['uniques']):
                keys.append('UK')
            lines.append(f"| {c['name']} | {c['type']} | {', '.join(keys) or '—'} | {'是' if c['nullable'] else '否'} |")
        lines += ['', '**主鍵：** `(' + ', '.join(t['pk']) + ')`。' + DESCRIPTIONS[name][1], '']
        for f in t['fks']:
            lines += [f"- FK `({', '.join(f['constrained_columns'])})` → `{f['referred_table']}({', '.join(f['referred_columns'])})`。"]
        for u in t['uniques']:
            lines += [f"- UNIQUE `({', '.join(u['column_names'])})`。"]
        for c in t['checks']:
            lines += [f"- CHECK：`{c['sqltext']}`。"]
        lines.append('')
    lines += ['## 關聯與正規化說明', '',
        'League → Season 是一對多。Season 與 Team 透過 Season_Team 成為多對多；Player 透過 Player_Team_Season 保留每季的球隊關聯。Match 的主客隊各連到同季的 Season_Team。Match_Set 透過 match_id 連到比賽；Player_Match_Stats 同時連到比賽與球員季別名冊。', '',
        'Player_Match_Stats.season_id 可以由 match_id 推得，但刻意保留以建立兩組複合外鍵，強制保證比賽與球員名冊賽季一致。這是受約束的少量冗餘，不宣稱所有表嚴格符合 3NF。', '',
        '每場局數、局勝負、比分合法性及球員是否屬於主客隊，屬於跨列或跨表規則，由匯入交易及 validate_data.py 驗證。一般 CHECK 不能替代這些加總檢查。', '',
        '重新產生：先啟動 MySQL，再執行 `python scripts/generate_schema_docs.py`。PNG 由 `node scripts/render_schema.cjs` 將 SVG 在本機轉出；需要 Node.js 與 Puppeteer，安裝方式見 README。']
    (ROOT/'docs/database_schema.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def visual(tables):
    width = 1920
    card_w = 600
    row_heights = [300, 400, 570]
    row_ys = [150, 490, 930]
    fk_lines = []
    for name,t in tables.items():
        for f in t['fks']:
            fk_lines.append(f"{name}({', '.join(f['constrained_columns'])})  →  {f['referred_table']}({', '.join(f['referred_columns'])})")
    footer_y = 1550
    height = footer_y + 110 + 33*len(fk_lines) + 75
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="#f1f5f9"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#172554}.title{font-size:38px;font-weight:700}.sub{font-size:20px;fill:#475569}.table{font-size:25px;font-weight:700;fill:white}.col{font-size:19px}.small{font-size:17px;fill:#475569}.key{font-size:17px;font-weight:700;fill:#1d4ed8}.ref{font-size:18px}</style>',
           '<text x="30" y="55" class="title">Volleyball Database Schema</text>',
           '<text x="30" y="92" class="sub">volleyball_db | 9 tables | PK = Primary Key · FK = Foreign Key · UK = Unique Key</text>',
           '<text x="30" y="122" class="sub">Columns and data types verified against MySQL and sql/schema.sql. Composite references are listed below.</text>']
    for i,(name,t) in enumerate(tables.items()):
        x=30+(i%3)*630; y=row_ys[i//3]; h=row_heights[i//3]
        svg += [f'<rect x="{x}" y="{y}" width="{card_w}" height="{h}" rx="12" fill="white" stroke="#cbd5e1"/>',
                f'<path d="M{x+12},{y} H{x+card_w-12} Q{x+card_w},{y} {x+card_w},{y+12} V{y+52} H{x} V{y+12} Q{x},{y} {x+12},{y}" fill="#1e3a8a"/>',
                f'<text x="{x+18}" y="{y+34}" class="table">{escape(name)}</text>']
        fkcols={c for f in t['fks'] for c in f['constrained_columns']}
        for j,c in enumerate(t['columns']):
            cy=y+85+j*33
            key=','.join(k for k,yes in [('PK',c['name'] in t['pk']),('FK',c['name'] in fkcols),('UK',any(u['column_names']==[c['name']] for u in t['uniques']))] if yes)
            svg += [f'<text x="{x+16}" y="{cy}" class="key">{key}</text>',
                    f'<text x="{x+95}" y="{cy}" class="col">{escape(c["name"])}</text>',
                    f'<text x="{x+380}" y="{cy}" class="small">{escape(c["type"])}{" NULL" if c["nullable"] else ""}</text>']
        svg += [f'<text x="{x+16}" y="{y+h-22}" class="small">PK: {escape(" + ".join(t["pk"]))}</text>']
    svg += [f'<text x="30" y="{footer_y}" class="title">Foreign Key References</text>']
    for i,line in enumerate(fk_lines):
        svg += [f'<text x="30" y="{footer_y+45+i*33}" class="ref">{escape(line)}</text>']
    svg += [f'<text x="30" y="{height-32}" class="sub">Read composite keys as a group. UNIQUE and CHECK details: docs/database_schema.md and sql/schema.sql.</text>', '</svg>']
    (ROOT/'diagrams/database_schema.svg').write_text('\n'.join(svg),encoding='utf-8')
    (ROOT/'docs/schema_metadata.json').write_text(json.dumps(tables,indent=2,ensure_ascii=False),encoding='utf-8')

if __name__=='__main__':
    tables=collect()
    reference(tables)
    visual(tables)
    print(f'PASS: {len(tables)} table definitions match SQL. Schema document and SVG generated.')
