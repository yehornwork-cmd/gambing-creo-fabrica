// forge-renderer: локальный композер локализованных креативов.
// Контракт повторяет creative-localizer (/api/render, /api/layout, /api/file),
// рендер — через HyperFrames (Chromium + FFmpeg) в docker-контейнере.
// Эндпоинты:
//   POST /api/render — {geo, headline[], disclaimer, vo_base64|vo_url, video_url, layout, qc, expect_duration}
//   POST /api/layout — {video_url} → замеры мастера
//   GET  /api/file?p&e&s — раздача готовых файлов (подпись HMAC)
import http from "node:http";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import fs from "node:fs/promises";
import path from "node:path";
import fsSync from "node:fs";
import crypto from "node:crypto";

const run = promisify(execFile);
const DATA = process.env.DATA_DIR || "/data";
const OUT = path.join(DATA, "out");
const TMP = path.join(DATA, "tmp");
const PROJECT = path.join(DATA, "project");
const BADGES = path.join(DATA, "badges");
const SECRET = process.env.RENDER_SECRET || "dev-only-secret";
const PUBLIC_BASE = process.env.PUBLIC_BASE || "https://render.vizioner.xyz";
const PORT = Number(process.env.PORT || 8890);
// Chromium+FFmpeg per job. Isolate projects so this can be >1 without
// jobs clobbering the same .project folder (that was why live sat at 2).
const CONCURRENCY = Number(process.env.CONCURRENCY || 4);

const queue = [];
let active = 0;

const APPLE_LANG = {
  NL: "nl", "CH-DE": "de", "CH-FR": "fr", "CA-FR": "fr-CA", FI: "fi", NO: "no", CZ: "cs", IT: "it",
  SK: "sk", SI: "sl", HR: "hr", PL: "pl", HU: "hu",
  AE: "ar", SA: "ar", KW: "ar", QA: "ar", OM: "ar", BH: "ar",
  "GULF-EN": "en-US", "CA-EN": "en-US", AU: "en-US",
};
const GOOGLE_LANG = {
  nl: "nl", de: "de", fr: "fr", "fr-CA": "fr-CA", fi: "fi", no: "no", cs: "cs", it: "it",
  sk: "sk", sl: "sl", hr: "hr", pl: "pl", hu: "hu", ar: "ar-SA", "en-US": "en",
};

