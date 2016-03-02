# -*- coding: utf-8 -*-

import time
import socket
import struct
import sys
from threading import Thread

class MSG:
    RSP = 0
    LOGIN = 2
    PING = 6
    BRIDGE = 15
    HW = 20
    STATUS_OK = 200

    @staticmethod
    def tobuffer(*args):
        return "\0".join(map(str, args))

    @staticmethod
    def bufferto(buff):
        return (buff.decode('ascii')).split("\0")


class TCPClient(object):
    """

    """
    __Socket = None
    __count_msg_id = 0
    __time_last_rx = 0
    __lastToken = None
    __t_Ping = 5
    connected = False
    __hps = struct.Struct("!BHH")

    def __init__(self, server='cloud.blynk.cc', port=8442):
        self.__Server = server
        self.__Port = port

    def connect(self, timeout=3):
        """
        """
        print('Connected %s:%d' % (self.__Server, self.__Port))
        self.close()
        self.__count_msg_id = 0
        try:
            self.__Socket = socket.create_connection((self.__Server, self.__Port), timeout)
            self.__Socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            if self.__Socket:
                self.connected = True
                return self.__Socket
        except:
            print(sys.exc_info())
            self.connected = False
        return self.connected

    def close(self):
        if self.__Socket:
            self.__Socket.close()
            self.connected = False

    def tx(self, data):
        if self.__Socket:
            try:
                self.__Socket.sendall(data)
            except Exception:
                self.connected = False

    def rx(self, length):
        if self.__Socket:
            d = []
            l = 0
            while l < length:
                try:
                    out_read = self.__Socket.recv(length - l)
                    self.__time_last_rx = time.time()
                except socket.timeout:
                    return ''
                except Exception as e:
                    self.connected = False
                    return ''
                if not out_read:
                    self.connected = False
                    return ''
                d += out_read,
                l += len(out_read)
            ret = bytes()
            for cluster in d:
                ret = ret + cluster
            return ret

    def rxframe(self):
        response = self.rx(self.__hps.size)
        if response:
            return self.__hps.unpack(response)

    def txframe(self, msg_type, data):
        self.tx(self.__hps.pack(msg_type, self.newmsgid(), data))

    def txframedata(self, msg_type, data):
        self.tx(self.__hps.pack(msg_type, self.newmsgid(), len(data)) + data.encode())

    def newmsgid(self):
        self.__count_msg_id += 1
        return self.__count_msg_id

    def auth(self, token=None):
        if not token and self.__lastToken:
            token = self.__lastToken
        elif token:
            self.__lastToken = token
        else:
            return False

        self.txframe(MSG.LOGIN, len(token))
        self.tx(token.encode())
        response = self.rxframe()
        if response:
            msg_type, msg_id, msg_status = response
            if msg_status == MSG.STATUS_OK:
                print("Auth successfull")
                return True

    def ping(self):
        self.txframe(MSG.PING, 0)
        rx_frame = self.rxframe()
        if rx_frame and rx_frame[0] == MSG.RSP and rx_frame[1] == self.__count_msg_id and rx_frame[2] == MSG.STATUS_OK:
            return True

    def keepconnection(self):
        if not self.connected:
            if self.__connect() and self.auth():
                return True
            else:
                time.sleep(0.5)
                return False
        if (self.__time_last_rx + self.__t_Ping) < time.time():
            self.ping()


class Hardware(TCPClient):
    """

    """

    decoratefunc = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self):
        if self.connected:
            self.keepconnection()
            rx_frame = self.rxframe()
            if rx_frame:
                if (rx_frame[0] == MSG.HW) or (rx_frame[0] == MSG.BRIDGE):
                    data = self.rx(rx_frame[2])
                    params = MSG.bufferto(data)
                    cmd = params.pop(0)
                    self.onmsg(cmd, params)
                    self.txframe(MSG.RSP, MSG.STATUS_OK)
                else:
                    self._unknown(rx_frame[0], rx_frame[2])
        for func, func_array in self.decoratefunc.items():
            if 'timer' in func_array[1]:
                if len(func_array) == 2:
                    self.decoratefunc[func] = func_array + (time.time(), )
                if len(func_array) == 3: 
                    if func_array[2]+(func_array[1]['timer']/1000) < time.time():
                        Thread(target=self.decoratefunc[func][0], kwargs=self.decoratefunc[func][1]).start()
                        self.decoratefunc[func] = func_array[0:2] + (time.time(), )

    @staticmethod
    def _unknown(msg_type, data):
        print('Type = %d, data = ' % msg_type, data)

    def sendarray(self, arr):
        """
        """
        try:
            for name, pin_value in arr.items():
                for __p, __v in pin_value:
                    self.send(name, __p, __v)
        except:
            print(sys.exc_info()[1])

    def send(self, name='vw', pin=1, value=0):
        self.txframedata(MSG.HW,  MSG.tobuffer(name, pin, str(value)))

    def onmsg(self, cmd, params):
#        print('DEBUG: ', cmd, params)
        for func, func_array in self.decoratefunc.items():
            if 'name' in func_array[1] and 'pin' in func_array[1]:
                if func_array[1]['name'] == cmd and str(func_array[1]['pin']) == params[0]:
                    params.pop(0)
                    copy_args = self.decoratefunc[func][1]
                    if len(params) > 0:
                        copy_args.update({'value': params})
                    Thread(target=self.decoratefunc[func][0], kwargs=copy_args).start()


    def route(self, **kwargs):
        """
        """
        def my_shiny_new_decorator(a_function_to_decorate):
            old_kwargs = kwargs.copy()
            self.decoratefunc.update({a_function_to_decorate.__name__: (a_function_to_decorate, old_kwargs)})
        return my_shiny_new_decorator

    def timer(self, **kwargs):
        """
        """
        return self.route(**kwargs)

    def close(self):
        super().close()



