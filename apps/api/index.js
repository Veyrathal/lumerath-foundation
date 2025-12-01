import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { z } from 'zod';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(cors());
app.use(express.json());
const PUBLIC_DIR = path.join(process.cwd(), 'apps', 'api', 'public');
app.use(express.static(PUBLIC_DIR));
app.get('/studio', (_req, res) => res.sendFile(path.join(PUBLIC_DIR, 'studio.html')));

// ENV + paths
const MEDIA_ROOT = process.env.MEDIA_ROOT || path.join(__dirname, '..', '..', 'storage');
const CODEX_DIR = path.resolve(MEDIA_ROOT, 'codex');
const RENDER_OUT = process.env.RENDER_OUT || path.resolve(MEDIA_ROOT, 'generated');

// Schemas
const RenderRequest = z.object({
  entryId: z.string(),
  template: z.enum(['parchment','open-weave','spiral']).default('parchment'),
  width: z.number().default(1080),
  height: z.number().default(1350),
  watermark: z.boolean().default(true)
});

// Helpers
function loadEntry(id) {
  const p = path.join(CODEX_DIR, `${id}.json`);
  if (!fs.existsSync(p)) return null;
  const raw = fs.readFileSync(p, 'utf8');
  const clean = raw.replace(/^\uFEFF/, ''); // strip BOM if present
  return JSON.parse(clean);
}


function ensureDir(p) {
  if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true });
}

// Routes
app.get('/entries/:id', (req, res) => {
  const entry = loadEntry(req.params.id);
  if (!entry) return res.status(404).json({ error: 'Entry not found' });
  return res.json({ ok: true, entry });
});
app.get('/entries', (_req, res) => {
  const files = fs.readdirSync(CODEX_DIR).filter(f => f.endsWith('.json'));
  const entries = files.map(f => {
    const raw = fs.readFileSync(path.join(CODEX_DIR, f), 'utf8').replace(/^\uFEFF/, '');
    const j = JSON.parse(raw);
    return { id: j.id, title: j.title || j.id };
  });
  res.json({ ok: true, entries });
});

// --- parchment render endpoint ---
app.post('/render', async (req, res) => {
  try {
    const { createCanvas } = await import('@napi-rs/canvas');

    // payload + entry
    const payload = RenderRequest.parse(req.body);
    const entry = loadEntry(payload.entryId);
    if (!entry) return res.status(404).json({ ok: false, error: 'Entry not found' });

    const W = payload.width || 1080;
    const H = payload.height || 1350;

    // canvas + ctx
    const canvas = createCanvas(W, H);
    const ctx = canvas.getContext('2d');

    // parchment background
    const bg = ctx.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, '#3b2f2f');   // deep brown
    bg.addColorStop(0.25, '#5a463d');
    bg.addColorStop(1, '#e7d4b5');   // warm parchment
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);

    // helper: wrap text
    function wrapText(text, x, y, maxWidth, lineHeight) {
      const words = (text || '').split(/\s+/);
      let line = '', yy = y;
      for (let n = 0; n < words.length; n++) {
        const test = line ? line + ' ' + words[n] : words[n];
        const metrics = ctx.measureText(test);
        if (metrics.width > maxWidth && n > 0) {
          ctx.fillText(line, x, yy);
          yy += lineHeight;
          line = words[n];
        } else {
          line = test;
        }
      }
      if (line) ctx.fillText(line, x, yy);
      return yy;
    }

    // margins + colors
    const M = 80;
    const innerW = W - M * 2;

    // Title
    ctx.fillStyle = '#f5deb3';
    ctx.font = 'bold 48px Georgia';
    ctx.fillText(entry.title || payload.entryId, M, M + 40);

    // Body
    ctx.font = '26px Georgia';
    ctx.globalAlpha = 0.95;
    const bodyTop = M + 100;
    const lastY = wrapText(entry.body || '', M, bodyTop, innerW, 40);

    // SovLang line with soft glow
    if (entry.sovlang) {
      ctx.save();
      ctx.font = '28px Georgia';
      ctx.globalAlpha = 1;
      ctx.shadowColor = 'rgba(255, 240, 200, 0.75)';
      ctx.shadowBlur = 12;
      ctx.fillStyle = '#ffe7b3';
      const sov = entry.sovlang;
      // centered at the bottom margin
      const metrics = ctx.measureText(sov);
      const x = (W - metrics.width) / 2;
      const y = H - M - 20;
      ctx.fillText(sov, x, y);
      ctx.restore();
    }

    // Optional watermark
    if (payload.watermark) {
      ctx.save();
      ctx.globalAlpha = 0.25;
      ctx.font = '18px Georgia';
      ctx.fillStyle = '#ffffff';
      ctx.fillText(entry.design?.watermark || 'Lumerath-Seal', W - M - 220, H - M + 10);
      ctx.restore();
    }

    // save file with timestamp
    const stamp = new Date().toISOString().replace(/[:.]/g, '-');
    const fileName = `${payload.entryId}-${stamp}.png`;
    const outPath = path.join(RENDER_OUT, fileName);
    fs.writeFileSync(outPath, canvas.toBuffer('image/png'));

    // return both local path + public URL
    return res.json({
      ok: true,
      file: outPath.replaceAll('\\', '/'),
      url: `/media/${fileName}`
    });
  } catch (err) {
    console.error(err);
    if (err?.issues) return res.status(400).json({ ok: false, error: 'Invalid payload', issues: err.issues });
    return res.status(500).json({ ok: false, error: 'Render error' });
  }
});

