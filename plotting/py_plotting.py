import argparse
import csv
import matplotlib.pyplot as plt
from matplotlib import rc

# Temp 
import random as rnd
import numpy as np
import time

# Syntax: [time];[actor_name]:[action]:[function], e.g. 62;tiny:delay;trigger;passthrough

TIME_IDX  	= 0
ACTOR_IDX 	= 1
ACTION_IDX	= 2
FUNC_IDX  	= 3
VALUE_IDX 	= 4

DELIMINATOR = ';'

TIME_SCALE = 1./1000000.
TIME_UNIT = 's'

def produce(path):
	global data 
	data = read_data(path)
	#data = mock_data()

	fig, axes = plt.subplots(nrows=2, ncols=7)

	# plt_dist( [ ('ball_n_beam_pid:inner', 'evaluate'), ('ball_n_beam_pid:outer', 'evaluate')], axes[0])
	# plt_diff_ts( [ ('ball_n_beam_pid:inner', 'evaluate'), ('ball_n_beam_pid:outer', 'evaluate')], axes[1])
	# plt_ts( [ ('ball_n_beam_pid:inner', EXEC_T_LABEL), ('ball_n_beam_pid:outer', EXEC_T_LABEL)] , axes[2])

	plt_ctrl_ts( 
		[ ( ('both:actm', 'write'), 'DATA', 'Ang. vel.'), ( ('both:angm', 'trigger'), 'DATA', 'Angle'), ( ('both:posm', 'trigger'), 'DATA', 'Position')],
		[ ( ('both:mpc', 'setref'), 'DATA', 'Pos. set point')], 
		axes[0,0],		
		title='MPC',
		x_label='Time (%s)' % TIME_UNIT,
		y_label='Signal (V)',
		time_scale=TIME_SCALE)
	plt_ctrl_ts( 
		[ ( ('both:act', 'write'), 'DATA', 'Ang. vel.'), ( ('both:ang', 'trigger'), 'DATA', 'Angle'), ( ('both:pos', 'trigger'), 'DATA', 'Position')], 
		[ ( ('both:outer', 'evaluate'), 'DATA', 'Ang. set point'), ( ('both:outer', 'set_ref'), 'DATA', 'Pos. set point')], 
		axes[1,0],
		title='PID',
		x_label='Time (%s)' % TIME_UNIT,
		y_label='Signal (V)',
		time_scale=TIME_SCALE)

	plt_diff_ts( 
		[ ( ('both:posm', 'trigger'), 'EXEC'), (('both:angm', 'trigger'), 'EXEC'), (('both:mpc', 'action'), 'EXEC')], 
		axes[0,1],
		title='MPC - Period')
	plt_diff_ts( 
		[ ( ('both:pos', 'trigger'), 'EXEC'), (('both:ang', 'trigger'), 'EXEC'), (('both:outer', 'evaluate'), 'EXEC'), (('both:inner', 'evaluate'), 'EXEC')],
		axes[1,1],
		title='PID - Period')

	plt_dist( 
		[ ( ('both:posm', 'trigger'), 'EXEC'), (('both:angm', 'trigger'), 'EXEC'), (('both:mpc', 'action'), 'EXEC')], 
		axes[0,2],
		title='MPC - Period dist.')
	plt_dist( 
		[ ( ('both:pos', 'trigger'), 'EXEC'), (('both:ang', 'trigger'), 'EXEC'), (('both:outer', 'evaluate'), 'EXEC'), (('both:inner', 'evaluate'), 'EXEC')], 
		axes[1,2],
		title='PID - Period dist.')
	
	plt_rel_phase(
		[ ( ('both:posm', 'trigger'), 'EXEC'), (('both:angm', 'trigger'), 'EXEC'), (('both:mpc', 'action'), 'EXEC')], 
		axes[0,3])
	plt_rel_phase(
		[ ( ('both:pos', 'trigger'), 'EXEC'), (('both:ang', 'trigger'), 'EXEC'), (('both:outer', 'evaluate'), 'EXEC'), (('both:inner', 'evaluate'), 'EXEC')], 
		axes[1,3])

	plt_cum_drift(
		[ ( ('both:posm', 'trigger'), 'EXEC'), (('both:angm', 'trigger'), 'EXEC'), (('both:mpc', 'action'), 'EXEC')], 
		ref_period_set = [100000 for i in range(3)],
		ax = axes[0,4] )
	plt_cum_drift(
		[ ( ('both:pos', 'trigger'), 'EXEC'), (('both:ang', 'trigger'), 'EXEC'), (('both:outer', 'evaluate'), 'EXEC'), (('both:inner', 'evaluate'), 'EXEC')],
		ref_period_set = [77000 for i in range(4)],
		ax = axes[1,4] )

	plt_rel_phase(
		[ ( ('both:mpc', 'action'), 'EXEC'), (('both:outer', 'evaluate'), 'EXEC'), (('both:inner', 'evaluate'), 'EXEC')], 
		axes[0,5])

	plt_sys_error_ts(
		[ (('both:posm', 'trigger'), 'DATA', 'MPC'), (('both:pos', 'trigger'), 'DATA', 'PID')], 
		ref_target_set = [( ('both:mpc', 'setref'), 'DATA'), ( ('both:outer', 'set_ref'), 'DATA')],
		ax = axes[1,5],
		title='Error',
		x_label='Time (%s)' % TIME_UNIT,
		y_label='Error',
		time_scale=TIME_SCALE
		)

	plt_ts( 
		[ ( ('both:mpc', 'action'), 'DUR')], 
		axes[0,6],
		y_label='Execution time (\mu s)',
		title='MPC - Execution time')
	plt_ts( 
		[ (('both:outer', 'evaluate'), 'DUR'), (('both:inner', 'evaluate'), 'DUR')],
		axes[1,6],
		y_label='Execution time (\mu s)',
		title='PID - Execution time')


	#plt.tight_layout()
	plt.savefig('image_output.png', dpi=300, format='png')
	plt.show()
	
