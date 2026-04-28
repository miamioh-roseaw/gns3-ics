#!/bin/sh
set -eu

DHCP_INTERFACE="${DHCP_INTERFACE:-eth0}"

if [ "${DHCP_ENABLED:-true}" = "true" ]; then
  if ip -4 addr show "${DHCP_INTERFACE}" | grep -q "inet " && [ "${DHCP_FORCE:-false}" != "true" ]; then
    echo "Existing IPv4 address found on ${DHCP_INTERFACE}; set DHCP_FORCE=true to request a DHCP lease anyway"
  else
    echo "Requesting DHCP address on ${DHCP_INTERFACE}"
    timeout "${DHCP_TIMEOUT:-15}" dhclient -1 -v "${DHCP_INTERFACE}" || echo "DHCP request failed; continuing with existing address"
  fi
fi

ip -4 addr show "${DHCP_INTERFACE}" || true
exec "$@"
