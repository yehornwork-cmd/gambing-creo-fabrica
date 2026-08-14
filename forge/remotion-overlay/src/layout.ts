/** Same geometry as forge-renderer `layoutFor` + `compositionHtml`. */

export const OUTPUT = { width: 1080, height: 1920, fps: 30 } as const;

export type HeadlineBox = { x: number; y: number; w: number; h: number };

export function defaultHeadlineBox(): HeadlineBox {
  const hw = Math.round(OUTPUT.width * 0.7);
  const hh = Math.round(OUTPUT.height * 0.22);
  return {
    x: Math.round((OUTPUT.width - hw) / 2),
    y: Math.round(OUTPUT.height * 0.55),
    w: hw,
    h: hh,
  };
}

export function headlineFontSize(headline: string[], box: HeadlineBox): number {
  const maxLen = Math.max(1, ...headline.map((s) => String(s || "").length));
  const fitW = Math.floor((box.w * 0.86) / (maxLen * 0.56));
  const fitH = Math.floor(box.h / 2.35);
  return Math.max(40, Math.min(fitW, fitH));
}

export function headlineLayout(headline: string[], box: HeadlineBox) {
  const fontSize = headlineFontSize(headline, box);
  const y1 = box.y;
  const y2 = box.y + Math.round(box.h * 0.54);
  return {
    fontSize,
    y1,
    y2,
    plateTop: y1 - 40,
    plateHeight: y2 - y1 + Math.round(fontSize * 1.15) + 80,
  };
}

export const CHROME = {
  stripBottom: 34,
  stripHeight: 536,
  badgesBottom: 40,
  badgeHeight: 110,
  badgeGap: 26,
  discBottom: 14,
  discFontSize: 22,
} as const;
