import { Composition, CalculateMetadataFunction } from "remotion";
import { Overlay } from "./Overlay";
import { OUTPUT, defaultHeadlineBox } from "./layout";
import { defaultOverlayProps, type OverlayProps } from "./types";

const calculateMetadata: CalculateMetadataFunction<OverlayProps> = ({ props }) => {
  const durationInSeconds = Math.max(1, Number(props.durationInSeconds) || 15);
  return {
    durationInFrames: Math.round(durationInSeconds * OUTPUT.fps),
    fps: OUTPUT.fps,
    width: OUTPUT.width,
    height: OUTPUT.height,
    props: {
      ...defaultOverlayProps,
      ...props,
      headline: Array.isArray(props.headline) ? props.headline : defaultOverlayProps.headline,
      headlineBox: props.headlineBox ?? defaultHeadlineBox(),
      durationInSeconds,
    },
  };
};

export const RemotionRoot = () => (
  <Composition
    id="Overlay"
    component={Overlay}
    durationInFrames={450}
    fps={OUTPUT.fps}
    width={OUTPUT.width}
    height={OUTPUT.height}
    defaultProps={defaultOverlayProps}
    calculateMetadata={calculateMetadata}
  />
);
