"""Export the Traditional Chinese proposal with embedded vector diagrams."""
import json
import os
import re
import shutil
import subprocess
from io import BytesIO
from html import escape
from pathlib import Path
import markdown
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from common import ROOT
from generate_schema_docs import DESCRIPTIONS

def md(content):
    # Printed documents link to repository references, not local file-system paths.
    def link(match):
        label, target = match.groups()
        if '://' not in target and not target.startswith('#'):
            relative = (ROOT/'docs'/target).resolve().relative_to(ROOT).as_posix()
            target = 'https://github.com/PearcePin/volleyball-database/blob/main/' + relative
        return f'[{label}]({target})'
    content=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,content)
    return markdown.markdown(content,extensions=['tables','fenced_code'])

def main():
    source=(ROOT/'docs/proposal_zh.md').read_text(encoding='utf-8')
    part1, remaining=source.split('## Part 2：E-R Diagram',1)
    er_text, schema_text=remaining.split('## Part 3：資料庫 Schema',1)
    er_text=re.sub(r'!\[[^\]]*\]\([^)]+\)','',er_text).strip()
    part1=part1.replace('# 期末企劃書 Part I：繁體中文理解版','# 期末專題企劃書 - Part I',1)
    part1=part1.replace('專題名稱：排球歷史賽事與球員數據管理系統。','**專題名稱：排球歷史賽事與球員數據管理系統**\n\nVolleyball Historical Statistics Database System  \n課程：Database Systems')
    # Keep source, data-quality facts, and all five queries in the standalone PDF.
    part1=part1.replace('詳細來源、授權與缺值見', '上游套件 DESCRIPTION 宣告 CC0。詳細來源、授權與缺值見')
    metadata=json.loads((ROOT/'docs/schema_metadata.json').read_text(encoding='utf-8'))
    er=(ROOT/'diagrams/er_diagram.svg').read_text(encoding='utf-8')
    schema=(ROOT/'diagrams/database_schema.svg').read_text(encoding='utf-8')
    parts=[f'<section class="prose intro">{md(part1)}</section>',
        '<section class="diagram-page"><h2>Part 2：E-R Diagram（實體關係圖）</h2>',
        '<p class="caption">採課本範例的實體長方形、菱形關係、底線主鍵、箭頭與雙線表示法。</p>',er,
        f'<div class="diagram-notes">{md(er_text)}</div></section>',
        '<section class="diagram-page"><h2>Part 3：Database Schema（資料庫結構圖）</h2>',
        '<p class="caption">九張資料表的實際欄位、型別與主外鍵。結構已核對 MySQL 與 sql/schema.sql。</p>',schema,
        '<p class="diagram-notes">PK＝主鍵；FK＝外鍵；UK＝唯一約束。NULL 表示允許缺值。複合外鍵必須整組閱讀。下一頁起提供各表完整欄位、用途及主鍵選擇原因。</p></section>']
    names=list(metadata)
    for offset in range(0,len(names),3):
        parts.append('<section class="schema-page"><h2>Part 3：Database Schema - 逐表說明</h2>')
        for i,name in enumerate(names[offset:offset+3],offset+1):
            t=metadata[name]
            fields='、'.join(f'<code>{escape(c["name"])}</code>' for c in t['columns'])
            pk=' + '.join(t['pk'])
            parts.extend([f'<article class="schema-card"><h3>{i}. {name}</h3>',
                f'<p>{escape(DESCRIPTIONS[name][0])}</p>',
                f'<p><strong>完整欄位：</strong>{fields}</p>',
                f'<p><strong>Primary Key：</strong><code>({escape(pk)})</code><br/><strong>選鍵原因：</strong>{escape(DESCRIPTIONS[name][1])}</p>'])
            if t['fks']:
                parts.append('<p><strong>Foreign Keys：</strong></p><ul>')
                for f in t['fks']:
                    left=', '.join(f['constrained_columns'])
                    right=f['referred_table']+'('+', '.join(f['referred_columns'])+')'
                    parts.append(f'<li><code>({escape(left)})</code> → <code>{escape(right)}</code></li>')
                parts.append('</ul>')
            else:
                parts.append('<p><strong>Foreign Keys：</strong>無。</p>')
            parts.append('</article>')
        if offset+3>=len(names):
            ending=schema_text[schema_text.index('核心設計盡量正規化。'):].split('報告練習請看',1)[0]
            parts.append('<div class="integrity"><h3>正規化、約束與實際驗證</h3>'+md(ending)+'</div>')
        parts.append('</section>')
    css='''
    @page {size:A4 portrait; margin:17mm 17mm 20mm;}
    @page diagram {size:A3 portrait; margin:14mm 14mm 20mm;}
    *{box-sizing:border-box;}body{margin:0;color:#172435;font-family:"Microsoft JhengHei","Noto Sans CJK TC",Arial,sans-serif;font-size:9.8pt;line-height:1.42;}
    h1{font-size:21pt;line-height:1.35;color:#11345c;margin:0 0 10pt;border-bottom:3px solid #9bbfdc;padding-bottom:9pt;}
    h2{font-size:15pt;color:#11345c;margin:12pt 0 8pt;break-after:avoid;}
    h3{font-size:11pt;color:#173f6b;margin:9pt 0 5pt;break-after:avoid;}
    p{margin:0 0 6pt;}a{color:#174f80;text-decoration:none;}strong{font-weight:700;}
    table{border-collapse:collapse;width:100%;font-size:8.5pt;line-height:1.5;margin:6pt 0 9pt;table-layout:fixed;}
    thead{display:table-header-group;}th{background:#e9f1f8;color:#12375c;font-weight:700;}
    th,td{border:1px solid #c5d3e0;padding:4pt;vertical-align:top;overflow-wrap:anywhere;}
    tr{break-inside:avoid;}td:first-child,th:first-child{width:17%;}
    code{font-family:Consolas,"Microsoft JhengHei",monospace;font-size:9pt;overflow-wrap:anywhere;}
    li{margin-bottom:3pt;}ul{margin:3pt 0 8pt;padding-left:19pt;}
    .intro h2{margin-top:12pt;}.diagram-page{page:diagram;break-before:page;break-after:page;break-inside:avoid;height:375mm;}
    .diagram-page h2{margin-top:0;}.diagram-page svg{display:block;width:265mm;height:270mm;max-height:none;margin:0 auto;}
    .caption{font-size:10pt;color:#526173;margin-bottom:10pt;}.diagram-notes{font-size:10pt;line-height:1.65;margin-top:10pt;}
    .schema-page{break-before:page;}.schema-page h2{margin-top:0;}.schema-card{break-inside:avoid;border-bottom:1px solid #c5d3e0;padding-bottom:8pt;margin-bottom:10pt;}
    .schema-card h3{margin-top:7pt;}.schema-card p{margin-bottom:5pt;}.schema-card li{font-size:9.4pt;line-height:1.5;}
    .integrity{break-inside:avoid;font-size:9.5pt;line-height:1.6;}
    '''
    html='<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>期末專題企劃書 - Part I（中文版）</title><style>'+css+'</style></head><body>'+''.join(parts)+'</body></html>'
    destination=ROOT/'output/pdf';destination.mkdir(parents=True,exist_ok=True)
    (destination/'Final_Project_Proposal_Part_I_zh.html').write_text(html,encoding='utf-8')
    node=shutil.which('node')
    local=Path(os.getenv('LOCALAPPDATA','.'))/'volleyball-node/node-v22.16.0-win-x64/node.exe'
    if not node and local.exists(): node=str(local)
    if not node: raise RuntimeError('Install Node.js before rendering the PDF.')
    subprocess.run([node,str(ROOT/'scripts/print_proposal.cjs')],check=True)
    # Merge explicitly rendered sections and add global page numbers.
    writer=PdfWriter()
    for file in sorted((ROOT/'.runtime/pdf-parts').glob('part-*.pdf')):
        writer.append(str(file))
    for i,page in enumerate(writer.pages,1):
        buffer=BytesIO(); width=float(page.mediabox.width);height=float(page.mediabox.height)
        layer=canvas.Canvas(buffer,pagesize=(width,height))
        layer.setFont('Helvetica',8);layer.setFillColorRGB(.38,.44,.51)
        layer.drawRightString(width-40,20,f'{i} / {len(writer.pages)}')
        layer.save();buffer.seek(0)
        page.merge_page(PdfReader(buffer).pages[0])
    writer.add_metadata({'/Title':'期末專題企劃書 - Part I（中文版）','/Subject':'排球歷史賽事與球員數據管理系統','/Author':'','/Creator':'Volleyball Database Project'})
    final=destination/'Final_Project_Proposal_Part_I_zh.pdf'
    with final.open('wb') as output:writer.write(output)
    print(f'Created {final.name}: {len(writer.pages)} pages')

if __name__=='__main__':
    main()
