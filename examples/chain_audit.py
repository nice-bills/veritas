from veritas import VeritasLogger
import time

def main():
    logger = VeritasLogger()
    print("🎥 Veritas Evidence Chaining Demo\n")

    # 1. Define Tools
    @logger.wrap(event_type="OBSERVATION")
    def fetch_price(token):
        print(f"   👀 FETCHING: Price of {token}")
        return 2500.00

    @logger.wrap(event_type="ACTION")
    def execute_trade(token_in, token_out, amount):
        print(f"   🚀 EXECUTING: Swap {amount} {token_in} -> {token_out}")
        return "tx_0xabc123"

    # 2. Run Agent with Chaining
    print("--- Agent Running ---")
    
    # Step 1: Observe
    price = fetch_price("ETH")
    observation_id = logger.last_event_id
    print(f"   [Veritas] Observation Captured: {observation_id}")

    # Step 2: Act based on Observation
    if price > 2000:
        print(f"   [Agent] Price is good, trading based on {observation_id[:8]}...")
        execute_trade("USDC", "ETH", 1000, basis_id=observation_id)
    
    print("--- Agent Finished ---\n")

    # 3. Audit
    print("🔒 AUDIT TRAIL (Linked Evidence):")
    for log in logger.get_logs():
        link = f" -> Based on {log.basis_id[:8]}" if log.basis_id else ""
        print(f"[{log.event_type}] {log.tool_name}{link}")
        if log.event_type == "ACTION" and not log.basis_id:
            print("    ⚠️  WARNING: Action has no linked evidence!")

    root = logger.get_current_root()
    print(f"\nFinal Merkle Root: {root}")

if __name__ == "__main__":
    main()
