from typing import Optional, Dict
from pytonlib import TonlibClient
from pytonlib.utils.tlb import parse_tlb_object, MsgAddressInt
from pytonlib.utils.address import detect_address
from pytonlib.utils.tlb import Slice
from bitarray.util import ba2int
from enum import Enum

# https://github.com/TelegramMessenger/telemint/blob/main/func/common.fc#L30-L54
# Error values.
class TelemintErrorCode(Enum):
    UNKNOWN_ERROR = -1
    SUCCESS = 0
    SUCCESS_ALT = 1
    INVALID_LENGTH = 201
    INVALID_SIGNATURE = 202
    WRONG_SUBWALLET_ID = 203
    NOT_YET_VALID_SIGNATURE = 204
    EXPIRED_SIGNATURE = 205
    NOT_ENOUGH_FUNDS = 206
    WRONG_TOPUP_COMMENT = 207
    UNKNOWN_OP = 208
    UNINITED = 210
    TOO_SMALL_STAKE = 211
    EXPECTED_ONCHAIN_CONTENT = 212
    FORBIDDEN_NOT_DEPLOY = 213
    FORBIDDEN_NOT_STAKE = 214
    FORBIDDEN_TOPUP = 215
    FORBIDDEN_TRANSFER = 216
    FORBIDDEN_CHANGE_DNS = 217
    FORBIDDEN_TOUCH = 218
    NO_AUCTION = 219
    FORBIDDEN_AUCTION = 220
    ALREADY_HAS_STAKES = 221
    AUCTION_ALREADY_STARTED = 222
    INVALID_AUCTION_CONFIG = 223
    INCORRECT_WORKCHAIN = 333
    NO_FIRST_ZERO_BYTE = 413
    BAD_SUBDOMAIN_LENGTH = 70

    @classmethod
    def _missing_(cls, value):
        return cls(cls.UNKNOWN_ERROR)


# Exception
class MethodError(Exception):
    """Raised when method didn't exited successfully."""
    def __init__(self, method_name: str, exit_code: int) -> None:
        self.method_name: str = method_name
        self.exit_code: TelemintErrorCode = TelemintErrorCode(exit_code)
        print(f'Method "{self.method_name}" exited with {self.exit_code}')


# TL-B Objects
# https://github.com/TelegramMessenger/telemint/blob/main/telemint.tlb#L25
class TelemintText:
    """
    telemint_text$_ len:(## 8) text:(bits (len * 8)) = TelemintText;
    """
    def __init__(self, cell_slice: Slice):
        self.text = cell_slice.read_next(cell_slice.bits_left()).tobytes().decode()


# Unused TL-B Objects
# https://github.com/TelegramMessenger/telemint/blob/main/telemint.tlb#L20
class TeleitemLastBid:
    """
    teleitem_last_bid bidder_address:MsgAddressInt bid:Grams bid_ts:uint32 = TeleitemLastBid;
    """
    def __init__(self, cell_slice: Slice):
        self.bidder_address = MsgAddressInt(cell_slice)
        self.bid = cell_slice.read_var_uint(16)
        self.bid_ts = ba2int(cell_slice.read_next(32), signed=False)


# https://github.com/TelegramMessenger/telemint/blob/main/telemint.tlb#L21
class TeleitemAuctionState:
    """
    teleitem_auction_state$_ last_bid:(Maybe ^TeleitemLastBid) min_bid:Grams end_time:uint32 = TeleitemAuctionState;
    """
    def __init__(self, cell_slice: Slice):
        self.last_bid = TeleitemLastBid(cell_slice.read_next_ref()) if cell_slice.read_next(1).any() else None
        self.min_bid = cell_slice.read_var_uint(16)
        self.end_time = ba2int(cell_slice.read_next(32), signed=False)


