#!/usr/bin/env bash
# Checkar in det klara: datakontrollerna, bara textfiler under data/ och
# versioner/, och en commit (K11, ADR-0088). Varje fel stoppar körningen;
# det som redan checkats in följer med i jobbets bundle. Jobbet kan inte
# pusha; det gör PR-jobbet (K95, ADR-0118).
# Användning: spara.sh <commit-meddelande>
set -euo pipefail
python -m kommunhandlingar.datakontroll data
git add -A
# Samma regel prövas igen i nattkorning-pr.yml, utanför det här jobbet (ADR-0115).
if git -c core.quotePath=false diff --cached --no-renames --name-only | grep -Ev '^(data|versioner)/'; then exit 1; fi
if git diff --cached --numstat | grep '^-'; then exit 1; fi
git diff --cached --quiet || git -c user.name="github-actions[bot]" \
  -c user.email="41898282+github-actions[bot]@users.noreply.github.com" \
  commit -q -m "$1"
