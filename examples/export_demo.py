from veritas import VeritasLogger
import os

def main():
    logger = VeritasLogger()
    print("🎥 Veritas Proof Export Demo\n")

    # 1. Generate some activity
    @logger.wrap(event_type="OBSERVATION")
    def get_market_data():
        return {"ETH": 2500, "BTC": 65000}

    @logger.wrap(event_type="ACTION")
    def buy_token(token):
        return f"Bought {token}"

    print("--- Simulating Agent Activity ---")
    get_market_data()
    buy_token("ETH")
    
    # 2. Export Proofs
    filename = "session_proof.json"
    logger.export_proofs(filename)
    
    # 3. Validation
    if os.path.exists(filename):
        print("\n✅ Success! Proof file created.")
        print(f"   Run 'cat {filename}' to see the cryptographic evidence.")

if __name__ == "__main__":
    main()