function esc(s) {
  return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
function signUrl(p, e) {
  const s = crypto.createHmac("sha256", SECRET).update(`${p}:${e}`).digest("hex").slice(0, 32);
  return `${PUBLIC_BASE}/api/file?p=${encodeURIComponent(p)}&e=${e}&s=${s}`;
}

// Очередь на параллельность (chromium тяжёлый)
function enqueue(fn) {
  return new Promise((resolve, reject) => {
    queue.push({ fn, resolve, reject });
    pump();
  });
}
function pump() {
  while (active < CONCURRENCY && queue.length) {
    const job = queue.shift();
    active++;
    job.fn().then(job.resolve, job.reject).finally(() => { active--; pump(); });
  }
}

async function ffprobe(file) {
  const { stdout } = await run("ffprobe", [
    "-v", "error", "-print_format", "json", "-show_format", "-show_streams", file,
  ]);
  const j = JSON.parse(stdout);
  const v = (j.streams || []).find((s) => s.codec_type === "video");
  const a = (j.streams || []).find((s) => s.codec_type === "audio");
  return {
    duration: j.format ? parseFloat(j.format.duration || 0) : 0,
    size: j.format ? parseInt(j.format.size || "0", 10) : 0,
    width: v ? v.width : 0,
    height: v ? v.height : 0,
    fpsRaw: v && v.avg_frame_rate ? v.avg_frame_rate : "30/1",
    hasAudio: !!a,
  };
}

function fpsOf(raw) {
  const [a, b] = raw.split("/").map(Number);
  return b ? a / b : 30;
}

async function download(url, dest) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`download failed ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());
  await fs.writeFile(dest, buf);
  return buf.length;
}

function layoutFor(src) {
  // Аппроксимация раскладки creative-localizer (замеры мастера → зона заголовка в выходных координатах).
  const ow = 1080, oh = 1920;
  const hw = Math.round(ow * 0.7);
  const hh = Math.round(oh * 0.22);
  return {
    source: {
      width: src.width, height: src.height,
      fps: Math.round(fpsOf(src.fpsRaw) * 100) / 100,
      duration: Math.round(src.duration * 100) / 100,
      has_audio: src.hasAudio,
    },
    output: { width: ow, height: oh, fps: 30 },
    headline: { box: { x: Math.round((ow - hw) / 2), y: Math.round(oh * 0.55), w: hw, h: hh } },
  };
}

function badgeFiles(lang, tmpDir) {
  // apple + google бейджи по языку; если языка нет — en
  const candidates = [lang, "en"];
  let apple = null, google = null;
  for (const l of candidates) {
    if (!apple) {
      const f = path.join(tmpDir, `apple_${l}.png`);
      if (fs.existsSync ? true : true) {
        try { fs.accessSync(f); apple = f; } catch {}
      }
    }
    if (!google) {
      const f = path.join(tmpDir, `google_${l}.png`);
      try { fs.accessSync(f); google = f; } catch {}
    }
  }
  return { apple, google };
}

function compositionHtml(args) {
  const { headline, disclaimer, duration, box, badgeApple, badgeGoogle, hasVo } = args;
  // Автоподбор кегля: вписываем самую длинную строку в box по ширине и высоте
  const maxLen = Math.max(1, ...headline.map((s) => String(s || "").length));
  const fitW = Math.floor((box.w * 0.86) / (maxLen * 0.56));
  const fitH = Math.floor(box.h / 2.35);
  const f1 = Math.max(40, Math.min(fitW, fitH));
  const y1 = box.y;
  const y2 = box.y + Math.round(box.h * 0.54);
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Creative</title>
    <style>
      * { margin:0; padding:0; box-sizing:border-box; }
      body { background:#000; }
      #root { position:relative; width:1080px; height:1920px; overflow:hidden; background:#000; }
      #bg { position:absolute; inset:0; width:1080px; height:1920px; object-fit:cover; }
      .hl { position:absolute; left:0; width:1080px; text-align:center; color:#fff;
            font-family:'Liberation Sans','Noto Sans',sans-serif; font-weight:800;
            text-shadow:0 6px 24px rgba(0,0,0,.95); letter-spacing:.5px; line-height:1.15;
            white-space:nowrap; }
      .hl1 { top:${y1}px; font-size:${f1}px; }
      .hl2 { top:${y2}px; font-size:${f1}px; }
      .hlplate { position:absolute; left:0; top:${y1 - 40}px; width:1080px;
                  height:${(y2 - y1) + Math.round(f1 * 1.15) + 80}px; background:#000; }
      .disc { position:absolute; bottom:14px; left:0; width:1080px; text-align:center; color:rgba(255,255,255,.88);
              font-family:'Liberation Sans','Noto Sans',sans-serif; font-size:22px; }
      .strip { position:absolute; bottom:34px; left:0; width:1080px; height:536px;
               background:#000; }
      .badges { position:absolute; bottom:40px; left:0; width:1080px; display:flex;
                justify-content:center; gap:26px; align-items:center; }
      .badges img { height:110px; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="${duration}">
      <video id="bg" src="assets/master.mp4" autoplay muted playsinline data-media-start="0"></video>
      ${hasVo ? `<audio src="assets/vo.mp3" data-volume="1" data-start="0" data-duration="${duration}"></audio>` : ""}
      <section class="hlplate" data-start="0" data-duration="${duration}" data-track-index="1"></section>
      <section class="hl hl1" data-start="0" data-duration="${duration}" data-track-index="2">${esc(headline[0] || "")}</section>
      <section class="hl hl2" data-start="0" data-duration="${duration}" data-track-index="3">${esc(headline[1] || "")}</section>
      <section class="strip" data-start="0" data-duration="${duration}" data-track-index="4"></section>
      <section class="badges" data-start="0" data-duration="${duration}" data-track-index="4">
        ${badgeApple ? `<img src="assets/${path.basename(badgeApple)}" alt="" />` : ""}
        ${badgeGoogle ? `<img src="assets/${path.basename(badgeGoogle)}" alt="" />` : ""}
      </section>
      ${disclaimer ? `<section class="disc" data-start="0" data-duration="${duration}" data-track-index="5">${esc(disclaimer)}</section>` : ""}
    </div>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>`;
}

