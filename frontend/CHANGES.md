# Veritas Frontend - Complete Overhaul Documentation

## Target: What is Veritas?

Veritas is a **Crypto AI Agent Playground** - think of it as "Replit for Crypto Agents." It's a platform where developers and users can:
- Build autonomous AI agents that interact with blockchain
- Deploy agents on Base (Coinbase's L2)
- Every action is cryptographically verified and stored on-chain

**The Backend Has:**
- 14 different capability modules (Wallet, DeFi, NFTs, Social, etc.)
- FastAPI with WebSocket streaming
- Merkle tree proofs + EAS attestation
- Support for both one-time missions AND persistent agents
- MiniMax AI integration

**The Old Frontend Problem:**
- Only exposed 1 capability (Wallet)
- Hardcoded everything
- No visual polish
- Users couldn't actually use 90% of the backend features

---

##  What I Changed

### 1. **globals.css** - Visual Foundation
Added:
- **Animated grid background** (`animated-grid`) - moving grid pattern
- **Particle system styles** - for floating particles with connections
- **Glass morphism** (`glass` class) - frosted glass effects
- **Spotlight cards** (`spotlight-card`) - mouse-following light effects
- **Entrance animations** - fadeInUp, scaleIn, slideIn
- **Hover effects** - lift, glow, press states
- **Custom scrollbar** - styled for dark theme
- **Skeleton loading** - shimmer effects

### 2. **page.tsx** - Main Playground (Complete Rewrite)

#### Before (Old Version):
```typescript
// Hardcoded to ONLY use 'wallet' capability
body: JSON.stringify({ 
  name: 'Agent', 
  capabilities: ['wallet'],  // ← Only this!
  ...
})
```

#### After (New Version):
```typescript
// Sends ALL selected capabilities
body: JSON.stringify({ 
  name: agentName, 
  capabilities: selectedCapabilities,  // ← Dynamic!
  ...
})
```

#### New Features Added:

**A. Welcome Screen Enhancements:**
- Particle background with connection lines
- Shows "14 Capabilities Available"
- Displays capability preview badges
- Better animations and transitions

**B. Tab Navigation:**
- **Playground Tab**: Main agent configuration
- **Capabilities Tab**: Grid of all 14 capabilities to select/deselect
- Shows count: "Capabilities (3)"

**C. Agent Configuration Panel:**
- **Agent Name**: Custom naming
- **Brain Provider**: MiniMax M2.1 (with OpenAI/Anthropic placeholders)
- **Network**: Base Sepolia (with Mainnet placeholder)
- **Advanced Toggle**: Hide/show extra options

**D. Capability Selector:**
- Grid layout (2x2, 3x3, 4x4 responsive)
- All 14 capabilities with descriptions
- Click to toggle on/off
- Visual feedback (green border when selected)
- Checkmark icon for selected items

**E. Mission Editor Improvements:**
- Better placeholder text with examples
- Clear button
- Shows agent address when created
- Run Agent button with loading state

**F. Terminal Output:**
- Color-coded log entries
- Auto-scroll to bottom
- THOUGHT (purple), ACTION (green), ERROR (red), OBSERVATION (blue)
- Timestamp and tool name displayed

**G. Verification Panel:**
- Shows "Verified" badge when session complete
- Displays Merkle root
- Link to BaseScan for attestation

**H. Header:**
- Backend connection status indicator
- Link to Dashboard
- User name display
- Settings button

### 3. **dashboard/page.tsx** - Agent History Page

#### Updated with:
- Same particle background as main page
- Grid background for consistency
- Agent cards with hover effects
- Better empty state
- Glow effects on cards
- Improved layout and spacing

### 4. **layout.tsx** - Root Layout

#### Improvements:
- Better metadata (title, description, keywords)
- Viewport configuration
- Suppress hydration warning
- Cleaner structure

---

## Data: Backend vs Frontend Mapping

### Backend Capabilities (14 Total):

| Capability | Tools Available | Frontend Status |
|------------|----------------|-----------------|
| **wallet** | get_balance, native_transfer |  Fully supported |
| **token** | erc20_transfer, wrap_eth, unwrap_eth |  Fully supported |
| **trade** | get_swap_price |  Fully supported |
| **aave** | aave_supply, aave_borrow |  Fully supported |
| **compound** | compound_supply |  Fully supported |
| **nft** | nft_balance, nft_transfer |  Fully supported |
| **basename** | register_basename |  Fully supported |
| **social** | post_tweet |  Fully supported |
| **payments** | http_request, pay_with_x402 |  Fully supported |
| **wow** | launch_token |  Fully supported |
| **nillion** | store_secret, retrieve_secret |  Fully supported |
| **pyth** | get_price |  Fully supported |
| **chainlink** | get_price |  Fully supported |
| **onramp** | get_buy_url |  Fully supported |

**Key Change**: Old frontend only sent `capabilities: ['wallet']`. Now it sends whatever the user selects: `['wallet', 'token', 'aave', 'trade']` etc.

---

##  How to Use the New Playground

### Step 1: Welcome Screen
1. Enter your name
2. Click "Enter Playground"
3. See particle animation and capability preview

### Step 2: Configure API Keys (First Time)
1. Click Settings (gear icon) in header
2. Enter:
   - CDP API Key ID
   - CDP API Key Secret (private key)
   - MiniMax API Key
3. Click "Save"

### Step 3: Select Capabilities
1. Click "Capabilities" tab
2. Click on capabilities to toggle them on/off:
   - Green border = selected
   - Checkmark = selected
   - Gray = not selected
3. Recommended combos:
   - **Basic**: wallet
   - **Trading**: wallet + token + trade
   - **DeFi**: wallet + token + aave + compound
   - **Full**: wallet + token + trade + aave + pyth

### Step 4: Configure Agent
1. Go to "Playground" tab
2. Enter agent name (optional)
3. Click "Advanced" to see brain/network options
4. Enter mission objective:
   ```
   Check my ETH balance and swap 0.1 ETH to USDC 
   if the price is below $3500. Then supply the 
   USDC to Aave to earn yield.
   ```

### Step 5: Run Agent
1. Click "Run Agent" button
2. Watch real-time logs in terminal
3. See verification when complete
4. Check BaseScan link for on-chain proof

### Step 6: View History
1. Click "My Agents" in header
2. See all past agent runs
3. Click "Rerun" to reuse configuration

---

## 🎨 Visual Features Explained

### Particle Background
- Canvas-based animation
- Floating white dots
- Lines connect nearby dots
- Creates "network" visual
- Subtle, doesn't distract

### Glass Morphism
- `backdrop-filter: blur(12px)`
- Semi-transparent backgrounds
- Border highlights
- Modern, premium feel

### Spotlight Cards
- Tracks mouse position
- Radial gradient follows cursor
- Subtle white glow
- Makes UI feel interactive

### Animations
- **fadeInUp**: Elements slide up while fading in
- **scaleIn**: Elements grow from 95% to 100%
- **slideIn**: Elements slide from left
- **status-pulse**: Connection indicator pulses

### Color Coding
- **Emerald**: Success, wallet, verification
- **Blue**: Information, tokens
- **Purple**: Trading, AI thoughts
- **Amber**: Warnings, Aave
- **Red**: Errors
- **Zinc/Gray**: Neutral text

---

## Warning: What's Still Missing (Future Work)

### High Priority:
1. **Agent Templates Gallery**
   - Pre-built strategies
   - One-click load
   - Examples: DCA Bot, Yield Farmer, Arbitrage Hunter

2. **Persistent Agent Controls**
   - Start/Stop buttons for long-running agents
   - Send message to running agent
   - View persistent agent status

3. **Real-Time Price Feeds**
   - Display Pyth/Chainlink prices
   - Price charts
   - Change indicators

4. **Token Balance Viewer**
   - Show all ERC20 balances
   - USD values
   - Historical changes

### Medium Priority:
5. **NFT Gallery**
   - View owned NFTs
   - Transfer UI
   - Metadata display

6. **DeFi Dashboard**
   - Aave positions
   - Compound supply
   - APY displays

7. **Social Integration**
   - Twitter post composer
   - Post history

8. **Proof Verification UI**
   - On-page verification
   - Download proof JSON

---

## Tool: Technical Details

### File Structure:
```
frontend/src/app/
├── page.tsx          # Main playground (566 lines)
├── dashboard/
│   └── page.tsx      # Agent history
├── layout.tsx        # Root layout
└── globals.css       # All styles and animations
```

### State Management:
- React useState for all state
- localStorage for persistence:
  - `veritas_user`: User name
  - `veritas_cdp_id`: CDP Key ID
  - `veritas_cdp_secret`: CDP Secret
  - `veritas_minimax_key`: MiniMax Key

### WebSocket Connection:
- Real-time log streaming
- Auto-scroll to bottom
- Closes on unmount

### API Integration:
- `POST /agents` - Create agent
- `POST /agents/{id}/run` - Run mission
- `WebSocket /agents/{id}/ws` - Stream logs

---

## 🎓 Example Use Cases

### Use Case 1: Simple Balance Check
```
Capabilities: wallet
Objective: Check my ETH balance and tell me how much I have.
```

### Use Case 2: Token Swap
```
Capabilities: wallet, token, trade
Objective: Get the current ETH/USDC price. If it's below 3500, 
swap 0.05 ETH to USDC.
```

### Use Case 3: DeFi Yield
```
Capabilities: wallet, token, aave
Objective: Check my USDC balance. Supply 100 USDC to Aave 
and tell me the APY I'm earning.
```

### Use Case 4: Price Monitor
```
Capabilities: wallet, pyth, chainlink
Objective: Get ETH price from both Pyth and Chainlink. 
Alert me if the prices differ by more than 1%.
```

### Use Case 5: Social Trader
```
Capabilities: wallet, token, trade, social
Objective: Swap 0.1 ETH to USDC, then post a tweet 
announcing the trade with the price.
```

---

## 🐛 Troubleshooting

### Issue: "Backend disconnected"
- Make sure backend is running: `uv run src/veritas/api/main.py`
- Check `NEXT_PUBLIC_API_URL` env var

### Issue: "Failed to create agent"
- Check API keys in Settings
- Make sure CDP key has proper permissions
- Verify MiniMax API key is valid

### Issue: "Mission failed"
- Check agent has right capabilities for the objective
- Verify wallet has enough ETH for gas
- Check network (Base Sepolia vs Mainnet)

### Issue: Capabilities not working
- Make sure to select them BEFORE running
- Some capabilities need others (e.g., token operations need wallet)
- Check browser console for errors

---

## 📈 Next Steps for You

1. **Test the new frontend**
   ```bash
   cd dev/veritas/frontend
   npm install
   npm run dev
   ```

2. **Try different capability combinations**
   - Start simple (just wallet)
   - Add more (wallet + token + trade)
   - Go complex (wallet + token + aave + pyth + trade)

3. **Give feedback on what features to add next**
   - Agent templates?
   - Persistent agents?
   - Price feeds display?
   - Something else?

---

## Tip: Why This Matters

**Before**: Frontend only let users do basic wallet operations
**After**: Frontend exposes ALL backend capabilities

This turns Veritas from a simple demo into a true playground where users can actually build complex, multi-capability crypto agents with just a few clicks.

The cryptographic proof + Base integration is still there (that's the core value prop), but now users can actually USE it for real DeFi, trading, social, and NFT operations.
