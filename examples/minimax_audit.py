import os
import json
import requests
from veritas import VeritasLogger

# Configuration
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_GROUP_ID = os.getenv("MINIMAX_GROUP_ID") # Optional, depending on endpoint

def call_minimax(prompt: str) -> str:
    """Simple wrapper to get a decision from MiniMax."""
    if not MINIMAX_API_KEY:
        print("[Mock] MiniMax API Key missing. Simulating response: 'BUY'")
        return "BUY"

    url = "https://api.minimax.chat/v1/text/chatcompletion_pro"
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "abab5.5-chat", # Using a standard model
        "messages": [
            {"sender_type": "USER", "sender_name": "User", "text": prompt}
        ],
        "bot_setting": [
            {
                "bot_name": "TraderAgent",
                "content": "You are a crypto trading bot. Output ONLY 'BUY' or 'SELL' based on the data."
            }
        ],
        "reply_constraints": {"sender_type": "BOT", "sender_name": "TraderAgent"},
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        res_json = response.json()
        return res_json['reply']
    except Exception as e:
        print(f"MiniMax Call Failed: {e}")
        return "HOLD"

def main():
    logger = VeritasLogger()
    print("Veritas + MiniMax Agent Demo")
    print("----------------------------")

    # 1. Define Tools
    @logger.wrap(event_type="OBSERVATION")
    def get_market_sentiment():
        # In a real app, this might fetch news or prices
        return {"ETH": 2650, "Trend": "Bullish", "Volume": "High"}

    @logger.wrap(event_type="ACTION")
    def execute_trade(action, token):
        print(f"   Executing Order: {action} {token}")
        return f"tx_0x{os.urandom(4).hex()}"

    # 2. Agent Loop
    print("--- 1. Observation ---")
    market_data = get_market_sentiment()
    obs_id = logger.last_event_id
    print(f"   Market Data Captured. ID: {obs_id}")

    print("--- 2. Deliberation (MiniMax) ---")
    prompt = f"Market Data: {json.dumps(market_data)}. Should I BUY or SELL ETH?"
    decision = call_minimax(prompt).strip()
    print(f"   MiniMax Decision: {decision}")

    print("--- 3. Execution ---")
    if "BUY" in decision.upper():
        execute_trade("BUY", "ETH", basis_id=obs_id)
    elif "SELL" in decision.upper():
        execute_trade("SELL", "ETH", basis_id=obs_id)
    else:
        print("   No trade executed.")

    print("--- 4. Proof Generation ---")
    logger.export_proofs("minimax_session.json")

if __name__ == "__main__":
    main()
