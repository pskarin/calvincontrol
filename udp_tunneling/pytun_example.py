import binascii
import socket
import argparse
import threading

from pytun import TunTapDevice, IFF_TUN, IFF_NO_PI

OFFSET = 0

def main(args):
	
	tun = TunTapDevice(flags = (IFF_TUN|IFF_NO_PI))
	tun.addr 	= '10.0.1.2'
	#tun.dstaddr = '192.168.1.3'
	tun.netmask = '255.255.255.0'
	tun.mtu 	= 1500

	tun.persist(True)

	tun.up()
	s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	print "\n---- UDP tunneling ----"
	print " # iface: %s (%s)" % (tun.name, tun.addr)
	print " ->| %s:%i" % (args.out_ip, args.out_port)
	print " |<- %s:%i" % (args.in_ip, args.in_port)
	#print " S<- %s:%i" % (tun.addr, 9095)
	print "-----------------------\n"

	'''130.235.20
	Thread management 
	'''
	global active 
	active = True

	threads = []

	t_out 	= threading.Thread(target = outbound, args = (tun, args.out_ip, args.out_port, s1))
	threads.append(t_out)
	t_out.start()

	t_in 	= threading.Thread(target = inbound, args = (tun, args.in_ip, args.in_port, s2))
	threads.append(t_in)
	t_in.start()

	#t_srv 	= threading.Thread(target = server, args = (tun.addr, 9095))
	#threads.append(t_srv)
	#t_srv.start()

	while len(threads) > 0:
		try:
			# Join all threads using a timeout so it doesn't block
			# Filter out threads which have been joined or are None
			threads = [t.join(1000) for t in threads if t is not None and t.isAlive()]
		except KeyboardInterrupt:
			print " (!) Ctrl-c received! Killing threads..."

			active = False
			for t in threads:
				t.join()

			tun.down()
			print "\t - %s dismantled." % tun.name

def server(inet, port):

	soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	soc.bind((inet, port))
	soc.settimeout(2)

	i=1

	while active:
		try: 
			packet, addr = soc.recvfrom(1500) # buffer size is 1024 
		
			print "S<- packet %i (%i bytes) " % (i, len(packet)),
			print binascii.hexlify(packet),
			print addr

			i+=1
		except socket.timeout:
			pass

	soc.close()
	print "\t - S<- thread terminated "

def outbound(iface, out_ip, out_port, soc):

	while active:
		packet = iface.read(iface.mtu)
		ip_ver = int(binascii.hexlify(packet[OFFSET])[0])
		addr_src, addr_dst = packet[12+OFFSET:16+OFFSET], packet[16+OFFSET:20+OFFSET]

		soc.sendto(packet, (out_ip, out_port))

		# if ip_ver == 6:
		# 	print "->|X IPv%i (%i bytes)" % (ip_ver, len(packet))
		# elif ip_ver == 4:
		# 	print "->|O  IPv%i packet %i (%i bytes)" % (ip_ver, i, len(packet)),
		# 	print ", src: %s" % [int(binascii.hexlify(byte), 16) for byte in addr_src],
		# 	print ", dst: %s" % [int(binascii.hexlify(byte), 16) for byte in addr_dst]
		# 	#print binascii.hexlify(packet)

			

		# 	i+=1
		# else:
		# 	print "->|  Undefined packet: %s" % binascii.hexlify(packet)

	soc.close()
	print "\t - ->| thread terminated "

def inbound(iface, in_ip, in_port, soc):
	soc.bind((in_ip, in_port))
	soc.settimeout(2)

	while active:
		try: 
			packet, addr = soc.recvfrom(iface.mtu) # buffer size is 1024 
		
			# print "|<- packet %i (%i bytes) " % (i, len(packet)),
			# print binascii.hexlify(packet),
			# print addr

			iface.write(packet)

		except socket.timeout:
			#print " - T-OUT"
			pass

	soc.close()
	print "\t - |<- thread terminated "
	
if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', dest='in_ip', help="Input IP address for UDP tunnel", default='0.0.0.0')
	parser.add_argument('-p', dest='in_port', help="Input UDP port for UDP tunnel", default=9095, type=int)
	parser.add_argument('-o', dest='out_ip', help="Output IP address for UDP tunnel", default='130.235.201.4')
	parser.add_argument('-d', dest='out_port', help="Output UDP port for UDP tunnel", default=9093, type=int)
	args = parser.parse_args()
	main(args)