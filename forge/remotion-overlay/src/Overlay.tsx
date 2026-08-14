import { AbsoluteFill, Audio, OffthreadVideo } from "remotion";
import { CHROME, headlineLayout } from "./layout";
import type { OverlayProps } from "./types";

const SANS = "'Liberation Sans','Noto Sans',Helvetica,Arial,sans-serif";

function Headline({
  text,
  top,
  fontSize,
}: {
  text: string;
  top: number;
  fontSize: number;
}) {
  if (!text) return null;
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        top,
        width: 1080,
        textAlign: "center",
        color: "#fff",
        fontFamily: SANS,
        fontWeight: 800,
        fontSize,
        letterSpacing: 0.5,
        lineHeight: 1.15,
        whiteSpace: "nowrap",
        textShadow: "0 6px 24px rgba(0,0,0,0.95)",
      }}
    >
      {text}
    </div>
  );
}

export function Overlay({
  headline,
  disclaimer,
  masterSrc,
  voSrc,
  badgeAppleSrc,
  badgeGoogleSrc,
  headlineBox,
}: OverlayProps) {
  const lines = [headline[0] || "", headline[1] || ""];
  const box = headlineBox;
  const { fontSize, y1, y2, plateTop, plateHeight } = headlineLayout(lines, box);

  return (
    <AbsoluteFill style={{ backgroundColor: "#000", overflow: "hidden" }}>
      {masterSrc ? (
        <OffthreadVideo
          src={masterSrc}
          muted
          style={{
            position: "absolute",
            inset: 0,
            width: 1080,
            height: 1920,
            objectFit: "cover",
          }}
        />
      ) : (
        <AbsoluteFill style={{ backgroundColor: "#111" }} />
      )}

      <div
        style={{
          position: "absolute",
          left: 0,
          top: plateTop,
          width: 1080,
          height: plateHeight,
          backgroundColor: "#000",
        }}
      />
      <Headline text={lines[0]} top={y1} fontSize={fontSize} />
      <Headline text={lines[1]} top={y2} fontSize={fontSize} />

      <div
        style={{
          position: "absolute",
          left: 0,
          bottom: CHROME.stripBottom,
          width: 1080,
          height: CHROME.stripHeight,
          backgroundColor: "#000",
        }}
      />

      <div
        style={{
          position: "absolute",
          left: 0,
          bottom: CHROME.badgesBottom,
          width: 1080,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: CHROME.badgeGap,
        }}
      >
        {badgeAppleSrc ? (
          <img src={badgeAppleSrc} alt="" style={{ height: CHROME.badgeHeight }} />
        ) : null}
        {badgeGoogleSrc ? (
          <img src={badgeGoogleSrc} alt="" style={{ height: CHROME.badgeHeight }} />
        ) : null}
      </div>

      {disclaimer ? (
        <div
          style={{
            position: "absolute",
            left: 0,
            bottom: CHROME.discBottom,
            width: 1080,
            textAlign: "center",
            color: "rgba(255,255,255,0.88)",
            fontFamily: SANS,
            fontSize: CHROME.discFontSize,
          }}
        >
          {disclaimer}
        </div>
      ) : null}

      {voSrc ? <Audio src={voSrc} /> : null}
    </AbsoluteFill>
  );
}
