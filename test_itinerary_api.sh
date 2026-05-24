#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"
CODE="40.7127,-74.006;10,45.4642,9.1896;1,46.4983,11.3548"

curl --silent --show-error --get \
  --data-urlencode "code=${CODE}" \
  "${BASE_URL}/api/itinerary"
