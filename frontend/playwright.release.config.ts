import { defineConfig } from "@playwright/test";
import liveConfig from "./playwright.live.config";

export default defineConfig({ ...liveConfig, testMatch: "release.spec.ts" });
