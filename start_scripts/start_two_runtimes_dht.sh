ip=$(/sbin/ip -o -4 addr list eth0 | awk '{print $4}' | cut -d/ -f1)

csruntime -n $ip -p 5000 -c 5001 --name 'rt1' --probe-buffer-size 500000 >> rt1_output.actortrace &
sleep 4
 
csruntime -n $ip -p 5002 -c 5003 --name 'rt2' --probe-buffer-size 500000 >> rt2_output.actortrace &
sleep 2

cscontrol http://$ip:5001 deploy ball_n_beam-sim-pid.calvin --reqs ball_n_beam-sim-pid.deployjson
sleep 3

echo "Started two runtimes {rt1, rt2} on host:$ip."
