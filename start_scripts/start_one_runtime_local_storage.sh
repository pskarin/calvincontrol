ip=$(/sbin/ip -o -4 addr list eth0 | awk '{print $4}' | cut -d/ -f1)

echo $ip

CALVIN_GLOBAL_STORAGE_TYPE=\"local\" csruntime -n $ip -p 5000 -c 5001 --name 'rt1' --probe-buffer-size 2000000 >> rt1_output.actortrace &

echo "Started one runtime {rt1} on host:$ip, with local storage."
