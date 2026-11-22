"""Render Mermaid locally with the official Mermaid CLI. No schema upload."""
import os
import shutil
import subprocess
from pathlib import Path
from common import ROOT

def main():
    content=(ROOT/'diagrams/er_diagram.md').read_text(encoding='utf-8')
    mermaid=content.split('```mermaid\n',1)[1].split('```',1)[0]
    (ROOT/'diagrams/er_diagram.mmd').write_text(mermaid,encoding='utf-8')
    local=Path(os.getenv('LOCALAPPDATA','.'))
    node_dir=local/'volleyball-node/node-v22.16.0-win-x64'
    if node_dir.exists():
        os.environ['PATH']=str(node_dir)+os.pathsep+os.environ['PATH']
    executable=shutil.which('mmdc')
    installed=local/'volleyball-mermaid/node_modules/.bin/mmdc.cmd'
    if not executable and installed.exists():
        executable=str(installed)
    if not executable:
        raise RuntimeError('Install Node.js and run: npm install -g @mermaid-js/mermaid-cli@11.4.3')
    for extension in ['svg','png']:
        subprocess.run([executable,'-i',str(ROOT/'diagrams/er_diagram.mmd'),
            '-o',str(ROOT/f'diagrams/er_diagram.{extension}'),'-b','white','-s','2'],check=True)
        print('Rendered '+extension)

if __name__=='__main__':
    main()
