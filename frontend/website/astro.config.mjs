import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";

export default defineConfig({
  site: "https://evidoc.hulkdesign.com",
  integrations: [tailwind()],
  i18n: {
    defaultLocale: "en",
    locales: [
      "en", "es", "fr", "de", "ja", "ko",
      "zh-cn", "zh-tw", "nl", "da", "pl", "pt", "th",
    ],
    routing: {
      prefixDefaultLocale: false,
    },
  },
});
