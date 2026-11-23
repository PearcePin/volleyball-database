"""Draw textbook-style E-R notation as editable SVG, without image generation."""
import json
from html import escape
from common import ROOT

BOXES = {
 'League': (100,190,340,145), 'Season': (100,570,360,190),
 'Team': (1770,570,360,145), 'Season_Team': (870,570,450,160),
 'Player': (100,1020,400,220), 'Player_Team_Season': (870,1020,470,255),
 'Match': (1740,1020,460,350), 'Player_Match_Stats': (870,1670,470,410),
 'Match_Set': (1740,1840,460,190),
}
# name, parent, child, diamond center, arrow-to-one path, total-child path, cardinality labels
RELATIONS = [
 ('in_league','League','Season',(280,450),[(280,395),(280,335)],[(280,505),(280,570)],[(305,370,'1'),(305,550,'N')]),
 ('in_season','Season','Season_Team',(650,650),[(540,650),(460,650)],[(760,650),(870,650)],[(490,630,'1'),(810,630,'N')]),
 ('team_entry','Team','Season_Team',(1530,390),[(1640,390),(1950,390),(1950,570)],[(1420,390),(1250,390),(1250,570)],[(1975,540,'1'),(1275,540,'N')]),
 ('registers','Season_Team','Player_Team_Season',(1105,875),[(1105,820),(1105,730)],[(1105,930),(1105,1020)],[(1130,770,'1'),(1130,985,'N')]),
 ('membership','Player','Player_Team_Season',(650,1140),[(540,1140),(500,1140)],[(760,1140),(870,1140)],[(512,1116,'1'),(810,1116,'N')]),
 ('home_team','Season_Team','Match',(1530,615),[(1420,615),(1320,615)],[(1640,615),(1660,615),(1660,875),(1880,875),(1880,1020)],[(1350,592,'1'),(1905,985,'N')]),
 ('away_team','Season_Team','Match',(1510,770),[(1400,770),(1250,770),(1250,730)],[(1510,825),(1510,950),(1680,950),(1680,1120),(1740,1120)],[(1225,759,'1'),(1708,1100,'N')]),
 ('has_stats','Match','Player_Match_Stats',(1520,1530),[(1630,1530),(1670,1530),(1670,1260),(1740,1260)],[(1410,1530),(1360,1530),(1360,1785),(1340,1785)],[(1705,1238,'1'),(1368,1760,'N')]),
 ('performed_by','Player_Team_Season','Player_Match_Stats',(1105,1480),[(1105,1425),(1105,1275)],[(1105,1535),(1105,1670)],[(1130,1320,'1'),(1130,1635,'N')]),
 ('has_set','Match','Match_Set',(1970,1600),[(1970,1545),(1970,1370)],[(1970,1655),(1970,1840)],[(1995,1420,'1'),(1995,1805,'N')]),
]

