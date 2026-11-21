// Kör webbplatsens skript, som de står i src/, på en sida ur ögonblicksbilden
// av webbplatsen (K78) i jsdom (K83, ADR-0104). Sidans inbäddade kopia körs inte.
import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";

const ROT = new URL("../../", import.meta.url);
const BILD = new URL("tests/fixtures/webbplats/ogonblicksbild/exempelby/", ROT);
const SKRIPTEN = new URL("src/kommunhandlingar/webbplats/", ROT);

function frysKlockan(window, nu) {
  const Datum = window.Date;
  window.Date = function (...tid) {
    return new Datum(...(tid.length ? tid : [nu]));
  };
  window.Date.now = () => new Datum(nu).getTime();
}

// `fore` får ändra sidan innan skripten körs, för fall som bilden saknar.
export function sida(namn, { skript, adress = "", nu, fore }) {
  const { window } = new JSDOM(readFileSync(new URL(namn, BILD), "utf-8"), {
    url: new URL(namn + adress, "https://exempel.test/exempelby/").href,
    runScripts: "outside-only",
  });
  if (nu) frysKlockan(window, nu);
  if (fore) fore(window.document);
  skript.forEach((fil) => window.eval(readFileSync(new URL(fil, SKRIPTEN), "utf-8")));
  return window;
}

export function synliga(document, valjare) {
  return [...document.querySelectorAll(valjare)].filter((e) => !e.hidden);
}

// Väntar på sidans timrar och, om den ges, på en händelse som jsdom köar.
export async function vanta(window, handelse) {
  if (handelse) await new Promise((klar) => window.addEventListener(handelse, klar, { once: true }));
  await new Promise((klar) => window.setTimeout(klar, 10));
}