# TODO: Implement base class for NFT?
# https://github.com/TelegramMessenger/telemint
class TelemintNFT:
    GET_METHOD_PREFIX = 'get_telemint_'

    def __init__(self, address: str) -> None:
        self.address: str = address
        
        # Telemint NFT data.
        self.token_name: Optional[str] = None
        self.auction_state: Optional[Dict] = None
        self.auction_config: Optional[Dict] = None
        
        # Other.
        self._data_loaded: bool = False

    def __str__(self) -> str:
        return f'TelemintNFT at {self.address}\n' + \
              (f'Token Name: {self.token_name}\n' \
               f'Auction State: {self.auction_state}\n' \
               f'Auction Config: {self.auction_config}' \
                if self._data_loaded else '')

    # Initialize.
    async def init(self, client: TonlibClient) -> None:
        # Load data.
        self.token_name = await self._load_token_name(client)
        self.auction_state = await self._load_auction_state(client)
        
        # If auction state is None there will be no auction config!
        if self.auction_state is not None:
            self.auction_config = await self._load_auction_config(client)

        # Mark as loaded.
        self._data_loaded = True

    # Data loaders.
    async def _load_token_name(self, client: TonlibClient) -> None:
        """
        returns:
            str: token_name
        """
        try:
            raw_response: Dict = await self._get(client, 'token_name')
        except MethodError as e:
            # Should handle exceptions for non-telemint NFTs?
            raise e
        
        return parse_tlb_object(read_stack_cell(raw_response['stack'][0]), TelemintText)['text']
    
    async def _load_auction_state(self, client: TonlibClient) -> Dict:
        """
        returns: {
            str: bidder_address,
            int: bid,
            int: bid_ts,
            int: min_bid,
            int: end_time
        }
        """
        try:
            raw_response = await self._get(client, 'auction_state')
        except MethodError as e:
            # exit code 219 = no auction is live.
            if e.exit_code == TelemintErrorCode.NO_AUCTION:
                return None

            # Should handle exceptions for non-telemint NFTs?
            raise e
        
        bidder_address_int = parse_tlb_object(read_stack_cell(raw_response['stack'][0]), MsgAddressInt)

        return {
            'bidder_address': _address_to_bounceable_b64url(bidder_address_int),
            'bid': read_stack_num(raw_response['stack'][1]),
            'bid_ts': read_stack_num(raw_response['stack'][2]),
            'min_bid': read_stack_num(raw_response['stack'][3]),
            'end_time': read_stack_num(raw_response['stack'][4]),
        }
    
    async def _load_auction_config(self, client: TonlibClient):
        """
        returns: {
            str: beneficiary_address,
            int: initial_min_bid,
            int: max_bid,
            int: min_bid_step,
            int: min_extend_time,
            int: duration,
        }
        """
        try:
            raw_response = await self._get(client, 'auction_config')
        except MethodError as e:
            # Should handle exceptions for non-telemint NFTs?
            raise e
        
        beneficiary_address_int = parse_tlb_object(read_stack_cell(raw_response['stack'][0]), MsgAddressInt)
        
        return {
            'beneficiary_address': _address_to_bounceable_b64url(beneficiary_address_int),
            'initial_min_bid': read_stack_num(raw_response['stack'][1]),
            'max_bid': read_stack_num(raw_response['stack'][2]),
            'min_bid_step': read_stack_num(raw_response['stack'][3]),
            'min_extend_time': read_stack_num(raw_response['stack'][4]),
            'duration': read_stack_num(raw_response['stack'][5]),
        }


    # Helpers.
    async def _get(self, client: TonlibClient, get_object: str, stack_data: list = []):
        method = f"{self.GET_METHOD_PREFIX}{get_object}"
        raw_response = await client.raw_run_method(
            address=self.address,
            method=method,
            stack_data=stack_data
        )

        if raw_response['exit_code'] != TelemintErrorCode.SUCCESS.value:
            raise MethodError(method, raw_response['exit_code'])

        return raw_response


def read_stack_num(entry: list):
    assert entry[0] == 'num'
    return int(entry[1], 16)


def read_stack_cell(entry: list):
    assert entry[0] == 'cell'
    return entry[1]['bytes']


def _address_to_bounceable_b64url(address):
    return detect_address(f"{address['workchain_id']}:{address['address']}")['bounceable']['b64url']
