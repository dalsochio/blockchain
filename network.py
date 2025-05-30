import json
import os
import socket
import threading
import traceback
from typing import Callable, Dict, List
from block import Block, create_block_from_dict, hash_block
from consensus import create_forks, apply_consensus


def list_peers(fpath: str):
    if not os.path.exists(fpath):
        print("[!] No peers file founded!")
        return []
    with open(fpath) as f:
        return [line.strip() for line in f if line.strip()]


def broadcast_block(block: Block, peers_fpath: str, port: int):
    print("Broadcasting transaction...")
    for peer in list_peers(peers_fpath):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((peer, port))
            s.send(json.dumps({"type": "block", "data": block.as_dict()}).encode())
            s.close()
        except Exception:
            pass


def broadcast_block(block: Block, peers_fpath: str, port: int):
    print("Broadcasting transaction...")
    for peer in list_peers(peers_fpath):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((peer, port))
            s.send(json.dumps({"type": "block", "data": block.as_dict()}).encode())
            s.close()
        except Exception:
            pass


def broadcast_transaction(tx: Dict, peers_fpath: str, port: int):
    for peer in list_peers(peers_fpath):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((peer, port))
            s.send(json.dumps({"type": "tx", "data": tx}).encode())
            s.close()
        except Exception as e:
            print(
                f"[BROADCAST_TX] Exception during comunication with {peer}. Exception: {e}"
            )


def handle_client(
    conn: socket.socket,
    addr: str,
    blockchain: List[Block],
    forks: List[List[Dict]],
    difficulty: int,
    fork_lim: int,
    transactions: List[Dict],
    blockchain_fpath: str,
    on_valid_block_callback: Callable,
):
    try:
        data = conn.recv(4096).decode()
        msg = json.loads(data)
        if msg["type"] == "block":
            block = create_block_from_dict(msg["data"])
            expected_hash = hash_block(block)

            # valida a integridade do bloco
            if not block.hash.startswith('0' * difficulty) or block.hash != expected_hash:
                print(f"[!] Invalid block received from {addr}")
                return

            # verifica se o bloco não está em duplicidade
            if block.hash == blockchain[-1].hash:
                print(f"[!] Duplicaded block received from {addr}")
                return

            # ------------------------------------------------ #
            # ------------------- SOLUÇÃO -------------------- #
            # ------------------------------------------------ #
            if block.index <= blockchain[-1].index or len(forks) > 0:
                create_forks(block, False, blockchain, forks)
                apply_consensus(fork_lim, blockchain, forks)
                on_valid_block_callback(blockchain_fpath, blockchain)
                return

            # adiciona na block chain
            blockchain.append(block)
            on_valid_block_callback(blockchain_fpath, blockchain)
            print(f"[✓] New valid block added from {addr}")

            '''
            if (block.prev_hash == blockchain[-1].hash and block.hash.startswith("0" * difficulty) and block.hash == expected_hash):

                # remove as transações que existem no pool com as transações que
                # foram processadas pelo bloco propagado por outro nó. assim
                # evita que transações apareçam em duplicidade na rede
                """
                new_txs = [tx for tx in transactions if tx not in block.transactions]
                transactions.clear()
                transactions.extend(new_txs)
                """

                blockchain.append(block)
                on_valid_block_callback(blockchain_fpath, blockchain)
                print(f"[✓] New valid block added from {addr}")
            else:
                print(f"[!] Invalid block received from {addr}")
            '''
        elif msg["type"] == "tx":
            tx = msg["data"]
            if tx not in transactions:
                transactions.append(tx)
                print(f"[+] Transaction received from {addr}")
    except Exception as e:
        print(
            f"Exception when hadling client. Exception: {e}. {traceback.format_exc()}"
        )
    conn.close()


def start_server(
    host: str,
    port: int,
    blockchain: List[Block],
    forks: List[List[Dict]],
    difficulty: int,
    fork_lim: int,
    transactions: List[Dict],
    blockchain_fpath: str,
    on_valid_block_callback: Callable,
):
    def server_thread():
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((host, port))
        server.listen()
        print(f"[SERVER] Listening on {host}:{port}")
        while True:
            conn, addr = server.accept()
            threading.Thread(
                target=handle_client,
                args=(
                    conn,
                    addr,
                    blockchain,
                    forks,
                    difficulty,
                    fork_lim,
                    transactions,
                    blockchain_fpath,
                    on_valid_block_callback,
                ),
            ).start()

    threading.Thread(target=server_thread, daemon=True).start()
