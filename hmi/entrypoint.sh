#!/bin/sh
set -eu

STATIC_INTERFACE="${STATIC_INTERFACE:-eth0}"

configure_static_ip() {
  ip_cidr="${STATIC_IP_CIDR:-}"
  gateway="${STATIC_GATEWAY:-}"
  dns_server="${STATIC_DNS:-}"

  if [ -t 0 ] && [ -z "${ip_cidr}" ]; then
    echo "Static IP setup for ${STATIC_INTERFACE}"
    printf "IP address with CIDR, example 192.168.10.40/24. Leave blank to keep current address: "
    read -r ip_cidr
    if [ -n "${ip_cidr}" ]; then
      printf "Default gateway, optional: "
      read -r gateway
      printf "DNS server, optional: "
      read -r dns_server
    fi
  elif [ -z "${ip_cidr}" ]; then
    echo "No static IP provided and stdin is not interactive; keeping current address"
  fi

  if [ -n "${ip_cidr}" ]; then
    echo "Applying static IP ${ip_cidr} on ${STATIC_INTERFACE}"
    ip link set "${STATIC_INTERFACE}" up || echo "Warning: could not bring ${STATIC_INTERFACE} up"
    ip addr replace "${ip_cidr}" dev "${STATIC_INTERFACE}" || echo "Warning: could not assign ${ip_cidr}; check NET_ADMIN/privileged settings"
    if [ -n "${gateway}" ]; then
      ip route replace default via "${gateway}" dev "${STATIC_INTERFACE}" || echo "Warning: could not set default gateway ${gateway}"
    fi
    if [ -n "${dns_server}" ]; then
      printf "nameserver %s\n" "${dns_server}" > /etc/resolv.conf || echo "Warning: could not update /etc/resolv.conf"
    fi
  fi
}

configure_static_ip
ip -4 addr show "${STATIC_INTERFACE}" || true
exec "$@"
