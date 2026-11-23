// Webbplatsens skript och deras tester (K83, ADR-0104): vanliga felkontroller
// plus gränserna i "Ren kod – strikt" i AGENTS.md, målen för skripten och de
// högre gränserna för testerna (K87, ADR-0108). Hur de körs står i
// docs/01-BIDRA.md.
import js from "@eslint/js";

const granser = ({ fil, funktion, parametrar, nastling, komplexitet }) => ({
  "max-lines": ["error", { max: fil }],
  "max-lines-per-function": ["error", { max: funktion }],
  "max-params": ["error", parametrar],
  "max-depth": ["error", nastling],
  complexity: ["error", komplexitet],
});

export default [
  { ignores: ["data/", "tests/fixtures/", "_site/"] },
  js.configs.recommended,
  {
    rules: granser({ fil: 150, funktion: 15, parametrar: 3, nastling: 2, komplexitet: 5 }),
  },
  {
    files: ["tests/**"],
    rules: granser({ fil: 250, funktion: 30, parametrar: 4, nastling: 3, komplexitet: 8 }),
  },
  {
    files: ["src/**/*.js"],
    languageOptions: {
      sourceType: "script",
      globals: {
        document: "readonly",
        window: "readonly",
        location: "readonly",
        history: "readonly",
        setTimeout: "readonly",
        URLSearchParams: "readonly",
      },
    },
  },
  {
    files: ["tests/**/*.mjs"],
    languageOptions: { globals: { URL: "readonly" } },
  },
];
