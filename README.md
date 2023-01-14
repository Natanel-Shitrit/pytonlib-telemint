[![GPLv3 License](https://img.shields.io/badge/License-GPL%20v3-yellow.svg)](https://opensource.org/licenses/)
# PyTONLib-Telemint

*[PyTONLib](https://github.com/toncenter/pytonlib)* utility for [*Telemint* NFTs](https://github.com/TelegramMessenger/telemint).

---
*Telemint* is the smart contract that Telegram uses in [Fragment.com](https://fragment.com/) for auctioning NFTs. \
*PyTONLib* is a standalone Python library based on `libtonlibjson`.
## Features

Read data from NFT:
##### • Token Name
- Phone Number for `Anonymous Telegram Numbers`
- Username for `Telegram Usernames`

##### • Auction State
- Bidder address
- Highest Bid
- Last Bid Timestamp
- Minimum Bid
- Auction End Timestamp

##### • Auction Config
- Beneficiary Address
- Initial Minimum Bid
- Maximum Bid
- Minimum Bid Step
- Minimum Extened Time
## Installation

Install `pytonlib-telemint` with pip:

```bash
pip install pytonlib-telemint
```
## Usage / Examples

```py
from pytonlib_telemint import TelemintNFT

# 'client' is an initialized 'TonlibClient' instance.

nft = TelemintNFT('EQBqs8pl1dJOZeXC3lspnYneBHag7VbQ9zKkv4IpQT3nnn5g')
print(nft)
# Output: TelemintNFT at EQBqs8pl1dJOZeXC3lspnYneBHag7VbQ9zKkv4IpQT3nnn5g

await nft.init(client)
print(nft)
""" Output:
Token Name: dage
Auction State: {
   'bidder_address': 'EQAV4pVmtxgOXz-Aj241MUePgGAjkn7znrHZRXb6cCGiRJ_b',
   'bid': 5050000000000,
   'bid_ts': 1673275014,
   'min_bid': 5302500000000,
   'end_time': 1673879814
}
Auction Config: {
  'beneficiary_address': 'EQBAjaOyi2wGWlk-EDkSabqqnF-MrrwMadnwqrurKpkla9nE',
  'initial_min_bid': 5050000000000,
  'max_bid': 0,
  'min_bid_step': 5,
  'min_extend_time': 3600,
  'duration': 604800
}
"""
```
###### See [PyTONLib Examples](https://github.com/toncenter/pytonlib#examples) for PyTONLib usage.
## Feedback

If you have any feedback, please reach out at [Telegram](https://natisht.t.me/).


## Acknowledgements

 - [TON](https://github.com/ton-blockchain/ton)
 - [PyTONLib](https://github.com/toncenter/pytonlib)
 - [`TON Dev Chat` On Telegram](https://t.me/tondev_eng)
## Authors

- [@Natanel-Shitrit](https://github.com/Natanel-Shitrit)
