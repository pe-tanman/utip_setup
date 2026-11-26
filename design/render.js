#!/usr/bin/env node
// Renders every design template to PNG/PDF in ../exports.
//   node design/render.js                 -> everything in design/manifest.json
//   node design/render.js --only story    -> only jobs whose name contains "story"
//   node design/render.js --event pipeline/events/2026-12-05.yaml --out exports/events
//        -> renders the event post + story for one event (used by the pipeline)
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const args = process.argv.slice(2);
const opt = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };

function loadYamlLite(file) {
  // Tiny "key: value" reader so the renderer has no npm dependencies.
  const out = {};
  for (const line of fs.readFileSync(file, 'utf8').split('\n')) {
    const m = line.match(/^([A-Za-z_]+):\s*(.*)$/);
    if (m) out[m[1]] = m[2].replace(/^["']|["']$/g, '');
  }
  return out;
}

(async () => {
  const club = JSON.parse(fs.readFileSync(path.join(__dirname, 'data/club.json'), 'utf8'));
  const officers = JSON.parse(fs.readFileSync(path.join(__dirname, 'data/officers.json'), 'utf8'));
  let jobs = JSON.parse(fs.readFileSync(path.join(__dirname, 'manifest.json'), 'utf8'));
  let event = null;
  let outDir = path.join(ROOT, opt('--out') || 'exports');

  if (opt('--event')) {
    event = loadYamlLite(path.resolve(opt('--event')));
    jobs = jobs.filter((j) => j.event);
  } else {
    jobs = jobs.filter((j) => !j.event);
  }
  if (opt('--only')) jobs = jobs.filter((j) => j.name.includes(opt('--only')));

  const browser = await chromium.launch();
  for (const job of jobs) {
    let pages = job.pages || [null];
    if (pages === 'officers') pages = ['cover', ...officers.map((_, i) => 'o' + i)];
    for (const [i, slide] of pages.entries()) {
      const page = await browser.newPage({ viewport: { width: job.width, height: job.height }, deviceScaleFactor: job.scale || 1 });
      await page.addInitScript((data) => { window.UTIP = data; }, { club, officers, event, slide, index: i });
      await page.goto('file://' + path.join(__dirname, 'templates', job.template));
      await page.evaluate(() => document.fonts.ready);
      const base = pages.length > 1 && !job.event ? `${job.name}-${String(i + 1).padStart(2, '0')}` : job.name;
      const dir = path.join(outDir, job.folder || '');
      fs.mkdirSync(dir, { recursive: true });
      await page.screenshot({ path: path.join(dir, base + '.png') });
      // PDF uses print layout: keep the same box as the screen render.
      if (job.pdf) await page.pdf({ path: path.join(dir, base + '.pdf'), width: job.width + 'px', height: job.height + 'px', printBackground: true });
      console.log('rendered', path.relative(ROOT, path.join(dir, base + '.png')));
      await page.close();
    }
  }
  await browser.close();
})();
