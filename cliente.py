# cliente.py
import socket
import struct
import json
import time
import random
import numpy as np

NUM_SERVIDORES = 4

SERVIDORES_DISPONIVEIS = [
    ("127.0.0.1", 5000),
    ("127.0.0.1", 5001),
    ("127.0.0.1", 5002),
    ("127.0.0.1", 5003),
    ("127.0.0.1", 5004),
    ("127.0.0.1", 5005),
    ("127.0.0.1", 5006),
    ("127.0.0.1", 5007),
]

SERVIDORES = SERVIDORES_DISPONIVEIS[:NUM_SERVIDORES]


def send_msg(sock, data_bytes):
    msg = struct.pack("!I", len(data_bytes)) + data_bytes
    sock.sendall(msg)

def recv_all(sock, n):
    data = b''
    while len(data) < n:
        p = sock.recv(n - len(data))
        if not p:
            raise EOFError("Conexão encerrada")
        data += p
    return data

def recv_msg(sock):
    raw_len = recv_all(sock, 4)
    (length,) = struct.unpack("!I", raw_len)
    return recv_all(sock, length)

def gerar_matriz(linhas, colunas):
    return [[random.randint(1, 9) for _ in range(colunas)] for _ in range(linhas)]

def print_matrix(matrix):
    for row in matrix:
        print(row)


def enviar_para_servidor(host, port, subA, B):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    payload = json.dumps({"subA": subA, "B": B}).encode("utf-8")
    send_msg(s, payload)

    data = recv_msg(s)
    s.close()

    resp = json.loads(data.decode("utf-8"))
    return resp.get("resultado")

def dividir_A(A, n):
    tam = len(A)
    base = tam // n
    resto = tam % n

    partes = []
    start = 0
    for i in range(n):
        extra = 1 if i < resto else 0
        end = start + base + extra
        partes.append(A[start:end])
        start = end
    return partes


def executar_serial(A, B):
    partes = dividir_A(A, len(SERVIDORES))
    tempos = []
    resultados = []

    t0 = time.time()

    for i, (host, port) in enumerate(SERVIDORES):
        print(f"[SÉRIE] Enviando bloco {i} para {host}:{port}...")
        ini = time.time()
        r = enviar_para_servidor(host, port, partes[i], B)
        fim = time.time()

        tempos.append(fim - ini)
        resultados.extend(r)

    t_total = time.time() - t0
    return resultados, tempos, t_total


def executar_paralelo(A, B):
    import threading

    partes = dividir_A(A, len(SERVIDORES))
    resultados = [None] * len(SERVIDORES)
    tempos = [0] * len(SERVIDORES)

    threads = []

    def worker(i, host, port):
        ini = time.time()
        resultados[i] = enviar_para_servidor(host, port, partes[i], B)
        tempos[i] = time.time() - ini

    t0 = time.time()

    for i, (host, port) in enumerate(SERVIDORES):
        print(f"[PARALELO] Enviando bloco {i} para {host}:{port}...")
        t = threading.Thread(target=worker, args=(i, host, port))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    resultado_final = []
    for bloco in resultados:
        resultado_final.extend(bloco)

    t_total = time.time() - t0
    return resultado_final, tempos, t_total


if __name__ == "__main__":
    print("=== MULTIPLICAÇÃO DE MATRIZES DISTRIBUÍDA ===")

    # entrada do usuário
    LinA = int(input("Linhas de A: "))
    ColA = int(input("Colunas de A: "))
    LinB = ColA
    ColB = int(input("Colunas de B: "))

    print("Gerando matrizes...")
    A = gerar_matriz(LinA, ColA)
    print_matrix(A)
    print("----------------")
    B = gerar_matriz(LinB, ColB)
    print_matrix(B)
    print("----------------")

    print(f"\nServidores usados ({NUM_SERVIDORES}):")
    for s in SERVIDORES:
        print(" -", s)

    print("\n=== EXECUTANDO EM SÉRIE ===")
    res_s, tempos_s, total_s = executar_serial(A, B)
    #sao_iguais = np.dot(A,B) == np.array(res_s)
    #print(sao_iguais)
    print("Tempo por servidor:", tempos_s)
    print("Tempo total em série:", total_s, "s")

    print("\n=== EXECUTANDO EM PARALELO ===")
    res_p, tempos_p, total_p = executar_paralelo(A, B)
    #sao_iguais = np.dot(A,B) == np.array(res_p)
    #print(sao_iguais)
    print("Tempo por servidor:", tempos_p)
    print("Tempo total em paralelo:", total_p, "s")

    print("\nFinalizado.")
