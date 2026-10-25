import flwr as fl

if __name__ == "__main__":
    strategy = fl.server.strategy.FedAvg(
        min_fit_clients=2,
        min_evaluate_clients=2,
        min_available_clients=2,
    )
    
    print("🛡️ Bandhan FL Server - GNN Mode Active 🕸️")
    print("Waiting for Banks to connect their Graphs...")
    
    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=10),
        strategy=strategy,
    )