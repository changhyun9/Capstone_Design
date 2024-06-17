import json
import torch
import os
import socket
import cv2
import numpy
import base64
import glob
import sys
import time
import threading
from datetime import datetime
from ultralytics import YOLO

model = YOLO('./best.pt')

SERVER_IP = '10.43.24.186'
SERVER_PORT = 8080

RAS_IP = '192.169.0.203'
RAS_PORT = 2018

class Socket:

    def __init__(self, ip, port):
        self.TCP_IP = ip
        self.TCP_PORT = port

    def socketClose(self):
        self.sock.close()
        print(u'Server socket [ TCP_IP: ' + self.TCP_IP + ', TCP_PORT: ' + str(self.TCP_PORT) + ' ] is close')

    def socketOpen(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.sock.bind((self.TCP_IP, self.TCP_PORT))
        self.sock.listen(1)
        print(u'Server socket [ TCP_IP: ' + self.TCP_IP + ', TCP_PORT: ' + str(self.TCP_PORT) + ' ] is open')
        self.conn, self.addr = self.sock.accept()
        print(u'Server socket [ TCP_IP: ' + self.TCP_IP + ', TCP_PORT: ' + str(self.TCP_PORT) + ' ] is connected with client')

    def receiveImages(self):
        self.socketOpen()
        try:
            while True:
                length = self.recvall(self.conn, 64).decode('utf-8')
                stringData = self.recvall(self.conn, int(length))
                data = numpy.frombuffer(base64.b64decode(stringData), numpy.uint8)
                decimg = cv2.imdecode(data, 1)
                cv2.imwrite("saved_image.jpg", decimg)

                results = model.predict("./saved_image.jpg", show=False)

                for result in results:
                    cls = int(result.boxes.cls[0])
                    # cls = result.boxes.cls
                    if (cls == 0):
                        value = {"r": 255, "g": 0, "b": 0, "lx": 50}
                    elif (cls == 1):
                        value = {"r": 0, "g": 255, "b": 0, "lx": 50}
                    elif (cls == 2):
                        value = {"r": 0, "g": 0, "b": 255, "lx": 50}
                    else:
                        print("No class")
                        continue

                    # change format from dict to json
                    # create new thread for sending JSON data and start
                    json_data = json.dumps(value)
                    thread = threading.Thread(target=send_socket, args=(json_data,))
                    thread.start()

        except Exception as e:
            print(e)
            self.socketClose()
            # self.sockOpen()
            self.receiveThread = threading.Thread(target=self.receiveImages)
            self.receiveThread.start()

    def recvall(self, sock, count):
        buf = b''
        while count:
            newbuf = sock.recv(count)
            if not newbuf: return None
            buf += newbuf
            count -= len(newbuf)
        return buf

    def send_ras(self, data):
        # implementation by ChatGPT
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((RAS_IP, RAS_PORT))
            sock.send(data.encode())
            print("Complete sending")

# 1. Create Socket and Wait to connect client
# 2. Call method receiveImages() and predict image through model
# 3. Based on the predicted result, producing output
# 4. Create new thread and Send the result to Raspberry pi
def receive_jetson(self):
    server = Socket(SERVER_IP, SERVER_PORT)
    server.receiveImages()

# plan to develop in second semester
# def receive_application(self):

# 1. Create Socket and Connect to client (Raspberry pi)
# 2. Encode data JSON and send the result Raspberry pi
def send_socket(self, data):
    server = Socket(RAS_IP, RAS_PORT)
    server.send_ras(data)

def main():

    # For Jetson Nano (After receiving images from client, predict result through model and send to Raspberry pi)
    receive_socket = threading.Thread(target=receive_jetson)
    receive_socket.start()

    # For Application (After receiving Color temperature and Lux from client, send to Raspberry pi)
    # plan to develop in second semester

if __name__ == "__main__":
    main()
