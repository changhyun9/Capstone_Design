import json
import torch
import os
import socket
import cv2
import numpy
import base64
import threading
from ultralytics import YOLO

model = YOLO('./best.pt')

SERVER_IP = '10.43.24.186'
SERVER_PORT = 8080

class Socket:
    def __init__(self, ip, port):
        self.TCP_IP = ip
        self.TCP_PORT = port
        self.sock = None
        self.socketOpen()

    def socketClose(self):
        if self.sock:
            self.sock.close()
            print(f'Server socket [ TCP_IP: {self.TCP_IP}, TCP_PORT: {self.TCP_PORT} ] is closed')

    def socketOpen(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.TCP_IP, self.TCP_PORT))
        self.sock.listen()
        print(f'Server socket [ TCP_IP: {self.TCP_IP}, TCP_PORT: {self.TCP_PORT} ] is open')

def receiveImages(conn):
    try:
        while True:
            # 길이 정보를 받아서 이미지 데이터 수신
            length = recvall(conn, 64)
            if not length:
                print("No length received, closing connection.")
                break
            length = int(length.decode('utf-8'))
            stringData = recvall(conn, length)
            data = numpy.frombuffer(base64.b64decode(stringData), numpy.uint8)
            decimg = cv2.imdecode(data, 1)
            cv2.imwrite("saved_image.jpg", decimg)

            # YOLO 모델을 사용해 예측
            results = model.predict("./saved_image.jpg", show=False)
            for result in results:
                cls = result.boxes.cls
                if cls == 0:
                    value = {"r": 255, "g": 255, "b": 0, "lx": 50, "cls": "Eating person"}
                elif cls == 1:
                    value = {"r": 204, "g": 0, "b": 0, "lx": 50, "cls": "Sleeping person"}
                elif cls == 2:
                    value = {"r": 51, "g": 0, "b": 255, "lx": 50, "cls": "Studying person"}
                else:
                    print("No class")
                    continue

                # JSON 데이터로 변환 후 전송
                json_data = json.dumps(value)
                conn.send(json_data.encode())  # 지속 연결이므로 동일한 conn을 사용해 전송

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()  # 연결 종료 시에만 소켓을 닫음
        print("Connection closed")

def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf:
            return None
        buf += newbuf
        count -= len(newbuf)
    return buf

def receive_jetson():
    server = Socket(SERVER_IP, SERVER_PORT)
    try:
        while True:
            conn, addr = server.sock.accept()
            print(f'Connected with {addr}')
            thread = threading.Thread(target=receiveImages, args=(conn,))
            thread.start()
    except Exception as e:
        print(e)
    finally:
        server.socketClose()

def main():
    receive_socket = threading.Thread(target=receive_jetson)
    receive_socket.start()

if __name__ == "__main__":
    main()
