#!/usr/bin/env python3
"""Apply Forge buyer-loop patches on the live /opt/forge tree."""

from __future__ import annotations

from pathlib import Path

APP = Path("/opt/forge/src/app/app")
OVERLAY = Path("/opt/forge/overlay-buyer")


SUBMIT_RUN = '''
export async function submitRun(
  user: SessionUser,
  input: { master_url: string; geos: string[]; product?: string; intent?: string; tone?: string },
): Promise<{ run: RunSummary; notice?: string }> {
  for (const g of input.geos) {
    if (!GEO_CODES.includes(g)) throw new ApiError("BAD_GEO");
  }
  if (input.master_url.startsWith("/media/")) {
    const base = (process.env.PUBLIC_ORIGIN || "https://forge.vizioner.xyz").replace(/\\/+$/, "");
    input.master_url = base + input.master_url;
  }
  assertSafeExternalUrl(input.master_url);

  const runId = uid();
  const t = nowIso();
  await db()
    .prepare(
      `INSERT INTO runs (id, user_id, master_url, geos, product, intent, tone, status, created_at)
       VALUES (?1,?2,?3,?4,?5,?6,?7,'running',?8)`,
    )
    .bind(runId, user.id, input.master_url, JSON.stringify(input.geos), input.product ?? "", input.intent ?? "", input.tone ?? "", t)
    .run();

  let analysis: Record<string, unknown> | null = null;
  let multiplyNotice = "";
  try {
    const plan = await triggerBuyerMultiply({
      master_url: input.master_url,
      geos: input.geos,
      product: input.product,
      intent: input.intent,
      tone: input.tone,
    });
    if (plan) {
      analysis = plan.analysis ?? null;
      const summary = (plan.summary ?? {}) as Record<string, unknown>;
      const multiply = {
        analysis_id: plan.analysis_id,
        jobs: summary.jobs ?? plan.jobs?.length ?? 0,
        job_ids: summary.job_ids,
        geos: summary.geos,
        ctas: summary.ctas,
        format: summary.format,
        duration_sec: summary.duration_sec,
        beats: summary.beats,
        deep_job_id: plan.deep_job_id ?? null,
        variants: plan.jobs,
      };
      await db()
        .prepare("UPDATE runs SET report_json=?1 WHERE id=?2")
        .bind(JSON.stringify({ analysis, multiply }), runId)
        .run();
      const beats = Array.isArray((analysis as { beats?: unknown[] } | null)?.beats)
        ? (analysis as { beats: unknown[] }).beats.length
        : 0;
      multiplyNotice = `Ролик разобран (${beats} битов, ${String(summary.format ?? "")}). План размножения: ${String(multiply.jobs)} вариантов. `;
    }
  } catch {
    multiplyNotice = "Разбор не успел за отведённое время — фабрика всё равно локализует мастер. ";
  }

  void triggerRun({
    master_url: input.master_url,
    geos: input.geos,
    product: input.product,
    intent: input.intent,
    tone: input.tone,
    analysis,
  })
    .then((res) => applyReportToRun(runId, user.id, input.product ?? "", res.report, res.link))
    .catch((e) => markRunFailed(runId, e));

  const row = await fetchRunRow(runId);
  return {
    run: runToSummary(row),
    notice:
      multiplyNotice +
      "Прогон рендера запущен. Обычно 30–60 секунд на 1–2 рынка — креативы появятся в библиотеке автоматически.",
  };
}
'''


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new.strip()[:40] in text and old not in text:
        print(f"skip {label} (already applied)")
        return
    if old not in text:
        raise SystemExit(f"{path}: marker missing for {label}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"patched {label}")


def main() -> int:
    factory_src = OVERLAY / "factory.server.ts"
    factory_dst = APP / "src/lib/factory.server.ts"
    factory_dst.write_text(factory_src.read_text(encoding="utf-8"), encoding="utf-8")
    print("copied factory.server.ts")

    data = APP / "src/lib/api/data.ts"
    text = data.read_text(encoding="utf-8")
    if "triggerBuyerMultiply" not in text:
        text = text.replace(
            "import { assertSafeExternalUrl, factoryKey, triggerRun } from \"../factory.server\";",
            "import { assertSafeExternalUrl, factoryKey, triggerBuyerMultiply, triggerRun } from \"../factory.server\";",
            1,
        )
    start = text.find("export async function submitRun(")
    end = text.find("// ---------- Библиотека ----------")
    if start < 0 or end < 0:
        raise SystemExit("submitRun block not found")
    text = text[:start] + SUBMIT_RUN.strip() + "\n\n" + text[end:]

    old_update = '''  const summary = `${report.готово ?? 0}/${(report.отсеяно ?? 0) + (report.готово ?? 0)}`;
  await db()
    .prepare("UPDATE runs SET status='done', report_json=?1, link=?2, error=NULL, summary=?3, finished_at=?4 WHERE id=?5")
    .bind(JSON.stringify(report), link, summary, nowIso(), runId)
    .run();'''
    new_update = '''  const prevRow = await db().prepare("SELECT report_json FROM runs WHERE id=?1").bind(runId).first();
  let prev: Record<string, unknown> = {};
  try {
    prev = prevRow?.report_json ? (JSON.parse(String(prevRow.report_json)) as Record<string, unknown>) : {};
  } catch {
    prev = {};
  }
  const merged = {
    ...report,
    analysis: report.analysis ?? prev.analysis ?? null,
    multiply: report.multiply ?? prev.multiply ?? null,
  };
  const summary = `${report.готово ?? 0}/${(report.отсеяно ?? 0) + (report.готово ?? 0)}`;
  await db()
    .prepare("UPDATE runs SET status='done', report_json=?1, link=?2, error=NULL, summary=?3, finished_at=?4 WHERE id=?5")
    .bind(JSON.stringify(merged), link, summary, nowIso(), runId)
    .run();'''
    if "report.analysis ?? prev.analysis" not in text:
        if old_update not in text:
            raise SystemExit("applyReportToRun update marker missing")
        text = text.replace(old_update, new_update, 1)
    data.write_text(text, encoding="utf-8")
    print("patched data.ts")

    types = APP / "src/lib/types.ts"
    t = types.read_text(encoding="utf-8")
    if "multiply?:" not in t:
        needle = "  отчёт_в_drive?: string | null;\n  время?: string;\n};"
        insert = """  отчёт_в_drive?: string | null;
  время?: string;
  analysis?: Record<string, unknown> | null;
  multiply?: {
    analysis_id?: string;
    jobs?: number;
    job_ids?: string[];
    geos?: string[];
    ctas?: string[];
    format?: string;
    duration_sec?: number;
    beats?: number;
    deep_job_id?: string | null;
    variants?: {
      job_id: string;
      geo?: string;
      locale?: string;
      cta_id?: string;
      format?: string;
      status?: string;
      cta_main?: string;
      disclaimer?: string;
    }[];
  } | null;
};"""
        if needle not in t:
            raise SystemExit("types RunReportShape marker missing")
        types.write_text(t.replace(needle, insert, 1), encoding="utf-8")
        print("patched types.ts")
    else:
        print("skip types.ts")

    gen = APP / "src/routes/app/generate.tsx"
    g = gen.read_text(encoding="utf-8")
    g = g.replace(
        "Новый прогон фабрики",
        "Загрузить и размножить",
        1,
    )
    g = g.replace(
        """          Фабрика берёт ваше мастер-видео и делает под каждый выбранный рынок лоукелизированную
          версию: утверждённый хук, озвучка, дисклеймер и QC-проверка. Хук и оффер она генерит
          сама на одобренных фразах рынка.""",
        """          Загрузите ролик-победитель. Фабрика сначала разберёт его (формат, длительность, биты),
          сразу покажет план размножения под выбранные рынки (локаль × CTA), затем локализует
          и отдаст готовые файлы.""",
        1,
    )
    g = g.replace(
        "mp4/webm до 150 МБ · загрузка станет доступна фабрике после публикации консоли; сейчас вставьте публичную ссылку",
        "mp4/webm до 150 МБ · файл сразу уходит на разбор и размножение",
        1,
    )
    g = g.replace(
        """              Прогон может занять несколько минут. Для быстрого синхронного ответа берите
              небольшое число рынков за раз; большие батчи уходят в работу и файлы публикуются в
              Google Drive.""",
        """              Разбор и план вариантов — за секунды. Рендер локализаций обычно 30–60 секунд
              на 1–2 рынка; большие батчи дописываются в библиотеку и Drive.""",
        1,
    )
    gen.write_text(g, encoding="utf-8")
    print("patched generate.tsx")

    result = APP / "src/components/run-result.tsx"
    r = result.read_text(encoding="utf-8")
    r = r.replace(
        'const RUN_PHASES = ["Мастер", "Локализация", "Рендер", "QA", "Финализация"];',
        'const RUN_PHASES = ["Разбор", "Размножение", "Рендер", "QA", "Финализация"];',
        1,
    )
    if "multiply?.variants" not in r:
        marker = "      <RunProgress status={run.status} ready={run.ready} failed={run.failed} />\n"
        extra = """      <RunProgress status={run.status} ready={run.ready} failed={run.failed} />
      {run.report?.multiply?.variants && run.report.multiply.variants.length > 0 && (
        <div className="border-t border-line px-4 py-3">
          <div className="text-xs text-t3">
            Разобрано · {run.report.multiply.beats ?? "—"} битов · {run.report.multiply.format} ·{" "}
            {run.report.multiply.jobs} вариантов
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {run.report.multiply.variants.slice(0, 12).map((v) => (
              <span key={v.job_id} className="rounded-full border border-line bg-ink2 px-2 py-0.5 text-[11px] text-t2">
                {v.geo} · {v.cta_main || v.cta_id}
              </span>
            ))}
          </div>
        </div>
      )}
"""
        if marker not in r:
            raise SystemExit("run-result marker missing")
        r = r.replace(marker, extra, 1)
    result.write_text(r, encoding="utf-8")
    print("patched run-result.tsx")

    compose = Path("/opt/forge/compose.yml")
    c = compose.read_text(encoding="utf-8")
    if "WORKER_URL" not in c:
        c = c.replace(
            "      N8N_FACTORY_KEY: ${FORGE_N8N_FACTORY_KEY}\n",
            "      N8N_FACTORY_KEY: ${FORGE_N8N_FACTORY_KEY}\n"
            "      WORKER_URL: ${WORKER_URL:-http://youtube-worker:8787}\n"
            "      WORKER_TOKEN: ${WORKER_TOKEN}\n",
            1,
        )
        compose.write_text(c, encoding="utf-8")
        print("patched compose.yml")
    else:
        print("skip compose.yml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
