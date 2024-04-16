import os
from typing import List, Dict
import json
from datetime import date

from bal_addresses import AddrBook


flatbook = AddrBook("mainnet").flatbook
usdc = flatbook["tokens/USDC"]
balancer_briber = flatbook["hidden_hand2/balancer_briber"]
bribe_vault = flatbook["hidden_hand2/bribe_vault"]
dao_msig = flatbook["multisigs/dao"]
fee_msig = flatbook["multisigs/fees"]

module_dir = os.path.dirname(os.path.abspath(__file__))

base_tx_template_path = os.path.join(module_dir, "templates/base_template.json")
erc20_approve_path = os.path.join(module_dir, "templates/erc20_approve.json")
erc20_transfer_path = os.path.join(module_dir, "templates/erc20_transfer.json")
bribe_balancer_path = os.path.join(module_dir, "templates/bribe_balancer.json")


def erc20_approve(tx_list: List[Dict], to: str, spender: str, amount: int) -> None:
    with open(erc20_approve_path) as f:
        payload = json.load(f)

    payload["to"] = to
    payload["contractInputsValues"]["spender"] = spender
    payload["contractInputsValues"]["rawAmount"] = str(amount)

    tx_list.append(payload)


def erc20_transfer(tx_list: List[Dict], to: str, receiver: str, amount: int) -> None:
    with open(erc20_transfer_path) as f:
        payload = json.load(f)

    payload["to"] = to
    payload["contractInputsValues"]["to"] = receiver
    payload["contractInputsValues"]["value"] = str(amount)

    tx_list.append(payload)


def bribe_balancer(tx_list: List[Dict], to: str, bribe_amounts: Dict) -> None:
    with open(bribe_balancer_path) as f:
        payload = json.load(f)

    payload["to"] = to

    for prop, amount in bribe_amounts.items():
        payload["contractInputsValues"]["_token"] = flatbook["tokens/USDC"]
        payload["contractInputsValues"]["_proposal"] = prop
        payload["contractInputsValues"]["_amount"] = str(amount)
        tx_list.append(payload)


def build_tx(dao_fee, bribe_amounts, output_dir) -> None:
    with open(base_tx_template_path) as f:
        tx = json.load(f)
        tx["meta"]["createdFromSafeAddress"] = fee_msig
        tx_list = []

    # dao fee
    erc20_transfer(tx_list, usdc, dao_msig, dao_fee)

    # hh bribes
    erc20_approve(tx_list, usdc, bribe_vault, sum(bribe_amounts.values()))
    bribe_balancer(tx_list, balancer_briber, bribe_amounts)

    tx["transactions"] = tx_list

    with open(f"{output_dir}/{date.today()}.json", "w") as f:
        json.dump(tx, f)