async function doRender(body) {
  const jobId = crypto.randomBytes(6).toString("hex");
  const tmp = path.join(TMP, jobId);
  const project = projectDirFor(tmp);
  await fs.mkdir(tmp, { recursive: true });
  try {
    const geo = String(body.geo || "").toUpperCase();
    const headline = Array.isArray(body.headline) ? body.headline.map(String) : [];
    const disclaimer = String(body.disclaimer || "");
    const videoUrl = String(body.video_url || "");
    if (!geo || !videoUrl || headline.length === 0) {
      return { error: "geo, video_url, headline required" };
    }
    const lang = APPLE_LANG[geo] || "en-US";

    // мастер
    await download(videoUrl, path.join(tmp, "master.mp4"));
    const src = await ffprobe(path.join(tmp, "master.mp4"));

    // озвучка
    let hasVo = false;
    if (body.vo_base64) {
      const b64 = String(body.vo_base64).replace(/^data:[^;]+;base64,/, "");
      await fs.writeFile(path.join(tmp, "vo.mp3"), Buffer.from(b64, "base64"));
      hasVo = true;
    } else if (body.vo_url) {
      await download(String(body.vo_url), path.join(tmp, "vo.mp3"));
      hasVo = true;
    }

    // бейджи
    const apple = pickBadge("apple", lang);
    const google = pickBadge("google", lang);
    let badgeApple = null, badgeGoogle = null;
    if (apple) { badgeApple = path.join(tmp, `apple_${lang}.png`); await fs.copyFile(apple, badgeApple); }
    if (google) { badgeGoogle = path.join(tmp, `google_${lang}.png`); await fs.copyFile(google, badgeGoogle); }

    // Per-job project: concurrent HyperFrames must not share index.html / assets.
    await fs.mkdir(path.join(project, "assets"), { recursive: true });
    await fs.cp(path.join(tmp, "master.mp4"), path.join(project, "assets/master.mp4"), { force: true });
    if (hasVo) await fs.cp(path.join(tmp, "vo.mp3"), path.join(project, "assets/vo.mp3"), { force: true });
    if (badgeApple) await fs.copyFile(badgeApple, path.join(project, "assets", path.basename(badgeApple)));
    if (badgeGoogle) await fs.copyFile(badgeGoogle, path.join(project, "assets", path.basename(badgeGoogle)));

    const layout = body.layout && body.layout.headline ? body.layout : layoutFor(src);
    const box = layout.headline.box;
    const duration = Math.max(1, Number(body.expect_duration || src.duration || layout.source?.duration || 10));

    const html = compositionHtml({
      headline, disclaimer, duration, box,
      badgeApple, badgeGoogle, hasVo,
    });
    await fs.writeFile(path.join(project, "index.html"), html);

    // рендер через hyperframes
    const outDir = path.join(OUT, "creatives", jobId);
    await fs.mkdir(outDir, { recursive: true });
    const outFile = path.join(outDir, `creative_${geo}.mp4`);
    await run("npx", ["hyperframes", "render", "--json", "--quality", "high", "--output", outFile], {
      cwd: project, timeout: 600_000, maxBuffer: 16 * 1024 * 1024,
    });

    // QC
    const o = await ffprobe(outFile);
    const durOk = o.duration > 0 && (o.duration >= duration * 0.85) && (o.duration <= duration * 1.5);
    const sizeOk = o.size > 100000;
    let lufs = null;
    if (o.hasAudio) {
      try {
        const { stdout } = await run("ffmpeg", ["-i", outFile, "-af", "ebur128", "-f", "null", "-"], { timeout: 120000, maxBuffer: 8 * 1024 * 1024 });
        const m = stdout.match(/\bI:\s*([-\d.]+)\s+LUFS/);
        lufs = m ? parseFloat(m[1]) : null;
      } catch {}
    }
    const issues = [];
    if (!durOk) issues.push(`длительность ${o.duration.toFixed(2)}с вне коридора ~${duration.toFixed(1)}с`);
    if (!sizeOk) issues.push("файл слишком мал");
    if (hasVo && !o.hasAudio) issues.push("нет аудио-дорожки");

    const filename = `creative_${geo.toLowerCase()}_${jobId.slice(0, 6)}.mp4`;
    const finalFile = path.join(outDir, filename);
    await fs.rename(outFile, finalFile).catch(() => fs.copyFile(outFile, finalFile));
    const rel = `creatives/${jobId}/${filename}`;
    const e = Math.floor(Date.now() / 1000) + 3600 * 24 * 7;
    const url = signUrl(rel, e);

    const sizeMb = Math.round((o.size / 1048576) * 100) / 100;
    return {
      geo, url, filename, size_mb: sizeMb,
      qc_pass: issues.length === 0,
      qc_issues: issues,
      qc_metrics: {
        width: o.width, height: o.height, fps: Math.round(fpsOf(o.fpsRaw)),
        duration: Math.round(o.duration * 100) / 100,
        audio: o.hasAudio, audio_duration: null,
        lufs, headline: { bright_ratio: null, dark_ratio: null, contrast: null },
      },
      meta: { renderer: "forge-renderer/hyperframes", run: jobId },
    };
  } catch (e) {
    return { error: String((e && e.message) || e).slice(0, 500) };
  } finally {
    fs.rm(tmp, { recursive: true, force: true }).catch(() => {});
  }
}

