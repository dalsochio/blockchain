from typing import Dict, List
from block import Block

from chain import (
    get_balance,
    load_chain,
    make_transaction,
    mine_block,
    on_valid_block_callback,
    print_chain,
)
from network import start_server
from utils import load_config


if __name__ == "__main__":
    """
    Exemplo de config:
    {
        "node_id": "george_linux", // nome exclusivo para o computador em que o código será executado
        "host": "172.29.20.2", // IP fornecido pelo zerotier para o computador em que o código será executado
        "port": 5002, // porta padrão estabelecida para toda a rede P2P
        "difficulty": 4, // dificuldade de mineração
        "reward": 10, // recompensa pela mineração
        "blockchain_file": "db/blockchain.json", // arquivo para salvar blockchain
        "peers_file": "configs/peers.txt" // arquivo para listar os IPs dos demais pares
    }
    """
    config = load_config()
    blockchain = load_chain(config["blockchain_file"])
    transactions: List[Dict] = []
    forks: List[List[Block]] = []

    start_server(
        config["host"],
        config["port"],
        blockchain,
        forks,
        config["difficulty"],
        config["fork_lim"],
        transactions,
        config["blockchain_file"],
        on_valid_block_callback,
    )

    print("=== SimpleCoin CLI ===")
    while True:
        print("\n1. Add transaction")
        print("2. Mine block")
        print("3. View blockchain")
        print("4. Get balance")
        print("5. Exit")
        print("6. View forks")
        choice = input("> ").strip()

        if choice == "1":
            sender = input("Sender: ")
            recipient = input("Recipient: ")
            amount = input("Amount: ")
            make_transaction(
                sender,
                recipient,
                amount,
                transactions,
                config["peers_file"],
                config["port"],
            )

        elif choice == "2":
            mine_block(
                transactions,
                blockchain,
                forks,
                config["node_id"],
                config["reward"],
                config["difficulty"],
                config["fork_lim"],
                config["blockchain_file"],
                config["peers_file"],
                config["port"],
            )

        elif choice == "3":
            print_chain(blockchain)

        elif choice == "4":
            node_id = input("Node ID: ")
            balance = get_balance(node_id, blockchain)
            print(f"[i] The balance of {node_id} is {balance}.")

        elif choice == "5":
            print("Exiting...")
            break

        elif choice == "6":
            for fork in forks:
                print()
                print_chain(fork)

        else:
            print("[!] Invalid choice.")
