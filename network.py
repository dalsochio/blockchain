import json
import os
import socket
import threading
import traceback
from typing import Callable, Dict, List
from block import Block, create_block_from_dict, hash_block


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
    difficulty: int,
    transactions: List[Dict],
    blockchain_fpath: str,
    on_valid_block_callback: Callable,
):
    """Lida com mensagens recebidas de outros nós.
    
    Args:
        conn: Conexão do socket
        addr: Endereço do nó remetente
        blockchain: Cadeia de blocos local
        difficulty: Dificuldade de mineração atual
        transactions: Lista de transações pendentes
        blockchain_fpath: Caminho para o arquivo da blockchain
        on_valid_block_callback: Função de callback para quando um bloco válido é recebido
    """
    try:
        data = conn.recv(4096).decode()
        if not data:
            conn.close()
            return
            
        msg = json.loads(data)
        
        if msg["type"] == "block":
            handle_received_block(
                msg["data"], 
                blockchain, 
                difficulty, 
                blockchain_fpath, 
                on_valid_block_callback, 
                addr
            )
            
        elif msg["type"] == "chain_request":
            # Envia a cadeia completa para o nó que solicitou
            send_chain(conn, blockchain)
            
        elif msg["type"] == "chain":
            # Recebeu uma cadeia completa de outro nó
            handle_received_chain(
                msg["data"], 
                blockchain, 
                blockchain_fpath, 
                addr
            )
            
        elif msg["type"] == "tx":
            # Recebeu uma nova transação
            tx = msg["data"]
            if tx not in transactions:
                transactions.append(tx)
                print(f"[+] Transação recebida de {addr}")
                
    except json.JSONDecodeError:
        print(f"[!] Mensagem inválida recebida de {addr}")
    except Exception as e:
        print(f"[!] Exceção ao lidar com cliente {addr}: {e}")
        print(traceback.format_exc())
    finally:
        conn.close()


def handle_received_block(block_data, blockchain, difficulty, blockchain_fpath, on_valid_block_callback, sender_addr):
    """Lida com um bloco recebido de outro nó."""
    try:
        block = create_block_from_dict(block_data)
        expected_hash = hash_block(block)
        
        # Verifica se o bloco é válido
        if block.hash != expected_hash or not block.hash.startswith("0" * difficulty):
            print(f"[!] Bloco inválido recebido de {sender_addr}")
            return
            
        # Se o bloco é o próximo da cadeia, adiciona normalmente
        if block.prev_hash == blockchain[-1].hash:
            blockchain.append(block)
            on_valid_block_callback(blockchain_fpath, blockchain)
            print(f"[✓] Novo bloco {block.index} adicionado de {sender_addr}")
            return
            
        # Se não for o próximo, verifica se é parte de uma cadeia mais longa
        if block.index > len(blockchain) - 1:
            print(f"[i] Possível fork detectado. Solicitando cadeia completa de {sender_addr}")
            request_chain(sender_addr, blockchain[0].port, blockchain[-1].hash)
            
    except Exception as e:
        print(f"[!] Erro ao processar bloco de {sender_addr}: {e}")


def handle_received_chain(chain_data, blockchain, blockchain_fpath, sender_addr):
    """Lida com uma cadeia de blocos recebida de outro nó."""
    try:
        # Converte os dicionários de volta para objetos Block
        new_chain = [create_block_from_dict(block) for block in chain_data]
        
        # Verifica se a nova cadeia é mais longa e válida
        if len(new_chain) > len(blockchain):
            print(f"[i] Recebida cadeia de tamanho {len(new_chain)} de {sender_addr}")
            from chain import replace_chain
            if replace_chain(new_chain, blockchain, blockchain_fpath):
                print(f"[✓] Cadeia substituída por uma mais longa de {sender_addr}")
            else:
                print(f"[!] Falha ao substituir cadeia por uma de {sender_addr}")
    except Exception as e:
        print(f"[!] Erro ao processar cadeia de {sender_addr}: {e}")


def send_chain(conn, blockchain):
    """Envia a cadeia de blocos para um nó solicitante."""
    try:
        chain_data = [block.as_dict() for block in blockchain]
        response = {
            "type": "chain",
            "data": chain_data
        }
        conn.send(json.dumps(response).encode())
    except Exception as e:
        print(f"[!] Erro ao enviar cadeia: {e}")


def request_chain(peer_addr, peer_port, last_hash):
    """Solicita a cadeia de blocos de um nó específico."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((peer_addr, peer_port))
        request = {
            "type": "chain_request",
            "last_hash": last_hash
        }
        s.send(json.dumps(request).encode())
        s.close()
    except Exception as e:
        print(f"[!] Erro ao solicitar cadeia de {peer_addr}:{peer_port}: {e}")


def start_server(
    host: str,
    port: int,
    blockchain: List[Block],
    difficulty: int,
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
                    difficulty,
                    transactions,
                    blockchain_fpath,
                    on_valid_block_callback,
                ),
            ).start()

    threading.Thread(target=server_thread, daemon=True).start()
