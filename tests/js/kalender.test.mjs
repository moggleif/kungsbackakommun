// Krav: K83 (och K22, K32) i docs/02-KRAV.md. Kör kalender.js på kalendern
// i ögonblicksbilden, med månaderna 2024-05–2027-01 och sammanträdena
// 2024-05-02 (FSN), 2026-12-05 (BUN, osäkert) och 2027-01-14 (FSN).
import { test } from "node:test";
import assert from "node:assert/strict";
import { sida, synliga } from "./sida.mjs";

const kalender = (nu) => sida("kalender.html", { skript: ["kalender.js"], nu }).document;
const manaden = (d) => synliga(d, ".manad").map((m) => m.dataset.manad);
const listan = (d) => synliga(d, "tr[data-datum]").map((r) => r.dataset.datum);
const knapp = (d, valjare) => d.querySelector(valjare);

test("innevarande månad visas, och listan från idag", () => {
  const d = kalender("2026-11-21T12:00:00");
  assert.deepEqual(manaden(d), ["2026-11"]);
  assert.deepEqual(listan(d), ["2026-12-05", "2027-01-14"]);
  assert.equal(synliga(d, ".listmanad").length, 2);
  assert.equal(synliga(d, ".alla, .tidigare, .blad").length, 3);
});

test("ensiffrig månad och dag räknas med två siffror", () => {
  const d = kalender("2027-01-05T12:00:00");
  assert.deepEqual(manaden(d), ["2027-01"]);
  assert.deepEqual(listan(d), ["2027-01-14"]);
});

test("dagens sammanträde står kvar i listan", () => {
  assert.deepEqual(listan(kalender("2026-12-05T23:00:00")), ["2026-12-05", "2027-01-14"]);
});

test("före första månaden visas den första, och bakåt går inte", () => {
  const d = kalender("2023-01-01T12:00:00");
  assert.deepEqual(manaden(d), ["2024-05"]);
  assert.equal(knapp(d, '[data-steg="-1"]').disabled, true);
  assert.equal(knapp(d, '[data-steg="1"]').disabled, false);
});

test("efter sista månaden visas den sista, och framåt går inte", () => {
  const d = kalender("2028-06-01T12:00:00");
  assert.deepEqual(manaden(d), ["2027-01"]);
  assert.equal(knapp(d, '[data-steg="1"]').disabled, true);
});

test("knapparna bläddrar en månad", () => {
  const d = kalender("2026-11-21T12:00:00");
  knapp(d, '[data-steg="1"]').click();
  assert.deepEqual(manaden(d), ["2026-12"]);
  knapp(d, '[data-steg="-1"]').click();
  knapp(d, '[data-steg="-1"]').click();
  assert.deepEqual(manaden(d), ["2026-10"]);
});

test("tidigare sammanträden visas och döljs med knappen", () => {
  const d = kalender("2026-11-21T12:00:00");
  const tidigare = knapp(d, ".tidigare button");
  tidigare.click();
  assert.deepEqual(listan(d), ["2024-05-02", "2026-12-05", "2027-01-14"]);
  assert.equal(tidigare.getAttribute("aria-expanded"), "true");
  assert.equal(tidigare.textContent, "Dölj tidigare sammanträden");
  tidigare.click();
  assert.deepEqual(listan(d), ["2026-12-05", "2027-01-14"]);
  assert.equal(tidigare.textContent, "Visa tidigare sammanträden");
});

test("ett organ som väljs bort döljs i månaden och listan", () => {
  const d = kalender("2026-11-21T12:00:00");
  const bun = knapp(d, '.urval input[data-organ="bun"]');
  bun.checked = false;
  bun.dispatchEvent(new d.defaultView.Event("change"));
  assert.deepEqual(listan(d), ["2027-01-14"]);
  assert.equal(synliga(d, ".listmanad").length, 1);
  assert.equal(synliga(d, '.manad [data-organ="bun"]').length, 0);
  assert.ok(synliga(d, '.manad [data-organ="fsn"]').length > 0);
  assert.equal(knapp(d, ".alla button").textContent, "Dölj alla");
});

test("knappen döljer alla organ och visar dem igen", () => {
  const d = kalender("2026-11-21T12:00:00");
  const alla = knapp(d, ".alla button");
  alla.click();
  assert.deepEqual(listan(d), []);
  assert.equal(alla.textContent, "Visa alla");
  alla.click();
  assert.deepEqual(listan(d), ["2026-12-05", "2027-01-14"]);
  assert.equal(alla.textContent, "Dölj alla");
});

test("länken till de osäkra datumen fäller ut kvaliteten", () => {
  const d = kalender("2026-11-21T12:00:00");
  knapp(d, 'a[href="#osakra"]').click();
  assert.equal(d.getElementById("kvalitet").open, true);
});

test("utan månader gör skriptet ingenting", () => {
  const d = sida("kalender.html", {
    skript: ["kalender.js"],
    fore: (dok) => dok.querySelectorAll(".manad").forEach((m) => m.remove()),
  }).document;
  assert.equal(synliga(d, ".alla, .tidigare, .blad").length, 0);
});