'''
Data plotting
'''
def plt_spect(mp_set, ax, title='Temporal spectal analysis', x_label='Frequency', y_label='Phase'):
	global data 

	ax.set_title(title)
	ax.set_xlabel(x_label)
	ax.set_ylabel(y_label)
	ax.grid(True)

	for mp in mp_set:
		target_data = data[ mp[0]][ mp[1]][ mp[2]]

		diff_tbl = np.array([])
		for i in range( len( target_data)): 
			np.concatenate( (diff_tbl, np.abs( np.subtract(target_data[i], target_data))) )

		ax.plot(diff_tbl, label='%s -> %s' % (mp[0], mp[1]))#, bins=1000, normed=1)

	ax.legend()

def plt_dist(mp_set, ax, title='', x_label='', y_label=''):
	global data

	ax.set_title(title)
	ax.set_xlabel(x_label)
	ax.set_ylabel(y_label)
	ax.grid(True)

	for mp in mp_set:
		target_data = data[ mp[0]][ mp[1]]

		label = '%s -> %s' % (mp[0][0], mp[0][1])
		if len(mp) >2:
			label = mp[2]

		ax.hist( np.diff(target_data), alpha=0.25, label=label)

	ax.legend()

def plt_diff_ts(mp_set, ax, title='', x_label='', y_label=''):
	global data 

	ax.set_title(title)
	ax.set_xlabel(x_label)
	ax.set_ylabel(y_label)
	ax.grid(True)

	for mp in mp_set:
		target_data = data[ mp[0]][ mp[1]]

		label = '%s -> %s' % (mp[0][0], mp[0][1])
		if len(mp) >2:
			label = mp[2]

		ax.plot( np.diff(target_data), label=label)

	ax.legend()

def plt_ts(mp_set, ax, title='', x_label='', y_label=''):
	global data 

	ax.set_title(title)
	ax.set_xlabel(x_label)
	ax.set_ylabel(y_label)
	ax.grid(True)

	for mp in mp_set:
		target_data = data[ mp[0]][ mp[1]]

		label = '%s -> %s' % (mp[0][0], mp[0][1])
		if len(mp) >2:
			label = mp[2]

		if len(target_data) == 2:
			ax.plot( target_data['TIME'], target_data['VALUE'], label=label)
		else:
			ax.plot( target_data, label=label)

	ax.legend()

