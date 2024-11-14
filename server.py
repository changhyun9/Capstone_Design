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
from cyclegan_turbo import CycleGAN_Turbo

#Load CycleGAN to memory 
cyclegan_model = CycleGAN_Turbo(pretrained_name="night_to_day")
cyclegan_model.eval()  # 평가 모드 설정
cyclegan_model.unet.enable_xformers_memory_efficient_attention()

model = YOLO('./best.pt')

clients = []

SERVER_IP = '175.45.194.40'
SERVER_PORT = 8080

class Socket:

    def __init__(self, ip, port):
        self.TCP_IP = ip
        self.TCP_PORT = port
        self.sock = None
        self.socketOpen()

    def socketClose(self):
        self.sock.close()
        print(u'Server socket [ TCP_IP: ' + self.TCP_IP + ', TCP_PORT: ' + str(self.TCP_PORT) + ' ] is close')

    def socketOpen(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.sock.bind((self.TCP_IP, self.TCP_PORT))
        self.sock.listen()
        print(u'Server socket [ TCP_IP: ' + self.TCP_IP + ', TCP_PORT: ' + str(self.TCP_PORT) + ' ] is open')


def is_low_light(image, threshold=50):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mean_brightness = gray.mean()
    return mean_brightness < threshold

def receiveImages(conn):
    try:
        while True:
            length = recvall(conn, 64).decode('utf-8')
            if length is None:
                break
            stringData = recvall(conn, int(length))
            data = numpy.frombuffer(base64.b64decode(stringData), numpy.uint8)
            decimg = cv2.imdecode(data, 1)
            cv2.imwrite("saved_image.jpg", decimg)
            
            if is_low_light("saved_image.jpg", 50):
            	#CycleGan code
            	print("Low light detected. Enhancing brightness with CycleGAN.")

                # CycleGAN 변환
                decimg = enhance_brightness_with_cyclegan(decimg)

            results = model.predict("./saved_image.jpg", show=False)

            for result in results:
                cls = result.boxes.cls
                if (cls == 0):
                    value = {"r": 255, "g": 255, "b": 0, "lx": 50, "cls": "Eating person"}
                elif (cls == 2):
                    value = {"r": 204, "g": 0, "b": 0, "lx": 50, "cls": "Sleeping person"}
                elif (cls == 3):
                    value = {"r": 51, "g": 0, "b": 255, "lx": 50, "cls": "Studying person"}
                else:
                    print("No class")
                    continue

                # change format from dict to json
                # create new thread for sending JSON data and start
                json_data = json.dumps(value)
                send_socket(json_data, conn)

    except Exception as e:
        print(e)
    finally:
        clients.remove(conn)
        conn.close()

def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf

# 1. Encode data JSON and send the result Raspberry pi
def send_socket(data, sender_conn):
    for client in clients:
        if client != sender_conn:
            print("Send results to Raspberry")
            client.send(data.encode())


# 1. Create Socket and Wait to connect client
# 2. Call method receiveImages() and predict image through model
# 3. Based on the predicted result, producing output
# 4. Create new thread and Send the result to Raspberry pi
def receive_jetson():
    server = Socket(SERVER_IP, SERVER_PORT)
    try:
        while True:
            conn, addr = server.sock.accept()
            print(f'Server socket is connected with {addr}')
            clients.append(conn)
            thread = threading.Thread(target=receiveImages, args=(conn,))
            thread.start()
    except Exception as e:
        print(e)
    finally:
        server.socketClose()
        
def enhance_brightness_with_cyclegan(image):
    # 이미지 전처리
    transform = transforms.Compose([
        transforms.Resize((512, 512)),
        transforms.ToTensor(),
        transforms.Normalize([0.5], [0.5])
    ])
    input_img = transform(image).unsqueeze(0).cuda()

    # CycleGAN 모델을 사용해 밝기 변환
    with torch.no_grad():
        output = cyclegan_model(input_img)
        output_img = output[0].cpu() * 0.5 + 0.5
        output_img = transforms.ToPILImage()(output_img).resize((image.shape[1], image.shape[0]))

    return numpy.array(output_img)


# plan to develop in second semester
# def receive_application(self):

def main():

    # For Jetson Nano (After receiving images from client, predict result through model and send to Raspberry pi)
    receive_socket = threading.Thread(target=receive_jetson)
    receive_socket.start()

    # For Application (After receiving Color temperature and Lux from client, send to Raspberry pi)
    # plan to develop in second semester

if __name__ == "__main__":
    main()