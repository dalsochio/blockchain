from block import Block
from typing import List, Dict

def fork_block(block: Block, blockchain: List[Block], forks: List[List[Block]]):
    # cria os forks caso não exista forks criados ainda.
    # um dos forks é uma parte da blockchain
    if len(forks) == 0:
        forks.append([block])
        forks.append(blockchain[block.index:])
        return

    # caso já exista forks criados, verifica em qual 
    # fork o bloco recebido pertence
    for i in range(0, len(forks)):
        if forks[i][-1].hash == block.prev_hash:
            forks[i].append(block)
            return

    # como não foi encontrado um fork para o bloco
    # começa um novo com ele
    forks.append(list(block))


def resolve_forks(lim: int, blockchain: List[Block], forks: List[List[Block]]):
    # se existe um fork com o limite especificado de blocos
    # combina o fork com a blockchain a partir da divergência
    # e limpa a lista de forks
    for fork in forks:
        if len(fork) >= lim:
            divergence = fork[0].index
            new_blockchain = blockchain[:divergence] + fork
            forks.clear()
            blockchain.clear()
            blockchain.extend(new_blockchain)
