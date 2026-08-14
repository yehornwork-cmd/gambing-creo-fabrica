import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("png");
Config.setColorSpace("bt709");
Config.setOverwriteOutput(true);
// Lambda / burst workers override this; local preview stays light.
Config.setConcurrency(1);
