import matplotlib.pyplot as plt
import matplotlib.animation as animation
import socket
import time
import threading
import argparse

'''
Thread functions
'''
def main(addr, port):
	def plot(i):
		for plt_i in range(NBR_GRAPHS):

			data = DATA_BUFFERS[plt_i]

			if len(data[0]['Y']) > 0:
				#X_LIMS[plt_i] = [ min(X_LIMS[plt_i][0], data['X']), max(X_LIMS[plt_i][1], data['X']) ]
				#Y_LIMS[plt_i] = [ min( Y_LIMS[plt_i][0], min(data[0]['Y'])), max(Y_LIMS[plt_i][1], max(data['Y'])) ]

				AXES[plt_i].clear() 
				AXES[plt_i].set_title(TITLES[plt_i]) 
				AXES[plt_i].grid( True) 

				for mp_i in range(len(data)):
					AXES[plt_i].plot(data[mp_i]['X'][-WINDOW_SIZES[plt_i]:], data[mp_i]['Y'][-WINDOW_SIZES[plt_i]:], label=data[mp_i]['NAME'])
				
				AXES[plt_i].set_ylim(Y_LIMS[plt_i])
				AXES[plt_i].set_xlim(
					min( [min( data[mp_i]['X'][-WINDOW_SIZES[plt_i]:]) for mp_i in range( len( data))]), 
					max( [max( data[mp_i]['X'][-WINDOW_SIZES[plt_i]:]) for mp_i in range( len( data))])
					)

				AXES[plt_i].set_xlabel( X_LABELS[plt_i])
				AXES[plt_i].set_ylabel( Y_LABELS[plt_i])
				AXES[plt_i].legend(loc='upper left')

	def udp_receive():
		while True:
			data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes

			data = data.split(':')

			figure_i = int(data[0])
			plot_i = int(data[1])

			DATA_BUFFERS[ figure_i][ plot_i]['X'].append( float(data[2]) - init_time) # X
			DATA_BUFFERS[ figure_i][ plot_i]['Y'].append( float(data[3])) # Y

			#X_LIMS[plt_i] = [ min(X_LIMS[plt_i][0], data['X']), max(X_LIMS[plt_i][1], data['X']) ]

			Y_EXT_VALS[ figure_i] = [ min( Y_EXT_VALS[ figure_i][0], float( data[3])), max( Y_EXT_VALS[ figure_i][1], float( data[3])) ]
			Y_LIMS[ figure_i] = [ Y_EXT_VALS[ figure_i][0]*(1.25), Y_EXT_VALS[ figure_i][1]*(1.25)]

	'''
	Parameters
	'''
	# Graphs
	NBR_GRAPHS = 3

	TITLES = [ 'NO NAME' for i in range( NBR_GRAPHS)]
	X_LABELS = [ 'Time (s)' for i in range( NBR_GRAPHS)]
	Y_LABELS = [ 'Signal (V)' for i in range( NBR_GRAPHS)]

	X_LIMS = [ [0.,0.] for i in range( NBR_GRAPHS)]
	Y_EXT_VALS = [ [0.,0.] for i in range( NBR_GRAPHS)]
	Y_LIMS = [ [0.,0.] for i in range( NBR_GRAPHS)]

	#style.use('fivethirtyeight')
	fig = plt.figure()
	AXES = [ fig.add_subplot(NBR_GRAPHS, 1, i+1) for i in range(NBR_GRAPHS)]

	# Data
	DATA_BUFFERS = [
		[
			{'X':[], 'Y':[], 'NAME':'Error'}, 
		],
		[
			{'X':[], 'Y':[], 'NAME':'Controller output'}, 
		],
		[
			{'X':[], 'Y':[], 'NAME':'Position'}, 
			{'X':[], 'Y':[], 'NAME':'Set point'}
		],
		]

	WINDOW_SIZES = [5000 for i in range( len( DATA_BUFFERS))]

	'''
	Initialisations
	'''
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((addr, port))

	init_time = time.time()

	'''
	Strat threads
	'''
	print 'Start UDP listener',
	listen_UDP = threading.Thread(target=udp_receive)
	listen_UDP.start()
	print ' - DONE'

	print 'Start plotter',
	ani = animation.FuncAnimation(fig, plot, interval=100)
	plt.show()
	print '- DONE'

if __name__ == '__main__':
	import sys
	parser = argparse.ArgumentParser()

	parser.add_argument('-a', action='store', dest='addr',
					type=str, help='IP of local machine', default='0.0.0.0')
	parser.add_argument('-p', action='store', dest='port',
					type=str, help='Ingress data port', default=9090)

	results = parser.parse_args()

	main(addr = results.addr, port = results.port)
