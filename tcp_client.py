import socket
import time

HOST = '127.0.0.1'
# HOST = '120.76.233.44'
PORT = 50007
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
while 1:
    # cmd = raw_input("Please input cmd:")
    cmd = "client now:%s" % time.ctime()
    s.sendall(cmd)
    try:
        data = s.recv(1024)
        print data
    except:
        pass
    time.sleep(1)

s.close()
