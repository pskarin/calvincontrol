import subprocess as sp
import argparse
import json
import time
import re
import random as rnd
import atexit

RUNNING = True

def main(target_node_uris, unmigratable_names, unmigratable_types, inter_mig_dist, mig_scheme):
	nodes = map_nodes(target_node_uris)
	actors, unmig_actors = map_actors(nodes, unmigratable_names, unmigratable_types)

	assert len(actors) > 0, 'None of the resident actors are migratable'

	print '\n --- System symmary:'
	print '  Nbr. nodes: %i' % len(nodes)
	print '  Nbr. migratable actors: %i' % len(actors)
	print '  Nbr. unmigratable actors: %i' % len(unmig_actors)
	print ' -------------------\n'

	migrator(inter_mig_dist, actor_centric_mig_scheme(nodes=nodes, actors=actors), nodes, actors) # Stick into a thread

def migrator(inter_mig_dist, mig_scheme, nodes, actors):
	while RUNNING:
		# 1) Wait
		time.sleep( inter_mig_dist())

		# 2) Select target
		src_node_id, dest_node_id, actor_id = mig_scheme()

		print 'Migrating actor:%s from node:%s to node:%s ... ' % (
		actors[actor_id]['NAME'],
		nodes[src_node_id]['NAME'],
		nodes[dest_node_id]['NAME']),

		# 3) Migrate
		success = migrate_actor(nodes[src_node_id]['CTRL_URIS'], dest_node_id, actor_id)

		# 4) Update state
		if success:
			actors[actor_id]['CURRENT_NODE'] = dest_node_id
			print 'SUCCEEDED'
		else:
			print 'FAILED'

		# Debug
		time.sleep(1.)
		print_state(nodes=nodes, actors=actors)
		# src_node_uris = nodes[src_node_id]['CTRL_URIS']
		# dest_node_uris = nodes[src_node_id]['CTRL_URIS']
		# print "\t Present in (src:%s, dest:%s), is shadow: %s" % (
		# actor_present(src_node_uris, actor_id), actor_present(dest_node_uris, actor_id), is_actor_shadow(dest_node_uris, actor_id))

def on_exit():
	RUNNING = False

	# [TO-DO] Join thread etc.

	print 'Bye bye ...'

'''
Migration schemes
'''
def actor_centric_mig_scheme(nodes, actors):
	def func():
		target_actor_id = rnd.choice(actors.keys())
		actors_current_node_id = actors[target_actor_id]['CURRENT_NODE']

		dest_node_id = rnd.choice( list( set( nodes).difference( set([actors_current_node_id]))))

		return actors_current_node_id, dest_node_id, target_actor_id

	return func

'''
Explore functions
'''
def map_nodes(target_node_uris): # [TO-DO] Make recurive to ensure that we get all nodes when using local storage
	print 'Mapping nodes ... ',
	start = time.time()

	result = {}

	node_ids = [get_node_id(target_node_uris)] # Target node ID
	node_ids += get_peer_node_ids(target_node_uris) # Target node's peers IDs

	for node_id in node_ids:
		parameters = get_peer_node_info(target_node_uris, node_id)
		result.update({ node_id: {
			'NAME':parameters['attributes']['indexed_public'][0].split('/')[-1],
			'URIS':parameters['uris'][0],
			'CTRL_URIS':parameters['control_uris'][0]}
		})

	end = time.time()
	print 'DONE:%.2f s' % (end-start)

	return result

def map_actors(nodes, unmigratable_names=[], unmigratable_types=[]):
	print 'Mapping migratable actors ... ',
	start = time.time()

	mig_actors = {}
	unmig_actors = {}
	nbr_unmigratables = 0

	for node_id, parameters in nodes.iteritems():
		node_uris = parameters['CTRL_URIS']
		for actor_id in get_node_actors(node_uris):
			actor_info = get_actor_info(node_uris, actor_id)

			script_name = actor_info['name'].split(':')[0]
			actor_name = actor_info['name'].split(':')[1]
			actor_type = actor_info['type']
			actor_node_id = actor_info['node_id']

			if not any([re.match(exp, actor_name) for exp in unmigratable_names]) and not any([re.match(exp, actor_type) for exp in unmigratable_types]):
				#print 'Actor:%s, Type:%s - Migratable' % (actor_name, actor_type)
				mig_actors.update({ actor_id: {
					'NAME':actor_name,
					'SCRIPT':script_name,
					'TYPE':actor_type,
					'INIT_NODE':actor_node_id,
					'CURRENT_NODE':actor_node_id}
				})
			else:
				#print 'Actor:%s, Type:%s - Unmigratable' % (actor_name, actor_type)
				unmig_actors.update({ actor_id: {
					'NAME':actor_name,
					'SCRIPT':script_name,
					'TYPE':actor_type,
					'INIT_NODE':actor_node_id,
					'CURRENT_NODE':actor_node_id}
				})


	end = time.time()
	print 'DONE in %.2f s' % (end-start)

	return mig_actors, unmig_actors

