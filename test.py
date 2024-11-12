# 서버 코드 (제공된 서버에서 실행)
import socket

# 제공된 IP와 포트
server_ip = '210.94.179.19'
port = 9610

# 서버 소켓 생성
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((server_ip, port))
server_socket.listen(1)

print(f"Server is listening on {server_ip}:{port}")

try:
    # 클라이언트의 연결 수락
    conn, addr = server_socket.accept()
    print(f"Connected by {addr}")

    # 클라이언트에 메시지 전송
    conn.sendall(b"Hello, Client! TCP/IP connection is successful.")
    
    # 클라이언트로부터 데이터 수신 (테스트 용도)
    data = conn.recv(1024)
    print("Received from client:", data.decode())

finally:
    conn.close()
    server_socket.close()
