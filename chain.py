import json
import os
from typing import List

from block import Block, create_block, create_block_from_dict, create_genesis_block
from network import broadcast_block, broadcast_transaction


def load_chain(fpath: str) -> List[Block]:
    if os.path.exists(fpath):
        with open(fpath) as f:
            data = json.load(f)
            blockchain = []
            for block_data in data:
                block = create_block_from_dict(block_data)
                blockchain.append(block)
            return blockchain

    return [create_genesis_block()]


def save_chain(fpath: str, chain: list[Block]):
    blockchain_serializable = []
    for b in chain:
        blockchain_serializable.append(b.as_dict())

    with open(fpath, "w") as f:
        json.dump(blockchain_serializable, f, indent=2)


def valid_chain(chain):
    """Verifica se uma cadeia de blocos é válida.
    
    Args:
        chain: Lista de blocos a ser validada
        
    Returns:
        bool: True se a cadeia for válida, False caso contrário
    """
    if not chain:
        return False
        
    # Verifica se o bloco gênese está correto
    genesis = chain[0]
    if genesis.index != 0 or genesis.prev_hash != "0" or genesis.hash != "0":
        return False
        
    # Verifica cada bloco subsequente
    for i in range(1, len(chain)):
        current = chain[i]
        previous = chain[i-1]
        
        # Verifica se o hash do bloco atual está correto
        if current.hash != hash_block(current):
            return False
            
        # Verifica se o hash do bloco anterior está correto
        if current.prev_hash != previous.hash:
            return False
            
        # Verifica se o índice está em sequência
        if current.index != previous.index + 1:
            return False
            
    return True


def replace_chain(new_chain, current_chain, blockchain_fpath):
    """Substitui a cadeia atual por uma nova se for válida e mais longa.
    
    Args:
        new_chain: Nova cadeia de blocos candidata
        current_chain: Cadeia de blocos atual
        blockchain_fpath: Caminho para salvar a blockchain
        
    Returns:
        bool: True se a cadeia foi substituída, False caso contrário
    """
    if not valid_chain(new_chain):
        print("[!] Cadeia recebida é inválida")
        return False
        
    if len(new_chain) <= len(current_chain):
        print(f"[!] Cadeia recebida não é mais longa (recebida: {len(new_chain)}, atual: {len(current_chain)})")
        return False
        
    # Se chegou aqui, a nova cadeia é válida e mais longa
    print(f"[i] Substituindo cadeia atual (tamanho {len(current_chain)}) por cadeia mais longa (tamanho {len(new_chain)})")
    current_chain.clear()
    current_chain.extend(new_chain)
    save_chain(blockchain_fpath, current_chain)
    return True


def print_chain(blockchain: List[Block]):
    for b in blockchain:
        print(f"Index: {b.index}, Hash: {b.hash[:10]}..., Tx: {len(b.transactions)}")


def mine_block(
    transactions: List,
    blockchain: List[Block],
    node_id: str,
    reward: int,
    difficulty: int,
    blockchain_fpath: str,
    peers_fpath: str,
    port: int,
):
    """Minera um novo bloco e o adiciona à blockchain.
    
    Args:
        transactions: Lista de transações a serem incluídas no bloco
        blockchain: Lista atual de blocos
        node_id: ID do nó minerador
        reward: Recompensa por mineração
        difficulty: Dificuldade de mineração
        blockchain_fpath: Caminho para salvar a blockchain
        peers_fpath: Caminho para o arquivo de pares
        port: Porta para broadcast
    """
    # Cria um novo bloco com as transações atuais
    new_block = create_block(
        transactions,
        blockchain[-1].hash,
        miner=node_id,
        index=len(blockchain),
        reward=reward,
        difficulty=difficulty,
    )
    
    # Adiciona o bloco à cadeia local
    blockchain.append(new_block)
    transactions.clear()
    save_chain(blockchain_fpath, blockchain)
    
    # Transmite o novo bloco para a rede
    broadcast_block(new_block, peers_fpath, port)
    print(f"[✓] Bloco {new_block.index} minerado e transmitido com sucesso. Hash: {new_block.hash[:10]}...")


def make_transaction(sender, recipient, amount, transactions, peers_file, port):
    tx = {"from": sender, "to": recipient, "amount": amount}
    transactions.append(tx)
    broadcast_transaction(tx, peers_file, port)
    print("[+] Transaction added.")


def get_balance(node_id: str, blockchain: List[Block]) -> float:
    balance = 0
    for block in blockchain:
        for tx in block.transactions:
            if tx["to"] == node_id:
                balance += float(tx["amount"])
            if tx["from"] == node_id:
                balance -= float(tx["amount"])
    return balance


def on_valid_block_callback(fpath, chain):
    save_chain(fpath, chain)