def main():
 tables=json.loads((ROOT/'docs/schema_metadata.json').read_text(encoding='utf-8'))
 assert set(tables)==set(BOXES)
 for name,parent,child,*_ in RELATIONS:
  assert any(f['referred_table']==parent for f in tables[child]['fks']),name
 parts=['<svg xmlns="http://www.w3.org/2000/svg" width="2400" height="2410" viewBox="0 0 2400 2410">',
  '<rect width="2400" height="2410" fill="white"/>',
  '<defs><marker id="one" viewBox="0 0 12 10" refX="11" refY="5" markerWidth="12" markerHeight="10" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,5 L0,10" fill="none" stroke="#222" stroke-width="1.8"/></marker></defs>',
  '<style>text{fill:#111;font-family:"Times New Roman",serif}.title{font-family:Arial,sans-serif;font-size:43px;font-weight:700;fill:#092c56}.sub{font-family:Arial,sans-serif;font-size:22px;fill:#475569}.entity{font-size:29px;font-style:italic}.attr{font-size:25px}.flag{font-family:Arial,sans-serif;font-size:16px;fill:#526171}.relationship{font-size:25px;font-style:italic}.cardinality{font-size:23px}.legend{font-family:Arial,sans-serif;font-size:22px}</style>',
  '<text x="100" y="80" class="title">E-R Diagram for a Volleyball Historical Statistics Database</text>',
  '<text x="100" y="124" class="sub">Textbook notation: entity boxes, relationship diamonds, key underlines, arrows and double participation lines.</text>']
 def line(points,double=False,arrow=False):
  points=' '.join(f'{x},{y}' for x,y in points)
  if double:
   parts.append(f'<polyline points="{points}" fill="none" stroke="#222" stroke-width="7" stroke-linejoin="miter"/>')
   parts.append(f'<polyline points="{points}" fill="none" stroke="white" stroke-width="3" stroke-linejoin="miter"/>')
  else:
   parts.append(f'<polyline points="{points}" fill="none" stroke="#222" stroke-width="2"'+(' marker-end="url(#one)"' if arrow else '')+'/>')
 for name,parent,child,xy,one,many,labels in RELATIONS:
  line(one,arrow=True); line(many,double=True)
 for name,(x,y,w,h) in BOXES.items():
  t=tables[name]
  parts.append(f'<g id="entity-{name}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white" stroke="#222" stroke-width="2"/>')
  if name=='Match_Set':
   parts.append(f'<rect x="{x+5}" y="{y+5}" width="{w-10}" height="{h-10}" fill="none" stroke="#222" stroke-width="2"/>')
  inset=6 if name=='Match_Set' else 1
  parts += [f'<rect x="{x+inset}" y="{y+inset}" width="{w-2*inset}" height="39" fill="#d8edf5"/>',
   f'<line x1="{x}" y1="{y+41}" x2="{x+w}" y2="{y+41}" stroke="#222" stroke-width="2"/>',
   f'<text x="{x+w/2}" y="{y+29}" text-anchor="middle" class="entity">{escape(name)}</text>']
  fks={c for f in t['fks'] for c in f['constrained_columns']}
  for i,c in enumerate(t['columns']):
   cy=y+72+i*30; key=c['name'] in t['pk']; partial=name=='Match_Set' and c['name']=='set_number'
   deco=' text-decoration="underline"' if key and not partial else ''
   parts.append(f'<text x="{x+18}" y="{cy}" class="attr"{deco}>{escape(c["name"])}</text>')
   if partial:
    parts.append(f'<line x1="{x+18}" y1="{cy+4}" x2="{x+135}" y2="{cy+4}" stroke="#111" stroke-width="1.5" stroke-dasharray="5 3"/>')
   flags=', '.join(k for k,yes in [('PK',key),('FK',c['name'] in fks)] if yes)
   if flags:
    parts.append(f'<text x="{x+w-15}" y="{cy}" text-anchor="end" class="flag">{flags}</text>')
  parts.append('</g>')
 for name,parent,child,(x,y),one,many,labels in RELATIONS:
  def diamond(rx,ry,fill):
   parts.append(f'<polygon points="{x-rx},{y} {x},{y-ry} {x+rx},{y} {x},{y+ry}" fill="{fill}" stroke="#222" stroke-width="2"/>')
  diamond(110,55,'#edf7fb')
  if name=='has_set': diamond(102,47,'none')
  parts.append(f'<text x="{x}" y="{y+8}" text-anchor="middle" class="relationship">{name}</text>')
  for lx,ly,label in labels:
   parts.append(f'<text x="{lx}" y="{ly}" class="cardinality">{label}</text>')
 parts += [
  '<line x1="100" y1="2150" x2="2200" y2="2150" stroke="#cbd5e1"/>',
  '<text x="100" y="2200" class="legend">Notation: blue-header box = entity; diamond = relationship; solid underline = primary-key attribute.</text>',
  '<text x="100" y="2242" class="legend">Arrow points to the ONE side; double line = total participation of the child in that relationship; N = many.</text>',
  '<text x="100" y="2284" class="legend">Double box / diamond = weak entity / identifying relationship. Dashed underline = partial key (set_number).</text>',
  '<text x="100" y="2326" class="legend">Match_Set SQL primary key = (match_id, set_number). FK attributes remain visible to match the implemented schema.</text>',
  '<text x="100" y="2370" class="sub">Nine entities; ten relationships. Every imported match has 3-5 sets (checked by validation, not implied by the parent-side line).</text>', '</svg>']
 (ROOT/'diagrams/er_diagram.svg').write_text('\n'.join(parts),encoding='utf-8')
 print('Generated textbook-style er_diagram.svg; 9 entities and 10 FK relationships verified.')

if __name__=='__main__':
 main()
