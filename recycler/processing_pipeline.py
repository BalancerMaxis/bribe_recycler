from dataclasses import dataclass, field
from typing import List, Dict

from web3 import Web3
from dotenv import load_dotenv

from recycler.data_collectors.snapshot_collectors import (
    get_votes_from_snapshot,
    get_previous_snapshot_round,
)
from recycler.data_collectors.hh_bribes import fetch_hh_aura_bribs


load_dotenv()


@dataclass
class PoolLabel:
    label: str
    title: str = field(init=False)
    tokens: List[str] = field(init=False)

    def __post_init__(self):
        self.title, self.tokens = self._parse_label()

    def _parse_label(self):
        label = self.label.split()

        if len(label) == 1:
            # case (PoolName)
            return label[0], []
        if len(label) == 2:
            # case (PoolType tokenA/tokenB)
            return (
                label[0],
                label[1].split("/"),
            )
        else:
            # case (PoolType tokenA/tokenB (0x....))
            if "(0x" in label[-1]:
                return label[0], label[1].split("/")

            # just fallback to matching the entire label
            return "".join(label), []

    def __eq__(self, other):
        if not isinstance(other, PoolLabel):
            return NotImplemented

        return self.title == other.title and sorted(self.tokens) == sorted(other.tokens)


def recycle_bribes(web3: Web3, usdc_amount: int) -> Dict[str, int]:
    prev_round = get_previous_snapshot_round(web3)
    votes = get_votes_from_snapshot(prev_round["id"])
    bribes = fetch_hh_aura_bribs()

    bribe_amounts = {}

    for vote_index, vote_weight in votes.items():
        vote_label = PoolLabel(prev_round["choices"][int(vote_index) - 1])
        for bribe in bribes:
            bribe_label = PoolLabel(bribe["title"])
            if vote_label == bribe_label:
                bribe_amount = int(usdc_amount * (vote_weight / 100))
                bribe_amounts[bribe["proposalHash"]] = bribe_amount
                break

    assert sum(bribe_amounts.values()) <= usdc_amount
    return bribe_amounts
