# Solana setup for Startup CLI

This guide walks you through setting up Solana for the Startup CLI (Devnet, keypairs, and API).

---

## 1. Choose your network: Devnet

The app uses **Solana Devnet** by default (testnet — no real SOL). No config needed unless you want a custom RPC.

- **Default RPC:** `https://api.devnet.solana.com`
- **Optional:** Set `SOLANA_RPC_URL` in `.env` if you use a different Devnet RPC (e.g. Helius, QuickNode).

---

## 2. Get a keypair or vault address

You need a **keypair** for the server to create mints and (optionally) sign buy transfers. For **vault_owner** (the wallet that holds the pre-minted supply), you can use either a keypair-based address or **your Phantom wallet address** — no `solana-keygen` required for the vault.

### Option A: Use your Phantom wallet as vault_owner (project creator owns the supply)

**Whoever creates the project can own the majority (or all) of the tokens** by passing their Phantom address as `vault_owner`. The full supply (e.g. 100,000 tokens) is minted **to that wallet** — the platform only pays for the mint and does not hold the tokens. So the person adding the project (the creator) receives all shares in their Phantom.

If you want the pre-minted tokens to live in **your Phantom wallet**:

1. **Set Phantom to Devnet**  
   Phantom → Settings → Developer Settings → Testnet Mode → Solana **Devnet**.

2. **Get your Phantom public address**  
   Open Phantom, open the main wallet view, and tap/click your address to copy it (or use the “Receive” / “Deposit” screen). It looks like `9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM`.

3. **Use that address as `vault_owner`**  
   - **API:** When creating a project or mint, send `"vault_owner": "YourPhantomAddress"` in the request body.  
   - Tokens are minted to your Phantom wallet’s token account; the platform still pays for mint creation.

4. **Devnet SOL in Phantom**  
   Get Devnet SOL so your Phantom wallet can pay fees when you sign (e.g. for sells): https://faucet.solana.com → Devnet → paste your Phantom address.

5. **Buy when vault is Phantom**  
   When the vault is your Phantom wallet, the server must sign a transfer **from** that vault to the buyer. So for **buy** you must either:
   - Send the vault owner’s keypair in the buy request (`keypair_base64` = Phantom export), or  
   - Use a “sign with Phantom” buy flow if the app supports it (vault owner signs in the browser).  
   For **sell**, users already sign with Phantom; no change.

You do **not** need `solana-keygen` for the vault if you use your Phantom address as `vault_owner`. You still need a **platform keypair** (Option B or C below) for the server to create mints and pay for them.

### Option B: Solana CLI (for server/platform keypair)

