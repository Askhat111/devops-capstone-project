#!/usr/bin/env bash
# Capture real command output for the capstone submission.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p evidence
nosetests -v --with-spec --spec-color --with-coverage --cover-package=service 2>&1 | tee evidence/security-headers-done.txt
coverage report --fail-under=95 | tee evidence/coverage.txt
make lint 2>&1 | tee evidence/lint.txt

capture() {
    local output=$1
    shift
    printf '%q ' "$@" > "evidence/$output.txt"
    printf '\n' >> "evidence/$output.txt"
    "$@" >> "evidence/$output.txt"
    cat "evidence/$output.txt"
}

base=${BASE_URL:-http://127.0.0.1:8080}
payload='{"name":"Example Customer","email":"customer@example.com","address":"Example Street 10","phone_number":"555-0100","date_joined":"2026-11-03"}'
capture rest-create-done curl -fsSi -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json' -X POST "$base/accounts" -d "$payload"
account_id=$(tail -n 1 evidence/rest-create-done.txt | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
capture rest-list-done curl -fsSi -H 'X-Forwarded-Proto: https' "$base/accounts"
capture rest-read-done curl -fsSi -H 'X-Forwarded-Proto: https' "$base/accounts/$account_id"
updated='{"name":"Updated Example Customer","email":"updated@example.com","address":"Example Street 20","phone_number":"555-0200","date_joined":"2026-11-03"}'
capture rest-update-done curl -fsSi -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json' -X PUT "$base/accounts/$account_id" -d "$updated"
capture rest-delete-done curl -fsSi -H 'X-Forwarded-Proto: https' -X DELETE "$base/accounts/$account_id"
curl -fsS -H 'X-Forwarded-Proto: https' "$base/" | tee evidence/kube-app-output.txt
docker images accounts --format 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedSince}}\t{{.Size}}' | tee evidence/kube-images.txt
