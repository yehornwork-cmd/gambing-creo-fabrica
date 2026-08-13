// Клиент фабрики (n8n webhook prod-run-7a7298) + buyer multiply (youtube-worker).
// Формат входа/выхода извлечён из воркфлоу «Фабрика креативов v3»:
//   вход:  { master_url, layout_url?, geos[], product?, intent?, tone?, analysis? }
//   выход: отчёт (готово/отсеяно/ссылки/прогон/отчёт_в_drive)
// Раскладка только на своём сервере: forge-renderer POST /api/layout.
// creative-localizer.vercel.app не используем.
// ВАЖНО: n8n-вебхук принимает заголовок ТОЛЬКО строчными буквами (x-agent-os-key).
import { bindings } from "./bindings.server";
import type { RunReportShape } from "./types";

export const N8N_FACTORY_URL = "https://n8n.vizioner.xyz/webhook/prod-run-7a7298";
const FETCH_TIMEOUT_MS = 15 * 60 * 1000;
const WORKER_TIMEOUT_MS = 45 * 1000;

export type SubmitRunInput = {
  master_url: string;
  geos: string[];
  product?: string;
  intent?: string;
  tone?: string;
};

export type BuyerMultiplyResult = {
  analysis_id: string;
  analysis: Record<string, unknown>;
  summary: Record<string, unknown>;
  jobs: Array<{
    job_id: string;
    geo?: string;
    locale?: string;
    cta_id?: string;
    format?: string;
    status?: string;
    cta_main?: string;
    disclaimer?: string;
    blocked_reason?: string | null;
  }>;
  deep_job_id?: string | null;
};

export function assertSafeExternalUrl(raw: string): void {
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    throw new Error("BAD_URL");
  }
  if (url.protocol !== "https:" && url.protocol !== "http:") throw new Error("BAD_URL");
  const host = url.hostname.toLowerCase();
  if (host === "localhost" || host.endsWith(".local")) throw new Error("BAD_URL");
  const blocked = [
    "127.",
    "10.",
    "192.168.",
    "172.16.",
    "172.17.",
    "172.18.",
    "172.19.",
    "172.2",
    "172.3",
    "169.254.",
    "0.",
    "[::1]",
    "[::]",
    "fc",
    "fd",
  ];
  // Internal docker hosts used by the worker allowlist are rewritten before this check.
  for (const p of blocked) {
    if (host.startsWith(p)) throw new Error("BAD_URL");
  }
}

export function factoryKey(): string | null {
  const env = bindings() as unknown as Record<string, string | undefined>;
  return env.N8N_FACTORY_KEY || null;
}

export function workerUrl(): string {
  const env = bindings() as unknown as Record<string, string | undefined>;
  return (env.WORKER_URL || "http://youtube-worker:8787").replace(/\/+$/, "");
}

export function workerToken(): string | null {
  const env = bindings() as unknown as Record<string, string | undefined>;
  return env.WORKER_TOKEN || null;
}

export async function triggerBuyerMultiply(input: SubmitRunInput): Promise<BuyerMultiplyResult | null> {
  const token = workerToken();
  if (!token) return null;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), WORKER_TIMEOUT_MS);
  try {
    const res = await fetch(`${workerUrl()}/jobs/buyer/multiply`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        source_url: input.master_url,
        geos: input.geos,
        product: input.product || "",
        deep_analyze: true,
      }),
      signal: controller.signal,
    });
    if (!res.ok) {
      throw Object.assign(new Error(`WORKER_HTTP_${res.status}`), { name: "WorkerError" });
    }
    return (await res.json()) as BuyerMultiplyResult;
  } finally {
    clearTimeout(timer);
  }
}

export async function triggerRun(
  input: SubmitRunInput & { analysis?: Record<string, unknown> | null },
): Promise<{ report: RunReportShape; link: string | null }> {
  const key = factoryKey();
  if (!key) throw Object.assign(new Error("FACTORY_NOT_CONFIGURED"), { name: "ConfigureError" });

  const body: Record<string, unknown> = {
    master_url: input.master_url,
    layout_url: input.master_url ? "" : undefined,
    geos: input.geos,
    product: input.product || undefined,
    intent: input.intent || undefined,
    tone: input.tone || undefined,
    analysis: input.analysis || undefined,
  };

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(N8N_FACTORY_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-agent-os-key": key },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    const text = await res.text();
    if (!res.ok) {
      throw Object.assign(new Error(`FACTORY_HTTP_${res.status}`), { name: "HttpError" });
    }
    let report: RunReportShape = {};
    try {
      report = JSON.parse(text) as RunReportShape;
    } catch {
      // отчёт может прийти не-JSON — оставляем пустой; статус по креативам возьмём позже
    }
    const link = report["отчёт_в_drive"] || null;
    return { report, link };
  } finally {
    clearTimeout(timer);
  }
}
