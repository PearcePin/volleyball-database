"""Render the requested textbook-style E-R diagram locally as SVG and PNG."""
import os
import shutil
import subprocess
from pathlib import Path
from common import ROOT
from generate_chen_diagram import main as draw

def main():
    draw()
    node=shutil.which('node')
    bundled=Path(os.getenv('LOCALAPPDATA','.'))/'volleyball-node/node-v22.16.0-win-x64/node.exe'
    if not node and bundled.exists():
        node=str(bundled)
    if not node:
        raise RuntimeError('Install Node.js to render PNG. The editable SVG was generated successfully.')
    subprocess.run([node,str(ROOT/'scripts/render_schema.cjs'),'er_diagram'],check=True)

if __name__=='__main__':
    main()
