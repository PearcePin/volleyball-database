// Print the same offline HTML and vector diagrams to the Chinese PDF.
const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');
let puppeteer;
try { puppeteer = require('puppeteer'); }
catch { puppeteer = require(path.join(process.env.LOCALAPPDATA, 'volleyball-mermaid/node_modules/puppeteer')); }
(async () => {
  const output = path.resolve(__dirname, '../output/pdf');
  const browser = await puppeteer.launch({ headless: true });
  try {
    const page = await browser.newPage();
    await page.goto(pathToFileURL(path.join(output, 'Final_Project_Proposal_Part_I_zh.html')).href, { waitUntil: 'load' });
    const components = await page.evaluate(() => ({
      css: document.head.querySelector('style').textContent,
      sections: [...document.querySelectorAll('body > section')].map(s => ({html:s.outerHTML, diagram:s.classList.contains('diagram-page')})),
    }));
    const directory = path.resolve(__dirname, '../.runtime/pdf-parts');
    fs.mkdirSync(directory, {recursive:true});
    for (const old of fs.readdirSync(directory).filter(n => /^part-\d+\.pdf$/.test(n))) fs.unlinkSync(path.join(directory,old));
    for (const [index, section] of components.sections.entries()) {
      const size=section.diagram?'A3':'A4';
      const override=`@page {size:${size} portrait;margin:17mm 17mm 20mm;} .diagram-page{page:auto!important;break-before:auto;break-after:auto;break-inside:auto;height:auto;} .schema-page{break-before:auto;}`;
      await page.setContent('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><style>'+components.css+'\n'+override+'</style></head><body>'+section.html+'</body></html>',{waitUntil:'load'});
      await page.evaluate(() => document.fonts.ready);
      await page.pdf({
        path:path.join(directory,`part-${String(index+1).padStart(2,'0')}.pdf`),
        preferCSSPageSize:true,printBackground:true,displayHeaderFooter:true,
        headerTemplate:'<span></span>',
        footerTemplate:'<div style="width:100%;text-align:center;font:9px Arial;color:#64748b;">Final Project Proposal - Part I</div>',
      });
    }
    console.log('Rendered '+components.sections.length+' proposal sections.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
