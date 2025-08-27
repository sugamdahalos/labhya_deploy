#!/usr/bin/env bash
# deploy_tunnel_host.sh
# Usage: deploy_tunnel_host.sh "<AGENT_PUBKEY_LINE>" [BASE_PORT] [PORT_COUNT]
set -euo pipefail
AGENT_PUBKEY="$1"
BASE_PORT="${2:-22000}"
PORT_COUNT="${3:-1000}"
TUNNEL_USER="tunnel-user"

# create user if missing
if ! id -u "${TUNNEL_USER}" >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" "${TUNNEL_USER}"
fi
mkdir -p /home/${TUNNEL_USER}/.ssh
chown ${TUNNEL_USER}:${TUNNEL_USER} /home/${TUNNEL_USER}/.ssh
chmod 700 /home/${TUNNEL_USER}/.ssh

# append key if not present
AUTHORIZED="/home/${TUNNEL_USER}/.ssh/authorized_keys"
touch "${AUTHORIZED}"
# Use fixed-line match to avoid duplicates
if ! grep -qxF "${AGENT_PUBKEY}" "${AUTHORIZED}" 2>/dev/null; then
  echo "${AGENT_PUBKEY}" >> "${AUTHORIZED}"
fi
chown ${TUNNEL_USER}:${TUNNEL_USER} "${AUTHORIZED}"
chmod 600 "${AUTHORIZED}"

# backup sshd_config if not backed up
SSHD="/etc/ssh/sshd_config"
BACKUP="/etc/ssh/sshd_config.labhya.bak"
[ -f "${BACKUP}" ] || cp "${SSHD}" "${BACKUP}"

# enable GatewayPorts and AllowTcpForwarding
if ! grep -q '^GatewayPorts yes' "${SSHD}"; then
  sed -i "s/^#\?GatewayPorts.*/GatewayPorts yes/" "${SSHD}" || echo "GatewayPorts yes" >> "${SSHD}"
fi
if ! grep -q '^AllowTcpForwarding yes' "${SSHD}"; then
  sed -i "s/^#\?AllowTcpForwarding.*/AllowTcpForwarding yes/" "${SSHD}" || echo "AllowTcpForwarding yes" >> "${SSHD}"
fi

# restart sshd
if systemctl is-active --quiet sshd; then
  systemctl restart sshd
else
  service ssh restart || true
fi

# optional: configure ufw for the tunnel port range
if command -v ufw >/dev/null 2>&1; then
  ufw --force enable
  ufw allow OpenSSH
  # calculate end port
  END_PORT=$((BASE_PORT + PORT_COUNT - 1))
  ufw allow ${BASE_PORT}:${END_PORT}/tcp || true
fi

echo "DEPLOY_OK"
