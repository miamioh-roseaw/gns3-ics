#!/bin/sh
set -eu

STATIC_INTERFACE="${STATIC_INTERFACE:-eth0}"

configure_static_ip() {
  ip_cidr="${STATIC_IP_CIDR:-}"
  gateway="${STATIC_GATEWAY:-}"
  dns_server="${STATIC_DNS:-}"
  dns_name="${STATIC_DNS_NAME:-${DEVICE_DNS_NAME:-}}"

  if [ -t 0 ] && [ -z "${ip_cidr}" ] && [ -z "${dns_name}" ]; then
    echo "Static IP setup for ${STATIC_INTERFACE}"
    printf "IP address with CIDR, example 192.168.10.30/24. Leave blank to keep current address: "
    read -r ip_cidr
    if [ -n "${ip_cidr}" ]; then
      printf "Default gateway, optional: "
      read -r gateway
      printf "DNS server, optional: "
      read -r dns_server
    fi
    printf "Device DNS name / hostname, optional: "
    read -r dns_name
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

  if [ -n "${dns_name}" ]; then
    ip_address="$(printf "%s" "${ip_cidr}" | cut -d/ -f1)"
    if [ -z "${ip_address}" ]; then
      ip_address="$(ip -4 -o addr show "${STATIC_INTERFACE}" | awk '{split($4, address, "/"); print address[1]; exit}' || true)"
    fi
    short_name="$(printf "%s" "${dns_name}" | cut -d. -f1)"
    echo "Applying device DNS name ${dns_name}"
    printf "%s\n" "${short_name}" > /etc/hostname || echo "Warning: could not update /etc/hostname"
    hostname "${short_name}" || echo "Warning: could not set runtime hostname"
    if [ -n "${ip_address}" ]; then
      printf "%s %s %s\n" "${ip_address}" "${dns_name}" "${short_name}" >> /etc/hosts || echo "Warning: could not update /etc/hosts"
    fi
  fi
}

configure_static_ip
ip -4 addr show "${STATIC_INTERFACE}" || true
current_ip="$(ip -4 -o addr show "${STATIC_INTERFACE}" | awk '{split($4, address, "/"); print address[1]; exit}' || true)"
if [ -n "${current_ip}" ] && [ -n "${SERVICE_PORT:-}" ]; then
  echo "${SERVICE_NAME:-Service} available at http://${current_ip}:${SERVICE_PORT}"
fi
exec "$@"
