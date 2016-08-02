# !/usr/bin/python
import socket

header = \
    "ICY 200 OK\r\n" + \
    "Server: POP_GW_Ntrip_1.0_1467449209/1.0 \r\n" + \
    "Via: n4_2\r\n" + \
    "Date: 2016/07/25 17:36:28\r\n" + \
    "Connection: keep-alive\r\n\r\n"

HOST = '127.0.0.1'
PORT = 50007
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
ss, addr = s.accept()
inited = 0
print 'got connected from', addr
while 1:
    ra = ss.recv(1024)
    print ra
    if len(ra) > 20 and inited == 0:
        ss.send(header)
        inited = 1
ss.close()
