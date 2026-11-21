// Målen i "Ren kod – strikt" i AGENTS.md ovanpå de hårda gränserna (K83).
import grund, { granser } from "./eslint.config.mjs";

export default [
  ...grund,
  { rules: granser({ fil: 150, funktion: 15, parametrar: 3, nastling: 2, komplexitet: 5 }) },
];
