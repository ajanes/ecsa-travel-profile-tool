#!/usr/bin/env bash
set -euo pipefail

REGISTRY_HOST="gitlab.inf.unibz.it:4567"
IMAGE_LOCAL="travel-profile-tool:latest"
IMAGE_REMOTE="$REGISTRY_HOST/andrea-janes/travel-profile-tool:latest"
PLATFORMS="linux/amd64"

if [[ -z "${GITLAB_TOKEN:-}" ]]; then
  echo "GITLAB_TOKEN is not set" >&2
  exit 1
fi

# Use a PAT with read_registry/write_registry scopes.
docker login "$REGISTRY_HOST" -u "andrea-janes" --password-stdin <<<"$GITLAB_TOKEN"

docker buildx create --use --name travel-profile-tool-builder >/dev/null 2>&1 || docker buildx use travel-profile-tool-builder
docker buildx build --platform "$PLATFORMS" -t "$IMAGE_REMOTE" --push .
