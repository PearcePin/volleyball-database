// Render the local SVG to PNG; no network or user browser session is used.
const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');
let puppeteer;
try {
  puppeteer = require('puppeteer');
} catch {
  const local = path.join(process.env.LOCALAPPDATA || '', 'volleyball-mermaid', 'node_modules', 'puppeteer');
  if (!fs.existsSync(local)) throw new Error('Install rendering dependency: npm.cmd install --no-save puppeteer@23.11.1');
  puppeteer = require(local);
}
(async () => {
  const root = path.resolve(__dirname, '..');
  const input = path.join(root, 'diagrams', 'database_schema.svg');
  const svg = fs.readFileSync(input, 'utf8');
  const width = Number(svg.match(/width="(\d+)"/)[1]);
  const height = Number(svg.match(/height="(\d+)"/)[1]);
  const browser = await puppeteer.launch({ headless: true });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width, height, deviceScaleFactor: 1 });
    await page.goto(pathToFileURL(input).href, { waitUntil: 'load' });
    await page.screenshot({ path: path.join(root, 'diagrams', 'database_schema.png'), fullPage: true });
    console.log('Rendered database_schema.png');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
