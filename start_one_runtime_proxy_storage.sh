rm rt2*

ip=$(/sbin/ip -o -4 addr list eth0 | awk '{print $4}' | cut -d/ -f1)

CALVIN_GLOBAL_STORAGE_TYPE=\"proxy\" CALVIN_GLOBAL_STORAGE_PROXY=\"calvinip://$1:5000\" csruntime -n $ip -p 5002 -c 5003 --name 'rt2' --probe-buffer-size 500000 >> rt2_output.actortrace &

echo "Started two runtimes {rt1, rt2} on host:$ip, with storage on rt1."
