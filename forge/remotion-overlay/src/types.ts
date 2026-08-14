import type { HeadlineBox } from "./layout";

/** Props n8n / Forge already send to `POST /api/render`. */
export type OverlayProps = {
  geo: string;
  headline: string[];
  disclaimer: string;
  /** HTTPS URL or local path to the master mp4. */
  masterSrc: string;
  /** HTTPS URL or local path to TTS mp3. Empty = no voiceover (master stays muted). */
  voSrc: string;
  badgeAppleSrc: string;
  badgeGoogleSrc: string;
  durationInSeconds: number;
  headlineBox: HeadlineBox;
};

export const defaultOverlayProps: OverlayProps = {
  geo: "PL",
  headline: ["KRĘĆ I WYGRYWAJ", "GRAJ TERAZ"],
  disclaimer: "No purchase necessary to play. In-game rewards are not real money.",
  masterSrc: "",
  voSrc: "",
  badgeAppleSrc: "",
  badgeGoogleSrc: "",
  durationInSeconds: 15,
  headlineBox: { x: 162, y: 1056, w: 756, h: 422 },
};
