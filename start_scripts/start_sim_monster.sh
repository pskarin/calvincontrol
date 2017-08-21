ip=$(/sbin/ip -o -4 addr list eth0 | awk '{print $4}' | cut -d/ -f1)

csruntime -n $ip -p 5000 -c 5001 --name 'rt1' --probe-buffer-size 500000 >> rt1_output.actortrace &
sleep 3

cscontrol http://$ip:5001 deploy ball_n_beam-sim-pid-calvinistic-monster.calvin
sleep 3

echo "Started one runtime {rt1} on host:$ip and deployed the monster"
