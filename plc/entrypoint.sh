#!/bin/sh
set -eu

DHCP_INTERFACE="${DHCP_INTERFACE:-eth0}"

configure_static_ip() {
  ip_cidr="${STATIC_IP_CIDR:-}"
  gateway="${STATIC_GATEWAY:-}"
  dns_server="${STATIC_DNS:-}"

  if [ "${STATIC_IP_PROMPT:-false}" = "true" ] && [ -t 0 ]; then
    echo "Static IP setup for ${DHCP_INTERFACE}"
    printf "IP address with CIDR, example 192.168.10.20/24. Leave blank to keep current address: "
    read -r ip_cidr
    if [ -n "${ip_cidr}" ]; then
      printf "Default gateway, optional: "
      read -r gateway
      printf "DNS server, optional: "
      read -r dns_server
    fi
  elif [ "${STATIC_IP_PROMPT:-false}" = "true" ]; then
    echo "STATIC_IP_PROMPT=true but stdin is not interactive; skipping prompt"
  fi

  if [ -n "${ip_cidr}" ]; then
    echo "Applying static IP ${ip_cidr} on ${DHCP_INTERFACE}"
    ip addr flush dev "${DHCP_INTERFACE}" || true
    ip addr add "${ip_cidr}" dev "${DHCP_INTERFACE}"
    ip link set "${DHCP_INTERFACE}" up
    if [ -n "${gateway}" ]; then
      ip route replace default via "${gateway}" dev "${DHCP_INTERFACE}"
    fi
    if [ -n "${dns_server}" ]; then
      printf "nameserver %s\n" "${dns_server}" > /etc/resolv.conf
    fi
    return 0
  fi

  return 1
}

if configure_static_ip; then
  echo "Static IP configuration complete"
elif [ "${DHCP_ENABLED:-true}" = "true" ]; then
  if ip -4 addr show "${DHCP_INTERFACE}" | grep -q "inet " && [ "${DHCP_FORCE:-false}" != "true" ]; then
    echo "Existing IPv4 address found on ${DHCP_INTERFACE}; set DHCP_FORCE=true to request a DHCP lease anyway"
  else
    echo "Requesting DHCP address on ${DHCP_INTERFACE}"
    timeout "${DHCP_TIMEOUT:-15}" dhclient -1 -v "${DHCP_INTERFACE}" || echo "DHCP request failed; continuing with existing address"
  fi
fi

ip -4 addr show "${DHCP_INTERFACE}" || true
exec "$@"