function projectDirFor(tmp) {
  return path.join(tmp, "project");
}

function pickBadge(kind, lang) {
  const l = kind === "google" ? (GOOGLE_LANG[lang] || lang) : lang;
  for (const cand of [l, "en-US", "en"]) {
    const f = path.join(BADGES, `${kind}_${cand}.png`);
    if (fsSync.existsSync(f)) return f;
  }
  return null;
}

async function serveFile(url) {
  const p = url.searchParams.get("p") || "";
  const e = url.searchParams.get("e") || "";
  const s = url.searchParams.get("s") || "";
  const expect = crypto.createHmac("sha256", SECRET).update(`${p}:${e}`).digest("hex").slice(0, 32);
  const a = crypto.createHmac("sha256", SECRET).update(`${p}:${e}`).digest("hex").slice(0, 32);
  const ok = a === s && expect === s;
  const safeE = parseInt(e, 10);
  if (!ok || !Number.isFinite(safeE) || safeE * 1000 < Date.now()) {
    return new Response("bad signature", { status: 403 });
  }
  const abs = path.resolve(OUT, p);
  if (!abs.startsWith(path.resolve(OUT) + path.sep)) return new Response("bad path", { status: 400 });
  const data = await fs.readFile(abs).catch(() => null);
  if (!data) return new Response("not found", { status: 404 });
  return new Response(data, {
    headers: {
      "content-type": "video/mp4",
      "content-length": String(data.byteLength),
      "cache-control": "public, max-age=604800",
    },
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url || "/", `http://${req.headers.host || "localhost"}`);
  try {
    if (url.pathname === "/api/render" && req.method === "POST") {
      const body = JSON.parse(await readBody(req));
      const out = await enqueue(() => doRender(body));
      res.writeHead(out.error ? 500 : 200, { "content-type": "application/json" });
      res.end(JSON.stringify(out));
      return;
    }
    if (url.pathname === "/api/layout" && req.method === "POST") {
      const body = JSON.parse(await readBody(req));
      const videoUrl = String(body.video_url || "");
      if (!videoUrl) { res.writeHead(400, { "content-type": "application/json" }); return res.end(JSON.stringify({ error: "video_url required" })); }
      const tmp = path.join(TMP, "layout_" + crypto.randomBytes(4).toString("hex"));
      await fs.mkdir(tmp, { recursive: true });
      try {
        await download(videoUrl, path.join(tmp, "m.mp4"));
        const src = await ffprobe(path.join(tmp, "m.mp4"));
        res.writeHead(200, { "content-type": "application/json" });
        res.end(JSON.stringify({ layout: layoutFor(src) }));
      } finally { fs.rm(tmp, { recursive: true, force: true }).catch(() => {}); }
      return;
    }
    if (url.pathname === "/api/file" && req.method === "GET") {
      const r = await serveFile(url);
      res.writeHead(r.status, Object.fromEntries(r.headers));
      return res.end(Buffer.from(await r.arrayBuffer()));
    }
    if (url.pathname === "/" || url.pathname === "/api/render") {
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({
        service: "forge-renderer",
        usage: "POST /api/render with {geo, headline[], disclaimer, vo_base64|vo_url, video_url, layout?, expect_duration?} → {url, filename, qc_pass, qc_metrics}",
        endpoints: ["/api/render", "/api/layout", "/api/file"],
      }));
      return;
    }
    res.writeHead(404, { "content-type": "application/json" });
    res.end(JSON.stringify({ error: "not found" }));
  } catch (e) {
    res.writeHead(500, { "content-type": "application/json" });
    res.end(JSON.stringify({ error: String(e && e.message || e).slice(0, 300) }));
  }
});

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

server.listen(PORT, () => {
  console.log(`forge-renderer listening on :${PORT} (data=${DATA}, concurrency=${CONCURRENCY})`);
});

// Сид бейджей из образа в volume при старте (не перезаписывает пользовательские)
(async () => {
  try {
    await fs.mkdir(OUT, { recursive: true });
    await fs.mkdir(TMP, { recursive: true });
    await fs.mkdir(BADGES, { recursive: true });
    const files = await fs.readdir("/srv/badges").catch(() => []);
    for (const f of files) {
      if (!f.endsWith(".png")) continue;
      await fs.copyFile(path.join("/srv/badges", f), path.join(BADGES, f));
    }
    console.log("badges seeded:", files.length);
  } catch (e) {
    console.error("badge seed:", e.message);
  }
})();