// Quick view: generate then redirect to the image
app.get('/render/:id', async (req, res) => {
  try {
    const { createCanvas } = await import('@napi-rs/canvas');
    const entryId = req.params.id;
    const entry = loadEntry(entryId);
    if (!entry) return res.status(404).send('Entry not found');

    const W = 1080, H = 1350;
    const canvas = createCanvas(W, H);
    const ctx = canvas.getContext('2d');

    const bg = ctx.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, '#3b2f2f');
    bg.addColorStop(0.25, '#5a463d');
    bg.addColorStop(1, '#e7d4b5');
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);

    // title
    ctx.fillStyle = '#f5deb3';
    ctx.font = 'bold 48px Georgia';
    ctx.fillText(entry.title || entryId, 80, 120);

    // body
    ctx.font = '26px Georgia';
    const text = entry.body || '';
    const wrap = (t, x, y, max, lh) => {
      const words = t.split(/\s+/); let line = '', yy = y;
      for (let i=0;i<words.length;i++){
        const test = line ? line + ' ' + words[i] : words[i];
        if (ctx.measureText(test).width > max && i>0){ ctx.fillText(line,x,yy); yy+=lh; line=words[i]; }
        else line = test;
      }
      if (line) ctx.fillText(line, x, yy);
    };
    wrap(text, 80, 200, W-160, 40);

    // sovlang glow bottom
    if (entry.sovlang){
      ctx.save();
      ctx.font = '28px Georgia';
      ctx.shadowColor = 'rgba(255,240,200,0.75)';
      ctx.shadowBlur = 12;
      ctx.fillStyle = '#ffe7b3';
      const m = ctx.measureText(entry.sovlang);
      ctx.fillText(entry.sovlang, (W - m.width)/2, H - 100);
      ctx.restore();
    }

    const stamp = new Date().toISOString().replace(/[:.]/g,'-');
    const fileName = `${entryId}-${stamp}.png`;
    const outPath = path.join(RENDER_OUT, fileName);
    fs.writeFileSync(outPath, canvas.toBuffer('image/png'));
    return res.redirect(`/media/${fileName}`);
  } catch (e) {
    console.error(e);
    return res.status(500).send('Render error');
  }
});

// serve rendered files at /media/...
app.use('/media', express.static(RENDER_OUT));

const PORT = process.env.PORT || 7070;
app.listen(PORT, () => {
  console.log(`[Lumerath API] listening on http://localhost:${PORT}`);
  console.log('MEDIA_ROOT:', MEDIA_ROOT);
  console.log('RENDER_OUT:', RENDER_OUT);
});
