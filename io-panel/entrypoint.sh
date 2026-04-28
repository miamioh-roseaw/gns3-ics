#!/bin/sh
set -eu

DHCP_INTERFACE="${DHCP_INTERFACE:-eth0}"

if [ "${DHCP_ENABLED:-true}" = "true" ]; then
  echo "Requesting DHCP address on ${DHCP_INTERFACE}"
  timeout "${DHCP_TIMEOUT:-15}" dhclient -1 -v "${DHCP_INTERFACE}" || echo "DHCP request failed; continuing with existing address"
fi

ip -4 addr show "${DHCP_INTERFACE}" || true
exec "$@"
