import socket
import SocketServer
import time
import datetime
import Queue
from NTRIP_client import NtripClient
from NTRIP_server import NtripServer

HOST = "10.80.57.162"
PORT = 50007


rf = open("caster.log", "wb")

class RequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        print '...connected from:', self.client_address
        header = self.request.recv(1024).strip()
        header_info = decode_ntrip_header(header)
        print header_info
        if header_info is None:
            return
            # self.finish()

        if header_info[0] is 'server':
            ntrip_svr = NtripServer(self, header_info[1])
            caster.add_server(ntrip_svr)
            self.request.sendall("ICY 200 OK")
        elif header_info[0] is 'client':
            ntrip_clt = NtripClient(self, header_info[1], header_info[4])
            caster.add_client(ntrip_clt)
            self.request.sendall(get_client_resp().encode('ascii'))
        while True:
            if header_info[0] is 'server':
                data = self.request.recv(1024).strip()
                if data is not None:
                    ntrip_svr.cache(data)
                    caster.bytes_rcved += len(data)
                    print "received:{} sent:{}".format(caster.bytes_rcved, caster.bytes_sent)
                    # self.request.sendall('[%s] %s' % (time.ctime(), data))
                    # self.client_address
                    # print data
            elif header_info[0] is 'client':
                # print "here in a loop for client"
                # data = self.request.recv(1024).strip()
                # handle_ntrip_client_data(data)
                resp = ntrip_clt.get_data()
                # resp = rf.read(256)
                # print len(resp)
                if resp is not None:
                    # print "{}bytes sent to client".format(len(resp))
                    self.request.sendall(resp)
                    caster.bytes_sent += len(resp)
                    # time.sleep(0.2)
            else:
                pass


class NtripSvrHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        print '...connected from:', self.client_address
        header = self.request.recv(1024).strip()
        header_info = decode_ntrip_header(header)
        if header_info is None:
            return
        if header_info[0] is not 'server':
            return
        print header_info
        self.ntrip_svr = NtripServer(self, header_info[1])
        caster.add_server(self.ntrip_svr)
        self.wfile.write("ICY 200 OK")
        while True:
            data = self.rfile.read(256)
            if data is not None:
                # print "received:{} sent:{}".format(caster.bytes_rcved, caster.bytes_sent)
                self.ntrip_svr.cache(data)
                # rf.write(data)
                caster.bytes_rcved += len(data)

    def finish(self):
        caster.del_server(self.ntrip_svr)


class NtripCltHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        print '...connected from:', self.client_address
        header = self.request.recv(1024).strip()
        header_info = decode_ntrip_header(header)
        if header_info is None:
            return
        if header_info[0] is not 'client':
            return
        print header_info
        self.ntrip_clt = NtripClient(self, header_info[1], header_info[4])
        caster.add_client(self.ntrip_clt)
        self.request.sendall(get_client_resp().encode('ascii'))
        while True:
            # data = self.rfile.read(1024).strip()
            resp = self.ntrip_clt.get_data()
            if resp is not None:
                self.wfile.write(resp)
                caster.bytes_sent += len(resp)

    def finish(self):
        caster.del_client(self.ntrip_clt)
        print "client removed"

class AdminHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        print 'ADMIN port connected from', self.client_address
        header = self.request.recv(32).strip()
        if not verify_auth_info(header):
            return
        print header
        while True:
            info = "[{}]".format(time.ctime())
            info = "connected clients:{}, servers:{}\n".format(len(caster.clients), len(caster.servers))
            self.wfile.write(info)
            info = "received:{}, sent:{}\n".format(caster.bytes_rcved, caster.bytes_sent)
            self.wfile.write(info)
            time.sleep(1)



def verify_auth_info(header): # todo: verify the account and passphrase
    return True

def handle_ntrip_client_data(data):
    pass


def get_client_resp():
    timephr = datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S")
    ack = \
        "ICY 200 OK\r\n" + \
        "Server: POP_GW_Ntrip_1.0_1467449209/1.0\r\n".format(caster.name) + \
        "Via: n4_2\r\n" + \
        "Date: {}\r\n".format(timephr) + \
        "Connection: keep-alive\r\n\r\n"
    return ack


