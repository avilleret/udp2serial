import socket,select,tty
import slip
import time
import serial
import platform
import glob

UDP_PORT_IN = 10000 # UDP server port
UDP_PORT_OUT = 11000
MAX_UDP_PACKET=4096 # max size of incoming packet to avoid sending too much data to the micro
plat = platform.system()
if plat == "Linux":
    SERIAL_PORT='/dev/ttyACM0'
elif plat == "Darwin":
    SERIAL_PORT=glob.glob("/dev/tty.usbmodem*")[0] # select the first available modem, please not we are no clue that this is a Teensy

BROADCAST_MODE=False #set to True if you want a broadcast replay instead of unicast


udp_client_address=('127.0.0.1',UDP_PORT_OUT) #where to forward packets coming from serial port
udp_server_address = ('',UDP_PORT_IN) #udp server
udp_broadcast=('<broadcast>',UDP_PORT_OUT) #broadcast address

#serial=open(SERIAL_PORT,'r+b') #open the file corrisponding to YUN serial port
serial = serial.Serial(
    port=SERIAL_PORT,
    baudrate=921600)

tty.setraw(serial) #this avoids the terminal to change bytes with value 10 in 13 10

udp_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
udp_socket.bind(udp_server_address)
if BROADCAST_MODE:
        udp_socket.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)

slip_processor=slip.slip()

while True:
        (rlist, wlist, xlist) = select.select([udp_socket,serial], [], [])
        if serial in rlist:
                serial_data = serial.read(1)
                slip_processor.append(serial_data)
                slip_packets=slip_processor.decode()
                for packet in slip_packets:
                        if BROADCAST_MODE:
                                udp_socket.sendto(packet,udp_broadcast)
                        else:
                                udp_socket.sendto(packet,udp_client_address)

        if udp_socket in rlist:
                udp_data,udp_client = udp_socket.recvfrom(MAX_UDP_PACKET)
                slip_data=slip_processor.encode(udp_data)
                serial.write(slip_data)
                serial.flush()
                udp_client_address=(udp_client[0],UDP_PORT_OUT)
                time.sleep(0.001) #avoid flooding the microcontroller (to be controlled)



