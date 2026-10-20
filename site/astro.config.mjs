// The documentation site of Vigil Alarm. The pages are not written here: `npm run sync` copies the guides from
// ../docs (and the ESPHome README and the changelog) into src/content/docs, so ../docs stays the one source.
import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

const REPO = "https://github.com/lightyearcoder/vigil-alarm";

export default defineConfig({
  site: "https://lightyearcoder.github.io",
  base: "/vigil-alarm",
  integrations: [
    starlight({
      title: "Vigil Alarm",
      favicon: "/favicon.png",
      customCss: ["./src/styles/vigil.css"],
      logo: { src: "./src/assets/logo.png", alt: "Vigil Alarm" },
      description: "A modular alarm system for Home Assistant: partitions, panels, tablets and a clear log.",
      defaultLocale: "root",
      locales: {
        root: { label: "English", lang: "en" },
        nl: { label: "Nederlands", lang: "nl" },
        de: { label: "Deutsch", lang: "de" },
        fr: { label: "Français", lang: "fr" },
        it: { label: "Italiano", lang: "it" },
        es: { label: "Español", lang: "es" },
      },
      social: [{ icon: "github", label: "GitHub", href: REPO }],
      sidebar: [
        { slug: "user-guide" },
        { slug: "tablet" },
        { slug: "troubleshooting" },
        { slug: "failure-behaviour" },
        { slug: "installation-and-testing" },
        { slug: "esphome-panel" },
        { slug: "changelog" },
      ],
    }),
  ],
});
