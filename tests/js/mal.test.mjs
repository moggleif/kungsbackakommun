// Krav: K83 (och K29, K35, K50) i docs/02-KRAV.md. Kör mal.js på målsidan
// (målen 0 Läsfrämjande, direktiv, och 1 Trygga miljöer, nämndmål, båda
// sist 2025) och initiativsidan i ögonblicksbilden.
import { test } from "node:test";
import assert from "node:assert/strict";
import { sida, synliga, vanta } from "./sida.mjs";

const SKRIPT = ["mal.js", "perspektiv.js"];
const malsida = (fore) => sida("fsn/mal-och-direktiv.html", { skript: SKRIPT, fore });
const valda = (d, valjare = "article[id]") => synliga(d, valjare).map((e) => e.dataset.mal);

function valj(window, urval) {
  window.document.querySelector(`.urval [data-urval="${urval}"]`).click();
  return window.document;
}

test("alla mål visas först, och knappen är nedtryckt", () => {
  const d = malsida().document;
  assert.deepEqual(valda(d).sort(), ["0", "1"]);
  assert.equal(d.querySelector('[data-urval="alla"]').getAttribute("aria-pressed"), "true");
  assert.equal(d.querySelector(".urval").hidden, false);
});

test("ett slag visar bara sina mål, i tidslinjen och bland korten", () => {
  const d = valj(malsida(), "nämndmål");
  assert.deepEqual(valda(d), ["1"]);
  assert.deepEqual(valda(d, "tr[data-mal]"), ["1"]);
  const aret = valda(d, "section.aret article");
  assert.ok(aret.length > 0 && aret.every((nr) => nr === "1"));
  assert.equal(d.querySelector('[data-urval="alla"]').getAttribute("aria-pressed"), "false");
});

test("aktiva är målen med sidans sista år, bytta har bytt formulering", () => {
  const fore = (dok) => {
    dok.querySelectorAll('[data-mal="0"]').forEach((m) => (m.dataset.sista = "2024"));
    dok.querySelectorAll('[data-mal="1"]').forEach((m) => (m.dataset.bytt = "ja"));
  };
  assert.deepEqual(valda(valj(malsida(fore), "aktiv")), ["1"]);
  assert.deepEqual(valda(valj(malsida(fore), "bytt")), ["1"]);
});

test("ett urval som inget mål har döljer alla kort", () => {
  const d = valj(sida("fsn/initiativ.html", { skript: ["mal.js"] }), "besvarat");
  assert.deepEqual(valda(d), []);
});

test("en rubrik i tidslinjen döljs när inget av dess mål visas", () => {
  const malsidan = valj(malsida(), "direktiv");
  const rubriker = synliga(malsidan, "tr.slag");
  assert.equal(rubriker.length, 1);
  assert.ok(rubriker[0].parentNode.querySelector('[data-mal="0"]'));
});

test("ett kommunmåls kort visas när ett av dess fokusområden visas", () => {
  const fore = (dok) => {
    const fokus = dok.createElement("div");
    fokus.className = "fokusomraden";
    fokus.append(dok.getElementById("mal-1"));
    dok.getElementById("mal-0").append(fokus);
  };
  const d = valj(malsida(fore), "nämndmål");
  assert.equal(d.getElementById("mal-0").hidden, false);
  assert.equal(d.getElementById("mal-1").hidden, false);
});

test("ett mål som väljs i tidslinjen öppnar kortets historik", async () => {
  const window = sida("fsn/initiativ.html", { skript: ["mal.js"] });
  const historik = window.document.querySelector("#sak-1 > details");
  const navigerad = vanta(window, "hashchange");
  window.document.querySelector('tr[data-mal="1"] a').click();
  await navigerad;
  assert.equal(historik.open, true);
  historik.open = false;
  window.document.querySelector('tr[data-mal="1"] a').click();
  await vanta(window);
  assert.equal(historik.open, true, "också när samma mål väljs igen");
});

test("en adress till ett kort öppnar dess historik", async () => {
  const window = sida("fsn/initiativ.html", { skript: ["mal.js"], adress: "#sak-0" });
  assert.equal(window.document.querySelector("#sak-0 > details").open, true);
  const navigerad = vanta(window, "hashchange");
  window.location.hash = "#sak-1";
  await navigerad;
  assert.equal(window.document.querySelector("#sak-1 > details").open, true);
});
