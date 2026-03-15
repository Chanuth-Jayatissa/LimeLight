"""
Tkinter GUI for Startup CLI: view trading price and run all features from one place.

Price is driven by the bonding curve: more buys -> higher price, more sells -> lower price.
Connect Phantom in the browser to buy/sell without exporting your keypair.
"""
from __future__ import annotations

import base64
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any

# Import backend (same as CLI)
from pathlib import Path

from . import state
from . import bonding_curve
from .bonding_curve import DEFAULT_CURVE_TYPE, DEFAULT_INITIAL_PRICE, derive_curve_params
from .addresses import get_project_addresses
from .solana_mint import (
    get_client,
    get_client_devnet,
    load_keypair,
    create_mint_for_project,
    mint_tokens_to_buyer,
    transfer_tokens_to_vault,
    build_unsigned_sell_transaction,
    submit_signed_transaction,
)
from .state import set_project_mint, set_project_token_metadata, update_project_tokens_and_treasury
from .ipfs_upload import upload_to_ipfs, get_devnet_mint_url
from .token_metadata import write_metadata_json
from .phantom_server import (
    start_phantom_server,
    phantom_server_url,
    get_phantom_state,
    set_pending_tx_for_phantom,
    wait_for_phantom_signed,
)

from solders.pubkey import Pubkey


def _get_current_price(project: dict[str, Any]) -> float | None:
    """Current price per token from bonding curve; None if invalid."""
    try:
        return bonding_curve.get_current_price(
            curve_type=project["curve_type"],
            base_price=project["initial_price"],
            tokens_sold=project["tokens_sold"],
            price_increment=project.get("price_increment"),
            k=project.get("k"),
        )
    except Exception:
        return None


def _price_after_buy(project: dict[str, Any], amount: int) -> tuple[float, float] | None:
    """(cost_sol, price_after) or None."""
    try:
        return bonding_curve.calculate_purchase_cost(
            curve_type=project["curve_type"],
            base_price=project["initial_price"],
            tokens_sold=project["tokens_sold"],
            amount=amount,
            price_increment=project.get("price_increment"),
            k=project.get("k"),
        )
    except Exception:
        return None


def _value_after_sell(project: dict[str, Any], amount: int) -> float | None:
    """SOL value when selling `amount` at current price."""
    try:
        price = _get_current_price(project)
        return price * amount if price is not None else None
    except Exception:
        return None


class StartupApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Startup CLI — Token Price & Actions")
        self.root.minsize(720, 520)
        self.root.geometry("900x580")

        self._selected_project_id: int | None = None
        self._build_ui()
        self._refresh_project_list()

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Top: project list (left) and detail (right)
        paned = ttk.PanedWindow(main, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(paned)
        paned.add(left, weight=0)
        ttk.Label(left, text="Projects").pack(anchor=tk.W)
        self._listbox = tk.Listbox(left, height=12, width=28, font=("Segoe UI", 10))
        self._listbox.pack(fill=tk.BOTH, expand=True, pady=(2, 6))
        self._listbox.bind("<<ListboxSelect>>", self._on_select_project)
        ttk.Button(left, text="Refresh list", command=self._refresh_project_list).pack(anchor=tk.W)

        right = ttk.Frame(paned, padding=(10, 0))
        paned.add(right, weight=1)

        # ——— Price (big and visible) ———
        price_frame = ttk.LabelFrame(right, text="Current token price (bonding curve)", padding=8)
        price_frame.pack(fill=tk.X, pady=(0, 8))
        self._price_var = tk.StringVar(value="—")
        self._price_label = ttk.Label(price_frame, textvariable=self._price_var, font=("Segoe UI", 22))
        self._price_label.pack(anchor=tk.W)
        ttk.Label(
            price_frame,
            text="Buy tokens → price goes up. Sell tokens → price goes down.",
            font=("Segoe UI", 9),
            foreground="gray",
        ).pack(anchor=tk.W)

        # ——— Phantom wallet ———
        phantom_frame = ttk.LabelFrame(right, text="Phantom wallet (use Devnet / testnet)", padding=8)
        phantom_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(phantom_frame, text="Set Phantom to Devnet: Settings → Developer Settings → Testnet Mode → Solana Devnet.", font=("Segoe UI", 8), foreground="gray").pack(anchor=tk.W)
        self._phantom_var = tk.StringVar(value="Not connected")
        ttk.Label(phantom_frame, textvariable=self._phantom_var, font=("Segoe UI", 10)).pack(side=tk.LEFT)
        ttk.Button(phantom_frame, text="Connect Phantom", command=self._connect_phantom).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(phantom_frame, text="Refresh", command=self._refresh_phantom_status).pack(side=tk.LEFT, padx=(4, 0))

        # ——— Project details ———
        detail_frame = ttk.LabelFrame(right, text="Project details", padding=8)
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        self._detail_text = tk.Text(detail_frame, height=10, wrap=tk.WORD, font=("Consolas", 9))
        self._detail_text.pack(fill=tk.BOTH, expand=True)

        # ——— Action buttons ———
        btn_frame = ttk.Frame(right)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Create project", command=self._dialog_create_project).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_frame, text="Create mint", command=self._dialog_create_mint).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_frame, text="Buy tokens", command=self._dialog_buy).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_frame, text="Sell tokens", command=self._dialog_sell).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_frame, text="Addresses", command=self._dialog_addresses).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_frame, text="Delete project", command=self._dialog_delete).pack(side=tk.LEFT, padx=(0, 4))

        # Status
        self._status_var = tk.StringVar(value="Select a project or create one.")
        ttk.Label(main, textvariable=self._status_var, font=("Segoe UI", 9), foreground="gray").pack(anchor=tk.W)

    def _connect_phantom(self) -> None:
        port = start_phantom_server(0)
        url = phantom_server_url(port)
        webbrowser.open(url)
        self._phantom_var.set("Browser opened — set Phantom to Devnet, connect, then click Refresh.")
        self._status_var.set("In Phantom: switch to Devnet (testnet), then connect in the browser tab and click Refresh.")

    def _refresh_phantom_status(self) -> None:
        wallet = get_phantom_state().get_wallet()
        if wallet.get("connected") and wallet.get("pubkey"):
            pub = wallet["pubkey"]
            self._phantom_var.set(f"Connected: {pub[:8]}…{pub[-8:]}")
            self._status_var.set("Phantom connected. You can Buy (as buyer) or Sell (sign in browser).")
        else:
            self._phantom_var.set("Not connected")
            self._status_var.set("Select a project or create one.")

    def _refresh_project_list(self) -> None:
        self._listbox.delete(0, tk.END)
        for p in state.list_projects():
            self._listbox.insert(tk.END, f"#{p['id']} {p['name']}")
        self._status_var.set(f"Loaded {len(state.list_projects())} project(s).")

    def _on_select_project(self, event: tk.Event) -> None:
        sel = self._listbox.curselection()
        if not sel:
            return
        idx = int(sel[0])
        projects = state.list_projects()
        if idx >= len(projects):
            return
        self._selected_project_id = projects[idx]["id"]
        self._update_detail_panel()

    def _update_detail_panel(self) -> None:
        pid = self._selected_project_id
        self._detail_text.delete("1.0", tk.END)
        if pid is None:
            self._price_var.set("—")
            return
        project = state.get_project(pid)
        if not project:
            self._price_var.set("—")
            return
        price = _get_current_price(project)
        if price is not None:
            self._price_var.set(f"{price:.8f} SOL per token")
        else:
            self._price_var.set("— (check curve params)")
        lines = [
            f"Name: {project.get('name', '—')}",
            f"ID: {project['id']}",
            f"Supply: {project.get('supply', 0):,}",
            f"Tokens sold: {project.get('tokens_sold', 0):,}",
            f"Treasury: {project.get('treasury_balance', 0):.8f} SOL",
            f"Curve: {project.get('curve_type', '—')}",
            f"Mint: {project.get('mint_address') or 'Not created'}",
        ]
        self._detail_text.insert(tk.END, "\n".join(lines))
        self._status_var.set(f"Project #{pid} — price updates when you buy/sell.")

    def _get_selected_project(self) -> dict[str, Any] | None:
        if self._selected_project_id is None:
            messagebox.showwarning("No project", "Select a project first.")
            return None
        p = state.get_project(self._selected_project_id)
        if not p:
            messagebox.showerror("Error", "Project not found.")
            return None
        return p

    def _dialog_create_project(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Create project")
        win.geometry("420x420")
        f = ttk.Frame(win, padding=10)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="Name").grid(row=0, column=0, sticky=tk.W, pady=2)
        name_var = tk.StringVar()
        ttk.Entry(f, textvariable=name_var, width=40).grid(row=0, column=1, sticky=tk.EW, pady=2)
        ttk.Label(f, text="Description").grid(row=1, column=0, sticky=tk.W, pady=2)
        desc_var = tk.StringVar()
        ttk.Entry(f, textvariable=desc_var, width=40).grid(row=1, column=1, sticky=tk.EW, pady=2)
        ttk.Label(f, text="GitHub URL").grid(row=2, column=0, sticky=tk.W, pady=2)
        github_var = tk.StringVar()
        ttk.Entry(f, textvariable=github_var, width=40).grid(row=2, column=1, sticky=tk.EW, pady=2)
        ttk.Label(f, text="Supply").grid(row=3, column=0, sticky=tk.W, pady=2)
        supply_var = tk.StringVar(value="100000")
        ttk.Entry(f, textvariable=supply_var, width=15).grid(row=3, column=1, sticky=tk.W, pady=2)
        ttk.Label(f, text="Initial price (SOL), blank=0.01").grid(row=4, column=0, sticky=tk.W, pady=2)
        price_var = tk.StringVar(value="0.01")
        ttk.Entry(f, textvariable=price_var, width=15).grid(row=4, column=1, sticky=tk.W, pady=2)
        ttk.Label(f, text="Curve type (blank=linear)").grid(row=5, column=0, sticky=tk.W, pady=2)
        curve_var = tk.StringVar(value="linear")
        curve_combo = ttk.Combobox(f, textvariable=curve_var, values=["linear", "exponential"], width=12, state="readonly")
        curve_combo.grid(row=5, column=1, sticky=tk.W, pady=2)
        ttk.Label(f, text="Price increment (linear) or leave blank").grid(row=6, column=0, sticky=tk.W, pady=2)
        inc_var = tk.StringVar(value="")
        ttk.Entry(f, textvariable=inc_var, width=15).grid(row=6, column=1, sticky=tk.W, pady=2)
        ttk.Label(f, text="k (exponential) or leave blank").grid(row=7, column=0, sticky=tk.W, pady=2)
        k_var = tk.StringVar(value="")
        ttk.Entry(f, textvariable=k_var, width=15).grid(row=7, column=1, sticky=tk.W, pady=2)
        ttk.Label(f, text="Target end price (optional)").grid(row=8, column=0, sticky=tk.W, pady=2)
        target_end_var = tk.StringVar(value="")
        ttk.Entry(f, textvariable=target_end_var, width=15).grid(row=8, column=1, sticky=tk.W, pady=2)
        ttk.Label(f, text="Price multiplier (e.g. 10 = 10x at end)").grid(row=9, column=0, sticky=tk.W, pady=2)
        mult_var = tk.StringVar(value="10")
        ttk.Entry(f, textvariable=mult_var, width=15).grid(row=9, column=1, sticky=tk.W, pady=2)
        upload_ipfs_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="Upload token metadata to IPFS (set PINATA_JWT)", variable=upload_ipfs_var).grid(row=10, column=0, columnspan=2, sticky=tk.W, pady=4)
        f.columnconfigure(1, weight=1)

        def do_create() -> None:
            try:
                supply = int(supply_var.get().strip())
                price_str = price_var.get().strip()
                initial_price = float(price_str) if price_str else DEFAULT_INITIAL_PRICE
                curve_str = curve_var.get().strip().lower()
                curve = curve_str if curve_str in ("linear", "exponential") else DEFAULT_CURVE_TYPE
                if curve not in ("linear", "exponential"):
                    raise ValueError("Curve must be linear or exponential")
                inc_str = inc_var.get().strip()
                k_str = k_var.get().strip()
                price_inc = float(inc_str) if inc_str and curve == "linear" else None
                k = float(k_str) if k_str and curve == "exponential" else None
                if (curve == "linear" and price_inc is None) or (curve == "exponential" and k is None):
                    target_end = target_end_var.get().strip()
                    mult_str = mult_var.get().strip()
                    end_price = float(target_end) if target_end else None
                    mult = float(mult_str) if mult_str else 10.0
                    inc_derived, k_derived = derive_curve_params(
                        curve, initial_price, float(supply),
                        end_price=end_price,
                        price_multiplier=mult if end_price is None else None,
                    )
                    if inc_derived is not None:
                        price_inc = inc_derived
                    if k_derived is not None:
                        k = k_derived
                if curve == "linear" and price_inc is None:
                    raise ValueError("Set price increment or target end price / multiplier")
                if curve == "exponential" and k is None:
                    raise ValueError("Set k or target end price / multiplier")
            except ValueError as e:
                messagebox.showerror("Invalid input", str(e), parent=win)
                return
            name = name_var.get().strip() or "Unnamed"
            description = desc_var.get().strip() or ""
            github = github_var.get().strip() or "https://github.com"
            project = state.create_project(
                name=name,
                description=description,
                github=github,
                supply=supply,
                initial_price=initial_price,
                curve_type=curve,
                price_increment=price_inc,
                k=k,
            )
            pid = project["id"]
            t_name = name
            t_symbol = "".join(c[0].upper() for c in name.split() if c)[:10] or "TKN"
            set_project_token_metadata(pid, token_name=t_name, token_symbol=t_symbol, token_description=description, token_external_url=github)
            if upload_ipfs_var.get():
                try:
                    data_dir = Path(state.STATE_FILE).parent
                    meta_path = write_metadata_json(
                        data_dir / f"metadata_{pid}.json",
                        name=t_name,
                        symbol=t_symbol,
                        description=description,
                        image="",
                        external_url=github,
                    )
                    token_uri = upload_to_ipfs(meta_path)
                    set_project_token_metadata(pid, token_uri=token_uri)
                except Exception as e:
                    messagebox.showwarning("IPFS upload failed", str(e), parent=win)
            win.destroy()
            self._refresh_project_list()
            self._status_var.set(f"Created project #{pid}. Select it and use Create mint / Buy / Sell.")

        ttk.Button(f, text="Create", command=do_create).grid(row=11, column=1, sticky=tk.W, pady=8)
        ttk.Button(f, text="Cancel", command=win.destroy).grid(row=11, column=1, sticky=tk.W, padx=70, pady=8)

    def _dialog_create_mint(self) -> None:
        project = self._get_selected_project()
        if not project:
            return
        pid = project["id"]
        if project.get("mint_address"):
            if not messagebox.askyesno("Already has mint", "Project already has a mint. Create another anyway?", parent=self.root):
                return
        win = tk.Toplevel(self.root)
        win.title("Create mint")
        win.geometry("440x180")
        f = ttk.Frame(win, padding=10)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="Keypair path (payer / mint authority)").grid(row=0, column=0, sticky=tk.W, pady=2)
        kp_var = tk.StringVar()
        ttk.Entry(f, textvariable=kp_var, width=45).grid(row=0, column=1, sticky=tk.EW, pady=2)
        ttk.Button(f, text="Browse", command=lambda: kp_var.set(filedialog.askopenfilename(title="Keypair JSON") or kp_var.get())).grid(row=0, column=2, padx=2)
        ttk.Label(f, text="Token name (optional)").grid(row=1, column=0, sticky=tk.W, pady=2)
        name_var = tk.StringVar(value=project.get("token_name") or "")
        ttk.Entry(f, textvariable=name_var, width=45).grid(row=1, column=1, sticky=tk.EW, pady=2)
        ttk.Label(f, text="Token symbol (optional)").grid(row=2, column=0, sticky=tk.W, pady=2)
        sym_var = tk.StringVar(value=project.get("token_symbol") or "")
        ttk.Entry(f, textvariable=sym_var, width=45).grid(row=2, column=1, sticky=tk.EW, pady=2)
        ttk.Label(f, text="Token URI (optional)").grid(row=3, column=0, sticky=tk.W, pady=2)
        uri_var = tk.StringVar(value=project.get("token_uri") or "")
        ttk.Entry(f, textvariable=uri_var, width=45).grid(row=3, column=1, sticky=tk.EW, pady=2)
        f.columnconfigure(1, weight=1)

        def do_mint() -> None:
            path = kp_var.get().strip()
            if not path:
                messagebox.showerror("Error", "Keypair path required.", parent=win)
                return
            try:
                kp = load_keypair(path)
            except FileNotFoundError as e:
                messagebox.showerror("Error", str(e), parent=win)
                return
            name = name_var.get().strip() or None
            symbol = sym_var.get().strip() or None
            uri = uri_var.get().strip() or None
            supply = project.get("supply", 100_000) or 100_000
            conn = get_client()
            try:
                mint_address = create_mint_for_project(
                    conn, kp,
                    token_name=name or project.get("token_name"),
                    token_symbol=symbol or project.get("token_symbol"),
                    token_uri=uri or project.get("token_uri"),
                    initial_supply=supply,
                )
            except Exception as e:
                messagebox.showerror("Create mint failed", str(e), parent=win)
                return
            set_project_mint(pid, mint_address, vault_owner=str(kp.pubkey()))
            if name or symbol or uri:
                set_project_token_metadata(pid, token_name=name, token_symbol=symbol, token_uri=uri)
            win.destroy()
            self._update_detail_panel()
            self._status_var.set(f"Mint created: {mint_address[:16]}...")
            messagebox.showinfo("Mint created", f"Mint: {mint_address}\n\nView: {get_devnet_mint_url(mint_address)}", parent=self.root)

        ttk.Button(f, text="Create mint", command=do_mint).grid(row=4, column=1, sticky=tk.W, pady=8)
        ttk.Button(f, text="Cancel", command=win.destroy).grid(row=4, column=1, sticky=tk.W, padx=90, pady=8)

    def _dialog_buy(self) -> None:
        project = self._get_selected_project()
        if not project:
            return
        pid = project["id"]
        mint_addr = project.get("mint_address")
        if not mint_addr:
            messagebox.showwarning("No mint", "Create a mint for this project first.", parent=self.root)
            return
        win = tk.Toplevel(self.root)
        win.title("Buy tokens")
        win.geometry("440x220")
        f = ttk.Frame(win, padding=10)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="Amount (tokens)").grid(row=0, column=0, sticky=tk.W, pady=2)
        amount_var = tk.StringVar(value="10")
        amount_entry = ttk.Entry(f, textvariable=amount_var, width=15)
        amount_entry.grid(row=0, column=1, sticky=tk.W, pady=2)
        ttk.Label(f, text="Buyer wallet (pubkey)").grid(row=1, column=0, sticky=tk.W, pady=2)
        buyer_var = tk.StringVar(value=get_phantom_state().get_wallet().get("pubkey") or "")
        ttk.Entry(f, textvariable=buyer_var, width=48).grid(row=1, column=1, sticky=tk.EW, pady=2)
        ttk.Label(f, text="Mint authority keypair").grid(row=2, column=0, sticky=tk.W, pady=2)
        kp_var = tk.StringVar()
        ttk.Entry(f, textvariable=kp_var, width=45).grid(row=2, column=1, sticky=tk.EW, pady=2)
        ttk.Button(f, text="Browse", command=lambda: kp_var.set(filedialog.askopenfilename(title="Keypair JSON") or kp_var.get())).grid(row=2, column=2, padx=2)
        self._buy_preview_var = tk.StringVar(value="")
        ttk.Label(f, textvariable=self._buy_preview_var, foreground="gray").grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=4)
        amount_entry.bind("<KeyRelease>", lambda e: self._update_buy_preview(project, amount_var, self._buy_preview_var))
        f.columnconfigure(1, weight=1)

        def do_buy() -> None:
            try:
                amount = int(amount_var.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Amount must be an integer.", parent=win)
                return
            buyer = buyer_var.get().strip()
            if not buyer:
                messagebox.showerror("Error", "Buyer wallet required.", parent=win)
                return
            kp_path = kp_var.get().strip()
            if not kp_path:
                messagebox.showerror("Error", "Mint authority keypair required.", parent=win)
                return
            try:
                kp = load_keypair(kp_path)
            except FileNotFoundError as e:
                messagebox.showerror("Error", str(e), parent=win)
                return
            cost, price_after = _price_after_buy(project, amount) or (0, 0)
            if not messagebox.askyesno("Confirm buy", f"Buy {amount} tokens for ~{cost:.8f} SOL?\nPrice after: {price_after:.8f} SOL/token.", parent=win):
                return
            conn = get_client()
            try:
                sig = mint_tokens_to_buyer(conn, mint_addr, Pubkey.from_string(buyer), amount, kp, kp)
            except Exception as e:
                messagebox.showerror("Buy failed", str(e), parent=win)
                return
            update_project_tokens_and_treasury(pid, amount, cost)
            win.destroy()
            self._update_detail_panel()
            self._status_var.set(f"Bought {amount} tokens. Tx: {sig[:16]}...")
            messagebox.showinfo("Done", f"Tx: {sig}", parent=self.root)

        ttk.Button(f, text="Buy", command=do_buy).grid(row=4, column=1, sticky=tk.W, pady=8)
        ttk.Button(f, text="Cancel", command=win.destroy).grid(row=4, column=1, sticky=tk.W, padx=50, pady=8)
        self._update_buy_preview(project, amount_var, self._buy_preview_var)

    def _update_buy_preview(self, project: dict[str, Any], amount_var: tk.StringVar, out_var: tk.StringVar) -> None:
        try:
            amount = int(amount_var.get().strip())
        except ValueError:
            out_var.set("")
            return
        result = _price_after_buy(project, amount)
        if result:
            cost, price_after = result
            out_var.set(f"Cost ≈ {cost:.8f} SOL — price after buy: {price_after:.8f} SOL/token")
        else:
            out_var.set("")

    def _dialog_sell(self) -> None:
        project = self._get_selected_project()
        if not project:
            return
        pid = project["id"]
        mint_addr = project.get("mint_address")
        if not mint_addr:
            messagebox.showwarning("No mint", "This project has no mint.", parent=self.root)
            return
        phantom_pubkey = get_phantom_state().get_wallet().get("pubkey")
        win = tk.Toplevel(self.root)
        win.title("Sell tokens")
        win.geometry("500x260")
        f = ttk.Frame(win, padding=10)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="Amount (tokens)").grid(row=0, column=0, sticky=tk.W, pady=2)
        amount_var = tk.StringVar(value="10")
        amount_entry = ttk.Entry(f, textvariable=amount_var, width=15)
        amount_entry.grid(row=0, column=1, sticky=tk.W, pady=2)
        use_phantom_var = tk.BooleanVar(value=bool(phantom_pubkey))
        phantom_cb = ttk.Checkbutton(f, text="Sign with Phantom (connect in browser first)", variable=use_phantom_var)
        phantom_cb.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=4)
        ttk.Label(f, text="Or keypair (wallet holding tokens)").grid(row=2, column=0, sticky=tk.W, pady=2)
        kp_var = tk.StringVar()
        kp_entry = ttk.Entry(f, textvariable=kp_var, width=45)
        kp_entry.grid(row=2, column=1, sticky=tk.EW, pady=2)
        ttk.Button(f, text="Browse", command=lambda: kp_var.set(filedialog.askopenfilename(title="Keypair JSON") or kp_var.get())).grid(row=2, column=2, padx=2)
        ttk.Label(f, text="Vault owner (pubkey)").grid(row=3, column=0, sticky=tk.W, pady=2)
        vault_owner_var = tk.StringVar(value=project.get("vault_owner") or "")
        ttk.Entry(f, textvariable=vault_owner_var, width=48).grid(row=3, column=1, sticky=tk.EW, pady=2)
        ttk.Label(f, text="Optional if project has it; else: startup-cli vault-owner --keypair <path>", font=("Segoe UI", 8), foreground="gray").grid(row=4, column=0, columnspan=2, sticky=tk.W)
        self._sell_preview_var = tk.StringVar(value="")
        ttk.Label(f, textvariable=self._sell_preview_var, foreground="gray").grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=4)
        amount_entry.bind("<KeyRelease>", lambda e: self._update_sell_preview(project, amount_var, self._sell_preview_var))
        f.columnconfigure(1, weight=1)

        def do_sell() -> None:
            vault_owner = (vault_owner_var.get().strip() or project.get("vault_owner")) or None
            if not vault_owner:
                messagebox.showerror("Vault owner required", "Enter the vault owner pubkey (where tokens go when selling). Get it with: startup-cli vault-owner --keypair <path-to-create-mint-keypair>", parent=win)
                return
            try:
                amount = int(amount_var.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Amount must be an integer.", parent=win)
                return
            sell_value = _value_after_sell(project, amount) or 0
            if not messagebox.askyesno("Confirm sell", f"Sell {amount} tokens for ~{sell_value:.8f} SOL?\nTokens return to project vault.", parent=win):
                return
            use_phantom = use_phantom_var.get()
            seller_pubkey_phantom = get_phantom_state().get_wallet().get("pubkey") if use_phantom else None
            if use_phantom and seller_pubkey_phantom:
                # Always use Devnet for Phantom flow so the tx is built and sent to Devnet only (not mainnet)
                conn = get_client_devnet()
                try:
                    tx_bytes = build_unsigned_sell_transaction(
                        conn,
                        mint_address=mint_addr,
                        seller_pubkey=Pubkey.from_string(seller_pubkey_phantom),
                        amount=amount,
                        vault_owner_pubkey=Pubkey.from_string(vault_owner),
                    )
                    tx_b64 = base64.standard_b64encode(tx_bytes).decode("ascii")
                    set_pending_tx_for_phantom(tx_b64)
                except Exception as e:
                    messagebox.showerror("Sell failed", str(e), parent=win)
                    return
                win.destroy()
                messagebox.showinfo(
                    "Sign in browser",
                    "A transaction is ready. Sign it in the Phantom browser tab (use Devnet in Phantom), then wait for confirmation.\n\nThis app sends the transaction to Solana Devnet only, not mainnet.\n\nIf Phantom says 'insufficient SOL', get free Devnet SOL at faucet.solana.com (choose Devnet, paste your Phantom address).",
                    parent=self.root,
                )

                def wait_and_submit() -> None:
                    signed_b64 = wait_for_phantom_signed(timeout=120.0)
                    if signed_b64:
                        try:
                            signed_bytes = base64.standard_b64decode(signed_b64)
                            conn = get_client_devnet()  # Always submit to Devnet, not mainnet
                            sig = submit_signed_transaction(conn, signed_bytes)
                            update_project_tokens_and_treasury(pid, -amount, -sell_value)
                            self.root.after(0, lambda: self._update_detail_panel())
                            self.root.after(0, lambda: self._status_var.set(f"Sold {amount} tokens. Tx: {sig[:16]}..."))
                            self.root.after(0, lambda: messagebox.showinfo("Done", f"Tx: {sig}\nYou are owed ~{sell_value:.8f} SOL by the project.", parent=self.root))
                        except Exception as e:
                            err_msg = str(e)
                            self.root.after(0, lambda msg=err_msg: messagebox.showerror("Submit failed", msg, parent=self.root))
                    else:
                        self.root.after(0, lambda: messagebox.showwarning("Timeout", "No signature received. Try again.", parent=self.root))

                threading.Thread(target=wait_and_submit, daemon=True).start()
                return
            kp_path = kp_var.get().strip()
            if not kp_path:
                messagebox.showerror("Error", "Keypair path required, or connect Phantom and use Sign with Phantom.", parent=win)
                return
            try:
                kp = load_keypair(kp_path)
            except FileNotFoundError as e:
                messagebox.showerror("Error", str(e), parent=win)
                return
            conn = get_client()
            try:
                sig = transfer_tokens_to_vault(
                    conn,
                    mint_address=mint_addr,
                    seller_pubkey=kp.pubkey(),
                    amount=amount,
                    seller_keypair=kp,
                    payer=kp,
                    vault_owner_pubkey=Pubkey.from_string(vault_owner),  # from vault_owner_var / project
                )
            except Exception as e:
                messagebox.showerror("Sell failed", str(e), parent=win)
                return
            update_project_tokens_and_treasury(pid, -amount, -sell_value)
            win.destroy()
            self._update_detail_panel()
            self._status_var.set(f"Sold {amount} tokens. Tx: {sig[:16]}...")
            messagebox.showinfo("Done", f"Tx: {sig}\nYou are owed ~{sell_value:.8f} SOL by the project.", parent=self.root)

        ttk.Button(f, text="Sell", command=do_sell).grid(row=6, column=1, sticky=tk.W, pady=8)
        ttk.Button(f, text="Cancel", command=win.destroy).grid(row=6, column=1, sticky=tk.W, padx=50, pady=8)
        self._update_sell_preview(project, amount_var, self._sell_preview_var)

    def _update_sell_preview(self, project: dict[str, Any], amount_var: tk.StringVar, out_var: tk.StringVar) -> None:
        try:
            amount = int(amount_var.get().strip())
        except ValueError:
            out_var.set("")
            return
        value = _value_after_sell(project, amount)
        if value is not None:
            out_var.set(f"You receive ≈ {value:.8f} SOL (price decreases after sell)")
        else:
            out_var.set("")

    def _dialog_addresses(self) -> None:
        project = self._get_selected_project()
        if not project:
            return
        pid = project["id"]
        proj_addr, treas_addr = get_project_addresses(pid)
        mint = project.get("mint_address") or "—"
        msg = f"Project account: {proj_addr}\nTreasury: {treas_addr}\nMint: {mint}"
        if mint and mint != "—":
            msg += f"\n\nView mint: {get_devnet_mint_url(mint)}"
        messagebox.showinfo("Addresses (Devnet)", msg, parent=self.root)

    def _dialog_delete(self) -> None:
        project = self._get_selected_project()
        if not project:
            return
        pid = project["id"]
        if not messagebox.askyesno("Delete project", f"Delete project #{pid} ({project.get('name', '')}) from local state?\nOn-chain data is not removed.", parent=self.root):
            return
        if state.delete_project(pid):
            self._selected_project_id = None
            self._refresh_project_list()
            self._update_detail_panel()
            self._status_var.set("Project deleted.")
        else:
            messagebox.showerror("Error", "Could not delete project.", parent=self.root)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = StartupApp()
    app.run()


if __name__ == "__main__":
    main()