def decode_ntrip_header(buff):
    if "GET" in buff:
        role = 'client'

    elif "SOURCE" in buff:
        role = 'server'
    else:
        role = None

    if role is 'server':
        source = buff.split('\r\n')
        passwd = source[0].split(' ')[1]
        mount_point = source[0].split(' ')[2]
        agent = source[1].split(' ')[1]
        ext_str = source[2].split(' ')[1]
        return role, mount_point, passwd, agent, ext_str

    elif role is 'client':
        request = buff.split('\r\n')
        mount_point = request[0].split(' ')[1]
        agent = request[1].split(' ')[1]
        auth_type = request[2].split(' ')[1]
        auth_phrase = request[2].split(' ')[2]
        return role, mount_point, agent, auth_type, auth_phrase

    return None


class NtripCaster:
    def __init__(self, host="0.0.0.0", server_port=50007, client_port=50008, admin_port=51000, max_server=1, max_client=1,
                 name="C_DJI_NTRIP_1.0_2938"):
        self.running = False
        self.servers = []
        self.clients = []
        self.address_svr = (host, server_port)
        self.address_clt = (host, client_port)
        self.admin_address = (host, admin_port)
        self.max_server = max_server
        self.max_client = max_client
        self.svr_handle = None
        self.clt_handle = None
        self.name = name
        self.bytes_rcved = 0
        self.bytes_sent = 0

    def run_svr_handle(self):
        handle = SocketServer.ThreadingTCPServer(self.address_svr, NtripSvrHandler)
        print 'waiting for Ntrip servers...'
        self.svr_handle = handle
        handle.timeout = 0.5
        handle.allow_reuse_address = True
        handle.serve_forever()

    def run_clt_handle(self):
        handle = SocketServer.ThreadingTCPServer(self.address_clt, NtripCltHandler)
        print 'waiting for Ntrip clients...'
        self.clt_handle = handle
        handle.timeout = 10
        handle.allow_reuse_address = True
        handle.serve_forever()

    def run_admin_handle(self):
        svr = SocketServer.ThreadingTCPServer(self.admin_address, AdminHandler)
        print 'waiting for admin...'
        svr.timeout = 1
        svr.allow_reuse_address = True
        svr.serve_forever()

    def run_all(self):
        from threading import Thread

        t2 = Thread(target=self.run_svr_handle)
        t2.setDaemon(True)
        t2.start()

        self.running = True

        t1 = Thread(target=self.run_router)
        t1.setDaemon(True)
        t1.start()

        t3 = Thread(target=self.run_clt_handle)
        t3.setDaemon(True)
        t3.start()

        t4 = Thread(target=self.run_admin_handle)
        t4.setDaemon(True)
        t4.start()

    def run_router(self):
        while True:
            if not self.running:
                # svr.shutdown()
                # print "not running"
                break
            if len(self.clients) == 0:
                continue
            for s in self.servers:
                buff = ''
                trans = s.get_data()
                while trans is not None:
                    # print "[{}][{},{}]".format(time.ctime(),s.mount_point, c.mount_point)
                    # c.push_data(trans)
                    buff += trans
                    trans = s.get_data()

                if len(buff) == 0:
                    continue
                for c in self.clients:
                    if s.mount_point == c.mount_point:
                        c.push_data(buff)

    def stop(self):
        self.running = False

    def add_server(self, svr):
        if svr is not None:
            self.servers.append(svr)

    def del_server(self, svr):
        if svr in self.servers:
            self.servers.remove(svr)

    def add_client(self, clt):
        if clt is not None:
            self.clients.append(clt)

    def del_client(self, clt):
        if clt in self.clients:
            self.clients.remove(clt)

    def shutdown(self):
        self.running = False


if __name__ == '__main__':
    caster = NtripCaster()
    caster.run_all()
    while True:
        pass
