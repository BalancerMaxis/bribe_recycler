import re
from typing import Dict
from typing import Optional

from gql import gql
from web3 import Web3

from recycler.data_collectors.transports import make_gql_client

from bal_addresses import AddrBook


flatbook = AddrBook("mainnet").flatbook

SNAPSHOT_GQL_API_URL = "https://hub.snapshot.org/graphql"
SNAPSHOT_STATE_CLOSED = "closed"
SNAPSHOT_MIN_AMOUNT_POOLS = 10

GET_ACTIVE_PROPOSALS_Q = lambda first, skip, space: gql(
    f"""
query {{
  proposals (
    first: {first},
    skip: {skip},
    where: {{
      space_in: ["{space}"],
      state: "closed"
      network_in: ["1"]
    }},
    orderBy: "created",
    orderDirection: asc
  ) {{
    id
    title
    body
    start
    end
    snapshot
    choices
    network
    state
    space {{
      id
      name
    }}
  }}
}}
"""
)

GET_PROPOSAL_VOTES_Q = lambda first, skip, snapshot_id, voter, space: gql(
    f"""
query {{
votes(
    first: {first},
    skip: {skip},
    where: {{
      space_in: ["{space}"],
      proposal_in: ["{snapshot_id}"],
      voter: "{voter}"
    }},
    orderBy: "created",
    orderDirection: asc
  ) {{
    voter
    proposal {{
      id
    }}
    choice
  }}
}}
"""
)


def get_previous_snapshot_round(
    web3: Web3, space: Optional[str] = "gauges.aurafinance.eth"
) -> Dict:
    """
    Using title re match and some pool heuristics, tries to get past
    gauge voting proposal. If not found, returns None
    :params:
    - web3: Web3 instance with valid node url
    - space: Snapshot space to query
    """
    client = make_gql_client(SNAPSHOT_GQL_API_URL)
    limit = 100
    offset = 0
    while True:
        result = client.execute(
            GET_ACTIVE_PROPOSALS_Q(first=limit, skip=offset, space=space)
        )
        offset += limit
        if not result or not result.get("proposals"):
            break
        gauge_proposal = None
        for proposal in result["proposals"]:
            if proposal["state"] != SNAPSHOT_STATE_CLOSED:
                continue
            match = re.match(r"Gauge Weight for Week of .+", proposal["title"])
            number_of_choices = len(proposal["choices"])
            current_timestamp = web3.eth.get_block(web3.eth.get_block_number())[
                "timestamp"
            ]
            timestamp_two_weeks_ago = current_timestamp - (60 * 60 * 24 * 7 * 2)
            # Use heuristics to find out the latest gauge proposal since there is no other way
            # to filter out proposals
            if match and number_of_choices > SNAPSHOT_MIN_AMOUNT_POOLS:
                # Sanity check: proposal should end within timeframe of past two weeks
                if timestamp_two_weeks_ago < proposal["end"] < current_timestamp:
                    gauge_proposal = proposal
                    break
        return gauge_proposal


def get_votes_from_snapshot(snapshot: str) -> Optional[Dict]:
    """
    Takes in snapshot id and returns all votes for the current value of MSIG_VOTER constant
    :param snapshot:  Snapshot id to query
    """
    client = make_gql_client(SNAPSHOT_GQL_API_URL)
    limit = 100
    offset = 0
    votes = None
    while True:
        result = client.execute(
            GET_PROPOSAL_VOTES_Q(
                first=limit,
                skip=offset,
                snapshot_id=snapshot,
                voter=flatbook["multisigs/vote_incentive_recycling"],
                space="gauges.aurafinance.eth",
            )
        )
        offset += limit
        if not result or not result["votes"]:
            break
        votes = result["votes"][0]
        if not votes:
            continue
        votes = votes["choice"]

    return votes
