// Webbplatsens skript och deras tester (K83, ADR-0104): vanliga felkontroller
// plus de hårda gränserna i "Ren kod – strikt" i AGENTS.md. Målen, som är
// lägre, listas med eslint.mal.config.mjs. Hur de körs står i docs/01-BIDRA.md.
import js from "@eslint/js";

export const granser = ({ fil, funktion, parametrar, nastling, komplexitet }) => ({
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
