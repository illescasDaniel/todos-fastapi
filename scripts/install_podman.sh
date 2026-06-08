#!/usr/bin/env bash
# Install rootless Podman on CachyOS / Arch. Run from repo root; requires sudo once.
set -euo pipefail

if command -v podman >/dev/null 2>&1; then
	echo "podman already installed: $(podman --version)"
else
	echo "Installing podman and podman-compose (sudo required)..."
	sudo pacman -S --needed --noconfirm podman podman-compose
fi

if ! grep -q "^${USER}:" /etc/subuid 2>/dev/null; then
	echo "Configuring subuids for rootless Podman (sudo required)..."
	sudo usermod --add-subuids 100000-165535 --user "${USER}"
	sudo usermod --add-subgids 100000-165535 --user "${USER}"
	echo "Log out and back in (or reboot) so subuid/subgid mappings apply."
fi

systemctl --user enable --now podman.socket 2>/dev/null || true

echo ""
echo "Rootless Podman:"
podman info --format '  version: {{.Version.Version}}  rootless: {{.Host.Security.Rootless}}'

echo ""
echo "Next steps:"
echo "  Full stack:  ./scripts/container/up.sh   # profile from DATABASE_URL"
echo "  Stop stack:  ./scripts/container/down.sh"
echo "  Wipe volumes: ./scripts/wipe.sh"
echo "  Seed data:   ./scripts/seed.sh"
echo "  DB only + venv:         ./scripts/start.sh   # infra from docker-compose.infra.yml"
echo "  Infra only (manual):    podman compose -f docker-compose.infra.yml up -d valkey"