def plt_ctrl_ts(mp_set, set_points, ax, title='', x_label='', y_label='', time_scale=1.0):
	global data 

	ax.set_title(title)
	ax.set_xlabel(x_label)
	ax.set_ylabel(y_label)
	ax.grid(True)
	ax.set_ylim([-10, 10])


	for mp in mp_set:
		target_data = data[ mp[0]][ mp[1]]

		label = '%s -> %s' % (mp[0][0], mp[0][1])
		if len(mp) >2:
			label = mp[2]

		ax.plot( np.multiply( np.subtract(target_data['TIME'], target_data['TIME'][0]), time_scale), target_data['VALUE'], label=label)

	for mp in set_points:
		target_data = data[ mp[0]][ mp[1]]

		label = '%s -> %s' % (mp[0][0], mp[0][1])
		if len(mp) >2:
			label = mp[2]

		ax.step( np.multiply( np.subtract(target_data['TIME'], target_data['TIME'][0]), time_scale), target_data['VALUE'], linestyle='dashed', label=label)

	ax.legend()

def plt_rel_phase(mp_set, ax, title='', x_label='', y_label=''):
	assert len(mp_set) >= 2, "1 actor function is not enough"

	ax.set_title(title)
	ax.set_xlabel(x_label)
	ax.set_ylabel(y_label)
	ax.grid(True)

	target_data = trim_for_min_phase(mp_set)

	for mp in mp_set[1:]:
		label = '%s -> %s' % (mp[0][0], mp[0][1])
		if len(mp) >2:
			label = mp[2]

		ax.plot( np.subtract( target_data[ mp_set[0][0]], target_data[ mp[0]]), label = label)

	ax.legend()

def plt_cum_drift(mp_set, ref_period_set, ax, title='', x_label='', y_label='Drift (%)'):
	assert len(mp_set) == len(ref_period_set), 'Numper of measurment points and reference phases are not the same'
	global data 

	ax.set_title(title)
	ax.set_xlabel(x_label)
	ax.set_ylabel(y_label)
	ax.grid(True)

	for mp_i in range( len( mp_set)):
		mp = mp_set[mp_i]

		target_data = data[ mp[0]][ mp[1]]

		label = '%s -> %s' % (mp[0][0], mp[0][1])
		if len(mp) >2:
			label = mp[2]

		ax.plot( np.cumsum( np.divide( np.subtract( np.diff(target_data), ref_period_set[ mp_i]), ref_period_set[ mp_i]*.01)), label=label)
		#ax.plot( np.cumsum( np.subtract( np.mean(target_data), np.diff(target_data))), label=label)

	ax.legend()

def plt_sys_error_ts(mp_set, ref_target_set, ax, title='', x_label='', y_label='', time_scale=1.):
	assert len( mp_set) == len( ref_target_set), 'Numper of measurment points and reference targets are not the same'
	global data 

	ax.set_title(title)
	ax.set_xlabel(x_label)
	ax.set_ylabel(y_label)
	ax.grid(True)

	err = []

	for mp_i in range( len( mp_set)):
		mp = mp_set[ mp_i]
		ref = ref_target_set[ mp_i]

		label = '%s -> %s' % ( mp[0][0], mp[0][1])
		if len(mp) >2:
			label = mp[2]

		err.append([])

		mp_ts = data[ mp[0]][ mp[1]][ 'TIME']
		mp_vals = data[ mp[0]][ mp[1]][ 'VALUE']

		ref_ts = data[ ref[0]][ ref[1]][ 'TIME']
		ref_vals = data[ ref[0]][ ref[1]][ 'VALUE']

		for i in range( len( mp_ts)):
			t = mp_ts[i]

			ref_idx = np.argmin(np.maximum(np.subtract( t, ref_ts),0))
			err[mp_i] .append( ref_vals[ ref_idx] - mp_vals[ i])


		ax.plot( np.multiply( np.subtract(mp_ts, mp_ts[0]), time_scale), err[mp_i], label=label)

	# Max set size
	max_i = np.argmax([len(arr) for arr in err])
	max_len = len( err[ max_i])

	for arr in err:
		arr += [0 for i in range(max_len - len(arr))]

	max_mp = mp_set[ max_i]
	max_mp_ts = data[ max_mp[0]][ max_mp[1]]['TIME']

	ax.plot( np.multiply( np.subtract(max_mp_ts, max_mp_ts[0]), time_scale), np.sum( np.abs( err), axis=0), label = 'Total')

	ax.legend()

