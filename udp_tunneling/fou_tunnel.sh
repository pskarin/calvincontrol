ip=$(/sbin/ip -o -4 addr list eth0 | awk '{print $4}' | cut -d/ -f1)

echo "Opening a UDP tunnel between $ip:$1 <-> $2:$1 using the interface:$3 with ip:$4" 

modprobe fou
ip fou add port $1 ipproto 4
ip link add name $3 type ipip \
       remote $2 local $ip ttl 225 \
       encap fou \
       encap-sport auto encap-dport $1
ifconfig tunudp inet $4 netmask 255.255.255.0 up