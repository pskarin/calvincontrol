import subprocess as sp
import argparse
import json

def main(target_host_ip, target_host_port):
	discover_nodes(target_host_ip, target_host_port)

	print node_responsive(target_host_ip, target_host_port)
'''
Explore functions
'''
def discover_nodes(node_ip, node_port):
	nodes = {}
	peer_node_ids = get_peer_node_ids(node_ip, node_port)

	for node_id in peer_node_ids:
		print get_peer_node_info(node_ip, node_port, node_id)

'''
Read functions
'''
def get_peer_node_ids(node_ip, node_port):
	return eval( sp.check_output(['cscontrol', 'http://%s:%i' % (node_ip, node_port), 'nodes', 'list']))

def get_peer_node_info(node_ip, node_port, node_id):
	return json.loads( sp.check_output(['cscontrol', 'http://%s:%i' % (node_ip, node_port), 'nodes', 'info', node_id]))

'''
Diagnostic functions
'''
def node_responsive(node_ip, node_port):
	return sp.check_output(['cscontrol', 'http://%s:%i' % (node_ip, node_port), 'nodes', 'list'])[:10] != 'Error HTTP'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-i', 
        dest='ip', 
        type=str,
        help='IP address of initial target node')
    parser.add_argument(
        '-p', 
        dest='port', 
        type=int,
        help='TCP port address of initial target node')

    args = parser.parse_args()

    main(target_host_ip=args.ip, target_host_port=args.port)