'''
Support functions
'''
def trim_for_min_phase(mp_set):
	global data 

	target_data = {val[0] : data[ val[0]][ val[1]] for val in mp_set}

	# Correct phase
	# Find set with latest first recorded executiona 
	keys = target_data.keys()

	phase_ref_idx = np.fromiter( [target_data[key][0] for key in keys], np.int).argmax()
	phase_ref_key = keys[phase_ref_idx]

	min_t_idx = np.fromiter( [target_data[key][0] for key in keys], np.int).argmin()
	min_t = target_data[ keys[min_t_idx]][0]

	phase_ref_lenght = len(target_data[ phase_ref_key])
	assert phase_ref_lenght >= 2

	#print 'Ref: %s : %s' % (phase_ref_key, np.divide( np.subtract( target_data[ phase_ref_key][0:5], min_t),1.))

	for key in keys:

		#print '%s : %s' % (key, np.divide( np.subtract( target_data[ key][0:5], min_t),1.))

		eval_space = max( int(phase_ref_lenght/2), 2)

		i = np.argmin( 
			[np.sum( 
				np.abs( 
					np.subtract( 
						np.subtract(target_data[ key][i:eval_space+i], min_t), 
						np.subtract(target_data[ phase_ref_key][:eval_space], min_t) 
					)
				)
				)
			for i in range(10)])

		#print i

		del target_data[ key][:i]

	# Trim
	# Find set with latest first recorded execution
	min_len = min( [ len(val) for val in target_data.itervalues()])

	for val in target_data.itervalues(): 
		del val[min_len:]

	return target_data

def running_mean_fast(x, N):
    return np.convolve(x, np.ones((N,))/N, mode='valid')[(N-1):]

'''
Import data
'''
def mock_data():
	actors = {'ACT_1':['FUNC_A','FUNC_B'], 'ACT_2':['FUNC_C']}
	NBR_ENTRIES = 100
	t = time.time()

	dt = 0.01

	#timing_struct = { act:{ func: t + np.cumsum( rnd.sample( range(100, 10000), NBR_ENTRIES)) for func in funcs} for act, funcs in actors.iteritems()}
	big_struct = { act:{ func: t + 0.1*np.sin(4*np.pi*np.arange(0, int(NBR_ENTRIES*dt), dt)) for func in funcs} for act, funcs in actors.iteritems()}

	return big_struct

def read_data(path):
	big_struct = {}

	time_keeper = {}

	with open(path, 'rb') as csvfile:
		reader = csv.reader(csvfile, delimiter=DELIMINATOR, quoting=csv.QUOTE_NONE)

		for row in reader:
			actor = row[ ACTOR_IDX]
			func = row[ FUNC_IDX]

			# Make sure the dict is populated+
			if (actor, func) not in big_struct and func != '':
				big_struct[ (actor, func)] =  {'EXEC': [], 'DUR': [], 'DATA': {'TIME':[], 'VALUE': []}}
			if actor not in time_keeper:
				time_keeper[ actor] = {'TRIGGERED': False, 'FUNC_NAME': None, 'T_ENTER': None}

			# States
			if row[ ACTION_IDX] == 'enter':
				time_keeper[ actor][ 'T_ENTER'] = float(row[ TIME_IDX])

			elif row[ ACTION_IDX] == 'trigger':
				func = row[ FUNC_IDX]

				# EXEC
				big_struct[ (actor, func)]['EXEC'].append( float(row[ TIME_IDX]))

				# VALUE
				if row[ VALUE_IDX] is not '':
					big_struct[ (actor, func)][ 'DATA'][ 'TIME'].append( float(row[ TIME_IDX]))
					big_struct[ (actor, func)][ 'DATA'][ 'VALUE'].append( float(row[ VALUE_IDX]))

				time_keeper[ actor][ 'TRIGGERED'] = True
				time_keeper[ actor][ 'FUNC_NAME'] = func

			elif row[ ACTION_IDX] == 'exit' and time_keeper[ actor][ 'TRIGGERED']:
				big_struct[ (actor, time_keeper[ actor][ 'FUNC_NAME'])][ 'DUR'].append( float(row[ TIME_IDX]) - time_keeper[ actor][ 'T_ENTER'])

				time_keeper[ actor][ 'TRIGGERED'] = False
				time_keeper[ actor][ 'FUNC_NAME'] = None
				time_keeper[ actor][ 'T_ENTER'] = None

			# else:
			# 	print 'Unknown state!? - read_data(...)'

	print ' --- Collected actor function pairs ---'
	for (actor, func) in big_struct.keys():
		print '\t%s -> %s' % (actor, func)

	return big_struct

if __name__ == '__main__':
	import sys
	parser = argparse.ArgumentParser()

	parser.add_argument('-p', action='store', dest='path',
					type=str, help='Path to CSV file', default='calvin-both-100ms-piderr.log')

	results = parser.parse_args()

	produce(path = results.path)