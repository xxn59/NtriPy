import serial
import socket
import time
import Queue

MOUNT_PT = "RTCM32_GGB"
# HOST = "120.76.233.44"
HOST = "10.81.0.39"
HOST = "127.0.0.1"
PORT = 50007
# SERIAL = '/dev/ttyUSB0'
SERIAL = 'com11'


class NtripServer:
    def __init__(self, request_handle=None, mount_point=MOUNT_PT, host=HOST, port=PORT):
        self.status = "init"
        self.connected = False
        self.target_caster = request_handle
        self.buf = ''
        self.lat = 0.0
        self.lon = 0.0
        self.alt = 0.0
        self.mount_point = mount_point
        self.connection = None
        self.remote = (host, port)
        self.q = Queue.Queue()

    def cache(self, dat):
        if self.q.qsize() > 20480:
            return
        self.q.put(dat)
        # self.buf += data
        # if len(self.buf) > 20480:
        #     self.buf = self.buf[-20480:-1]

    def get_data(self):
        # send_buff = self.buf
        # self.flush()
        # return send_buff
        if not self.q.empty():
            return self.q.get()

    def flush(self):
        self.buf = ''

    def connect(self):
        print "connecting to caster:", self.remote
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(self.remote)
        s.sendall(req_ntrip_source())
        print s.recv(1024)
        self.connection = s
        self.connected = True

    def shutdown(self):
        self.connection.close()
        pass


def req_ntrip_source():
    passwd = "123456"
    mount = "RTCM32_GGB"
    lat = "22.63901900"
    lon = "113.81104800"
    alt = "3.85"
    req = \
        "SOURCE {} /{}\r\n".format(passwd, mount) + \
        "Source-Agent: NTRIP pyCaster/0.1\r\n" + \
        "STR: lat {} lon {} alt {}\r\n\r\n".format(lat, lon, alt)
    return req


if __name__ == '__main__':
    f_log = open("ntrip_server.log", "wb")
    svr = NtripServer()
    svr.connect()
    # serial = serial.Serial(SERIAL, 115200)
    while True:
        # data = serial.read(1024)
        data = time.ctime()
        if len(data) > 0:
            print "sent {}bytes data to {}".format(len(data), svr.remote)
            # f_log.write(data)
            svr.connection.sendall(data)
            # time.sleep(1)
