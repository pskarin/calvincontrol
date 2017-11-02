#!/bin/bash

ip=$(/sbin/ip -o -4 addr list eth0 | awk '{print $4}' | cut -d/ -f1)

declare -A hashmap
hashmap["USRP1"]=130.235.202.176

out_port=5000$1
in_port=5100$1
iface=ue${1}2rbs
rbs_ip=${hashmap[${2}]}
tun_ip=10.0.0.$1

echo "Opening a UDP tunnel to LuMaMi $2 for UE$1"
echo "$ip:$in_port <-> $rbs_ip:$out_port using the interface: $iface with ip:$tun_ip"

modprobe fou
ip fou add port $in_port ipproto 4
ip link add name $iface type ipip \
      remote $rbs_ip local $ip ttl 225 \
      encap fou \
      encap-sport auto encap-dport $out_port
ifconfig $iface inet $tun_ip netmask 255.255.255.0 up
