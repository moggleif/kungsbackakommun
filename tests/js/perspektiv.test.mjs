// Krav: K83 (och K50) i docs/02-KRAV.md. Kör perspektiv.js, efter mal.js som
// på sidan, på målsidan i ögonblicksbilden: åren 2022–2026, förvalt 2025.
import { test } from "node:test";
import assert from "node:assert/strict";
import { sida, synliga, vanta } from "./sida.mjs";

const malsida = (adress) =>
  sida("fsn/mal-och-direktiv.html", { skript: ["mal.js", "perspektiv.js"], adress });

function lage(window) {
  const d = window.document;
  const tryckt = (grupp) => d.querySelector(`${grupp} [aria-pressed="true"]`).dataset;
  return {
    vy: synliga(d, "section[data-vy]").map((s) => s.dataset.vy).join(),
    ar: synliga(d, "section.aret").map((s) => s.dataset.ar).join(),
    knappar: `${tryckt(".perspektiv").vy} ${tryckt(".arval").ar}`,
    adress: window.location.search + window.location.hash,
  };
}

const klicka = (window, valjare) => window.document.querySelector(valjare).click();

test("utan val visas tidslinjen och det förvalda året", () => {
  const window = malsida();
  assert.deepEqual(lage(window), { vy: "tidslinje", ar: "2025", knappar: "tidslinje 2025", adress: "" });
  assert.equal(synliga(window.document, ".perspektiv, .arval").length, 2);
});

test("adressen väljer perspektiv och år", () => {
  assert.equal(lage(malsida("?vy=ar&ar=2023")).knappar, "ar 2023");
  assert.equal(lage(malsida("?vy=kort")).vy, "kort");
});

test("ett okänt val i adressen ger förvalet", () => {
  assert.equal(lage(malsida("?vy=okand&ar=1999")).knappar, "tidslinje 2025");
});

test("en adress till ett kort visar korten", () => {
  assert.equal(lage(malsida("#mal-1")).vy, "kort");
});

test("ett år som väljs läggs i adressen och historiken", async () => {
  const window = malsida();
  klicka(window, '.arval [data-ar="2024"]');
  assert.deepEqual(lage(window), { vy: "ar", ar: "2024", knappar: "ar 2024", adress: "?vy=ar&ar=2024" });
  klicka(window, '.perspektiv [data-vy="kort"]');
  assert.equal(lage(window).adress, "?vy=kort");
  const tillbaka = vanta(window, "popstate");
  window.history.back();
  await tillbaka;
  assert.equal(lage(window).knappar, "ar 2024");
});

test("det valda året står kvar när perspektivet byts", () => {
  const window = malsida("?vy=ar&ar=2023");
  klicka(window, '.perspektiv [data-vy="tidslinje"]');
  klicka(window, '.perspektiv [data-vy="ar"]');
  assert.equal(lage(window).adress, "?vy=ar&ar=2023");
});

test("ett mål som väljs i tidslinjen visar korten och hamnar i adressen", async () => {
  const window = malsida();
  const navigerad = vanta(window, "hashchange");
  klicka(window, 'tr[data-mal="1"] a');
  assert.equal(lage(window).vy, "kort", "redan i klickhanteraren");
  await navigerad;
  assert.equal(lage(window).adress, "?vy=kort#mal-1");
});
