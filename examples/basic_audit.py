from veritas import VeritasLogger
import time

def main():
    # 1. Initialize the Recorder
    logger = VeritasLogger()
    print("Veritas Recorder Started\n")

    # 2. Define a "Tool" (Simulated Trade)
    @logger.wrap
    def execute_trade(token_in, token_out, amount):
        print(f"   EXECUTING: Swap {amount} {token_in} -> {token_out}")
        time.sleep(0.5) # Simulate network lag
        return "tx_hash_0x123456789"

    # 3. Define another tool
    @logger.wrap
    def fetch_price(token):
        print(f"   FETCHING: Price of {token}")
        return 2500.00

    # 4. Run the Agent Logic
    print("--- Agent Running ---")
    price = fetch_price("ETH")
    if price > 2000:
        execute_trade("USDC", "ETH", 1000)
    print("--- Agent Finished ---\n")

    # 5. Verify the Evidence
    print("AUDIT TRAIL:")
    root = logger.get_current_root()
    print(f"Merkle Root (Session Fingerprint): {root}")
    
    logs = logger.get_logs()
    for i, log in enumerate(logs):
        print(f"\n[{i}] {log.tool_name}")
        print(f"    Params: {log.input_params}")
        print(f"    Result: {log.output_result}")
        print(f"    Hash: {log.to_hashable_json()[:30]}...")

if __name__ == "__main__":
    main()