'''
Read functions - [TO-DO] Throw 'node not reachable' exception when eval or json.loads fails
'''
def get_node_id(target_node_uris):
	return eval( sp.check_output(['cscontrol', target_node_uris, 'id']))

def get_peer_node_ids(target_node_uris):
	return eval( sp.check_output(['cscontrol', target_node_uris, 'nodes', 'list']))

def get_peer_node_info(target_node_uris, node_id):
	return json.loads( sp.check_output(['cscontrol', target_node_uris, 'nodes', 'info', node_id]))

def get_node_actors(target_node_uris):
	return eval( sp.check_output(['cscontrol', target_node_uris, 'actor', 'list']))

def get_actor_info(target_node_uris, actor_id):
	return json.loads(sp.check_output(['cscontrol', target_node_uris, 'actor', 'info', actor_id]))

def migrate_actor(source_node_uris, dest_node_id, actor_id):
	return sp.check_output(['cscontrol', source_node_uris, 'actor', 'migrate', actor_id, dest_node_id]) != 'Error HTTP'

def actor_present(target_node_uris, actor_id):
	actor_ids = get_node_actors(target_node_uris)
	return actor_id in actor_ids

def is_actor_shadow(target_node_uris, actor_id):
	actor_attr = get_actor_info(target_node_uris, actor_id)['is_shadow']
	return actor_attr == True

'''
Diagnostic functions
'''
def node_responsive(target_node_uris):
	return sp.check_output(['cscontrol', target_node_uris, 'nodes', 'list'])[:10] != 'Error HTTP'

def print_state(nodes, actors):
	for node_id, parameters in nodes.iteritems():
		node_uris = parameters['CTRL_URIS']
		node_name = parameters['NAME']
		print "Actors in node:%s" % node_name
		for actor_id in get_node_actors(node_uris):
			if actor_id in actors:
				print " - %s" % actors[actor_id]['NAME']

'''
Formatting functions
'''
def regex_compile_list(expr_list):
	return [re.compile(expr) for expr in expr_list]

def dist_factory(dist_name, kwargs, min_mig_time):
    result = None
    try:
        func = getattr(rnd, dist_name)
        func(**kwargs)

        def sample_dist():
            return max( func(**kwargs), min_mig_time)

        result = sample_dist
    except AttributeError:
        print '%s is not a supported distribution in random' % dist
        # TO-DO exit
    except TypeError:
        print 'Arguments: %s do not match the function rnd.%s' % (kwargs, dist_name)
        # TO-DO exit

    return result

def mig_policy_factory(mig_policy_name):
	return None

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-c',
		dest='uris',
		type=str,
		help='Control uris of initial target node',
		default='http://localhost:5001')
	parser.add_argument(
		'-n',
		dest='mig_name',
		nargs='+',
		type=str,
		help='Unmigratable actor names, RegEx',
		default=[])
	parser.add_argument(
		'-t',
		dest='mig_type',
		nargs='+',
		type=str,
		help='Unmigratable actor types, RegEx',
		default=[])
	parser.add_argument( # [TO-DO] Implement parent parser
		'-d',
		dest='dist',
		type=str,
		help='Inter-migration time distribution name from the package: random',
		default='gauss')
	parser.add_argument( # [TO-DO] Implement child parser for dist parameters
		'-k',
		dest='kwargs',
		type=json.loads,
		help='Dist ',
		default='{"mu":5.0, "sigma":1.0}')
	parser.add_argument(
		'-m',
		dest='min_mig_time',
		type=float,
		help='Minimum migration time',
		default=5.0)
	parser.add_argument(
		'-s',
		dest='scheme',
		type=str,
		help='Migration scheme',
		default='ACTOR_CENTRIC')

	args = parser.parse_args()

	atexit.register( on_exit)

	main(
		target_node_uris=args.uris,
		unmigratable_names=regex_compile_list(expr_list=args.mig_name),
		unmigratable_types=regex_compile_list(expr_list=args.mig_type),
		inter_mig_dist=dist_factory(dist_name=args.dist, kwargs=args.kwargs, min_mig_time=args.min_mig_time),
		mig_scheme=args.scheme)
