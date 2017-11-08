#!/bin/bash

ip=$(/sbin/ip -o -4 addr list eth0 | awk '{print $4}' | cut -d/ -f1)

out_port=6000$1
in_port=6100$1
iface=rbs2ue$1
rbs_ip=130.235.202.183
tun_ip=10.0.0.10$1

echo "Opening a UDP tunnel to LuMaMi RBS for UE$1"
echo "$ip:$in_port <-> $rbs_ip:$out_port using the interface: $iface with ip:$tun_ip"

modprobe fou
ip fou add port $in_port ipproto 4
ip link add name $iface type ipip \
       remote $rbs_ip local $ip ttl 225 \
       encap fou \
       encap-sport auto encap-dport $out_port
ifconfig $iface inet $tun_ip netmask 255.255.255.0 up
