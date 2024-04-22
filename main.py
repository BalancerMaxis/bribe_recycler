import os
import argparse

from web3 import Web3
from dotenv import load_dotenv

from recycler.processing_pipeline import recycle_bribes
from recycler.tx_builder.builder import build_tx


load_dotenv()

module_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(module_dir, "output")

RECYCLE_PCT = 0.7


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("amount", type=int, help="USDC to recycle")
    usdc_amount = int(parser.parse_args().amount * 1e6)

    web3 = Web3(Web3.HTTPProvider(os.getenv("ETHNODEURL")))

    recycle_usdc_amount = int(usdc_amount * RECYCLE_PCT)
    dao_usdc_amount = int(usdc_amount - recycle_usdc_amount)

    bribe_amounts = recycle_bribes(web3, recycle_usdc_amount)
    build_tx(dao_usdc_amount, bribe_amounts, output_dir)


if __name__ == "__main__":
    main()