1. **Install Solana CLI**  
   - macOS/Linux: `sh -c "$(curl -sSfL https://release.solana.com/stable/install)"`  
   - Windows: see [Solana docs](https://docs.solana.com/cli/install-solana-cli-tools).  
   Then restart your terminal.

2. **Confirm it’s on Devnet**
   ```bash
   solana config set --url devnet
   solana config get
   ```
   You should see `RPC URL: https://api.devnet.solana.com`.

3. **Create a new keypair** (or use existing)
   ```bash
   # New keypair; default path is ~/.config/solana/id.json
   solana-keygen new
   ```
   Or use a specific path:
   ```bash
   solana-keygen new -o ~/my-platform-keypair.json
   ```

4. **Get your public key (wallet address)**
   ```bash
   solana address
   # or with custom path:
   solana address -k ~/my-platform-keypair.json
   ```
   Use this address as the platform keypair (e.g. `PLATFORM_KEYPAIR_PATH`) or as `vault_owner` if you want the server wallet to hold the supply.

### Option C: Use an existing keypair file

If you already have a keypair JSON (e.g. from Phantom export or another tool), use its path. The file must be a JSON array of 64 bytes (Solana standard).

---

## 3. Get Devnet SOL (for fees)

Creating mints and sending transactions costs a small amount of SOL. On Devnet you get free SOL from a faucet.

1. **Get your wallet address** (from step 2 — Phantom address, or `solana address` if using CLI keypair):
   ```bash
   solana address
   ```

2. **Request airdrop**
   ```bash
   solana airdrop 2
   ```
   Or use the web faucet: open **https://faucet.solana.com**, choose **Devnet**, paste your address, and request SOL.

3. **Check balance**
   ```bash
   solana balance
   ```

---

## 4. Configure the Startup CLI / API

### For CLI only

- Use the keypair path when you run commands:
  ```bash
  startup-cli create-mint --project-id 1 --keypair ~/.config/solana/id.json
  startup-cli buy-tokens --project-id 1 --amount 10 --buyer <PUBKEY> --keypair ~/.config/solana/id.json
  ```

### For API (automatic create-mint and buy without user keypairs)

Set **one** of these in your environment (e.g. in `.env`):

**Option 1: Path to keypair file**

```bash
# In .env (copy from .env.example)
PLATFORM_KEYPAIR_PATH=~/.config/solana/id.json
```

On Windows use a full path, e.g. `PLATFORM_KEYPAIR_PATH=C:\Users\You\.config\solana\id.json`.

**Option 2: Base64 keypair (e.g. for AWS or Docker)**

Encode your keypair file to base64:

```bash
# Linux/macOS (keypair file path)
python3 -c "import base64,json; f=open('$HOME/.config/solana/id.json'); d=json.load(f); print(base64.b64encode(bytes(d)).decode())"
```

Or in Python, with your keypair path:

```python
import base64, json
with open("/path/to/id.json") as f:
    data = json.load(f)
print(base64.b64encode(bytes(data)).decode())
```

Then in `.env`:

```bash
PLATFORM_KEYPAIR_BASE64=<paste_the_base64_string>
```

**Load `.env`**

- Linux/macOS: `export $(grep -v '^#' .env | xargs)`  
- Windows PowerShell: run the snippet from `.env.example` to load vars into the process.  
- Or use `python-dotenv` in your app so the server reads `.env` automatically.

---

## 5. Vault owner address

- **When you create a project/mint with the API** and do **not** pass `vault_owner`, the vault is the **platform keypair’s public key** (same as `solana address -k <your-keypair-path>`).
- **When you pass `vault_owner`** in the API, that address is the vault (tokens are minted to that wallet’s token account).
- **To see the vault address for a project:**  
  `GET /projects/{id}/vault` or `GET /projects/{id}/addresses` (field `vault_owner`).
- **CLI:** If a project has no vault stored (e.g. created before that feature), run:
  ```bash
  startup-cli vault-owner --keypair ~/.config/solana/id.json
  ```
  Use that address as `--vault-authority` when selling.

---

## 6. Phantom wallet (optional, for testing buy/sell)

For testing with a browser wallet (no keypair file on server):

1. **Install Phantom**  
   https://phantom.app/

2. **Switch to Devnet**  
   Phantom → Settings → Developer Settings → turn on **Testnet Mode** → under Solana choose **Devnet**.

3. **Get Devnet SOL in Phantom**  
   Copy your Phantom wallet address, then use https://faucet.solana.com (Devnet) to airdrop SOL to that address.

4. **Use with the app**  
   - **GUI:** “Connect Phantom” opens a local page; connect there, then Buy/Sell in the app.  
   - **API:** Use Phantom’s public key as `buyer_pubkey` or `seller_pubkey`; for sell, use the prepare → sign in Phantom → confirm flow (see API_ENDPOINTS.md).

---

## 7. Quick checklist

| Step | What to do |
|------|------------|
| 1 | Use Devnet (default; optional: set `SOLANA_RPC_URL` in `.env`) |
| 2 | **Vault:** Use Phantom address as `vault_owner` (copy from Phantom; no keygen), or use a keypair address (Option B/C) |
| 3 | **Platform keypair:** For API create-mint, set `PLATFORM_KEYPAIR_PATH` or `PLATFORM_KEYPAIR_BASE64` (Solana CLI keypair or exported keypair) |
| 4 | Get Devnet SOL: `solana airdrop 2` (for platform keypair) and/or faucet.solana.com (for Phantom) |
| 5 | Run `startup-cli serve`; create projects with `"vault_owner": "YourPhantomAddress"` to mint into Phantom |
| 6 | Optional: Phantom on Devnet + faucet SOL for testing and for using Phantom as vault |

---

## 8. Troubleshooting

- **“PLATFORM_KEYPAIR not set”**  
  Set either `PLATFORM_KEYPAIR_PATH` or `PLATFORM_KEYPAIR_BASE64` in `.env` and ensure the process loads it (e.g. `export` or python-dotenv).

- **“Insufficient funds” / transaction fails**  
  Get more Devnet SOL: `solana airdrop 2` or https://faucet.solana.com (Devnet).

- **“Project has no vault_owner”**  
  Create the mint with this app (so vault is stored), or run `startup-cli vault-owner --keypair <path>` and use that as `--vault-authority` when selling.

- **Phantom shows mainnet**  
  In Phantom: Developer Settings → Testnet Mode → Solana → **Devnet**. This app only sends transactions to Devnet.
