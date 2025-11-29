
import socket
import struct
import json
import sys

def recv_all(sock, n):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            raise EOFError("Conexão fechada antes de receber todos os bytes")
        data += packet
    return data

def recv_msg(sock):
    raw_len = recv_all(sock, 4)
    (length,) = struct.unpack('!I', raw_len)
    if length == 0:
        return b''
    return recv_all(sock, length)

def send_msg(sock, data_bytes):
    length_prefix = struct.pack('!I', len(data_bytes))
    sock.sendall(length_prefix + data_bytes)

def multiplicar_linha_serial(linha_A, B):
    resultado = []
    for j in range(len(B[0])):
        soma = 0
        for k in range(len(linha_A)):
            soma += linha_A[k] * B[k][j]
        resultado.append(soma)
    return resultado

def handle_connection(conn):
    try:
        data_bytes = recv_msg(conn)
        data = json.loads(data_bytes.decode('utf-8'))

        subA = data.get('subA')
        B = data.get('B')

        if subA is None or B is None:
            resp = json.dumps({"error": "payload inválido"}).encode('utf-8')
            send_msg(conn, resp)
            return

        resultado = []
        for linha in subA:
            resultado.append(multiplicar_linha_serial(linha, B))

        resp = json.dumps({"resultado": resultado}).encode('utf-8')
        send_msg(conn, resp)

    except Exception as e:
        try:
            err = json.dumps({"error": str(e)}).encode('utf-8')
            send_msg(conn, err)
        except:
            pass
    finally:
        conn.close()

def run_server(host, port):
    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serv.bind((host, port))
    serv.listen(1)
    print(f"Servidor TCP (SÉRIE) ouvindo em {host}:{port} ... (CTRL+C para encerrar)")

    try:
        while True:
            conn, addr = serv.accept()
            handle_connection(conn)

    except KeyboardInterrupt:
        print("\nEncerrando servidor.")
    finally:
        serv.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python server_serie.py <porta>")
        sys.exit(1)
    port = int(sys.argv[1])
    HOST = "0.0.0.0"
    run_server(HOST, port)
