import serial
import socket
import time
import Queue
from threading import Thread

MOUNT_PT = "RTCM32_GGB"
HOSTS = ["120.76.233.44",  # aliyun
         "119.29.114.47"]  # tencent

# HOST = "10.81.0.39"
# HOST = "127.0.0.1"
PORT = 50007
SERIAL = '/dev/ttyUSB0'


# SERIAL = 'com11'


class NtripServer:
    def __init__(self, request_handle=None, mount_point=MOUNT_PT, hosts=HOSTS, port=PORT):
        self.status = "init"
        self.connected = False
        self.target_caster = request_handle
        self.buf = ''
        self.lat = 0.0
        self.lon = 0.0
        self.alt = 0.0
        self.mount_point = mount_point
        self.connection = []
        self.hosts = hosts
        self.remote_port = port
        # self.remote = (host, port)
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

    def connect_all(self):
        for h in self.hosts:
            try:
                self.connect(h)
            except socket.error:
                pass

    def connect(self, host):
        print "connecting to caster:", host, self.remote_port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr = (host, self.remote_port)
        s.connect(addr)
        s.sendall(req_ntrip_source())
        print s.recv(1024)
        self.connection.append(s)
        self.connected = True

    def shutdown(self):
        for s in self.connection:
            s.close()

    def loop_send(self):

        while True:
            send_buf = self.get_data()
            if send_buf is None:
                continue
            for cnn in self.connection:
                try:
                    cnn.sendall(send_buf)
                except socket.error:
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


def start_sending_thread(t):
    from threading import Thread

    t = Thread(target=t)
    t.setDaemon(True)
    t.start()

if __name__ == '__main__':
    f_log = open("ntrip_server.log", "wb")
    svr = NtripServer()
    svr.connect_all()
    s = serial.Serial(SERIAL, 115200, timeout=0.1)
    start_sending_thread(svr.loop_send)
    while True:
        data = s.read(256)
        # data = time.ctime()
        if len(data) > 0:
            print "sent {}bytes data to {}".format(len(data), HOSTS)
            svr.cache(data)
            # f_log.write(data)
            # sc.sendall(data)
            # time.sleep(1)
