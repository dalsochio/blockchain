from block import Block
from typing import List, Dict


def get_block_info(blockchain: List[Block], forks: List[List[Block]]):
    if len(forks) > 0:
        for fork in forks:
            if blockchain[-1].hash == fork[0].hash:
                return fork[-1].hash, fork[-1].index + 1

    return blockchain[-1].hash, blockchain[-1].index + 1


def create_forks(block: Block, own_block, blockchain: List[Block], forks: List[List[Block]]):
    # cria os forks caso não exista ainda
    # 1. uma das listas contém o block minerado/recebido
    # 2. uma das liasta contém o último bloco da blockchain
    # caso o bloco pertence ao minerador, substitui o último bloco
    # da blockchain pelo bloco passado como argumento
    if len(forks) == 0:
        forks.append([block])
        forks.append(blockchain[block.index:])

        if own_block:
            blockchain[-1] = block

        return

    # como já existe forks criados, o passo seguinte
    # é verificar em qual lista de forks o bloco passado
    # na função pertence. verifica o "prev_hash" do bloco
    for i in range(0, len(forks)):
        if forks[i][-1].hash == block.prev_hash:
            forks[i].append(block)
            return

    # como não foi encontrada nenhuma lista a qual o
    # bloco pertença, cria uma lista iniciando desse
    # bloco
    forks.append([block])


def apply_consensus(lim: int, blockchain: List[Block], forks: List[List[Block]]):
    # soma a quantidade total de blocos que existem 
    # nos forks, caso o total seja igual ou maior 
    # que o limite estipulado, aplica o consenso. caso
    # contrário, espera por novos blocos
    blocks_in_forks = sum(len(f) for f in forks)
    if blocks_in_forks >= lim: 
        fork = forks[get_most_worked(forks)]
        divergence = fork[0].index
        new_blockchain = blockchain[:divergence] + fork
        forks.clear()
        blockchain.clear()
        blockchain.extend(new_blockchain)


def get_most_worked(forks: List[List[Block]]):
    prev_total = 0
    chain_index = -1

    for k, chain in enumerate(forks):
        total = sum((2**256)/(b.difficulty+1) for b in chain)
        if total > prev_total:
            chain_index = k
            prev_total = total

    return chain_index
