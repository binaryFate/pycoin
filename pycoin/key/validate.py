
import binascii
from .. import encoding
from ..networks.registry import network_codes, network_prefixes
from ..serialize import h2b

DEFAULT_ADDRESS_TYPES = ["address", "pay_to_script"]


def netcode_and_type_for_data(data, netcodes=None):
    """
    Given some already-decoded raw data from a base58 string,
    return (N, T) where N is the network code ("BTC" or "LTC") and
    T is the data type ("wif", "address", "public_pair", "prv32", "pub32").
    May also raise EncodingError.
    """
    if netcodes is None:
        netcodes = network_codes()
    prefixes = network_prefixes()
    d = {}
    for length in (4, 1):
        for netcode, the_type in prefixes.get(data[:length], []):
            d[netcode] = the_type
    for netcode in netcodes:
        v = d.get(netcode)
        if v:
            return netcode, v

    raise encoding.EncodingError("unknown prefix")


def netcode_and_type_for_text(text):
    # check for "public pair"
    try:
        LENGTH_LOOKUP = {
            33: "public_pair",
            65: "public_pair",
            16: "elc_seed",
            32: "elc_prv",
            64: "elc_pub",
        }
        as_bin = h2b(text)
        l = len(as_bin)
        if l in LENGTH_LOOKUP:
            return None, LENGTH_LOOKUP[l], as_bin
    except (binascii.Error, TypeError):
        pass

    data = encoding.a2b_hashed_base58(text)
    netcode, the_type = netcode_and_type_for_data(data)
    length = 1 if the_type in ["wif", "address", "pay_to_script"] else 4
    return netcode, the_type, data[length:]


def _check_against(text, expected_type, allowable_netcodes):
    if allowable_netcodes is None:
        allowable_netcodes = network_codes()
    try:
        data = encoding.a2b_hashed_base58(text)
        netcode, the_type = netcode_and_type_for_data(data, netcodes=allowable_netcodes)
        if the_type in expected_type and netcode in allowable_netcodes:
            return netcode
    except encoding.EncodingError:
        pass
    return None


def is_address_valid(address, allowable_types=DEFAULT_ADDRESS_TYPES, allowable_netcodes=None):
    """
    Accept an address, and a list of allowable address types (a subset of "address" and "pay_to_script"),
    and allowable networks (defaulting to just Bitcoin mainnet), return the network that the address is
    a part of, or None if it doesn't validate.
    """
    return _check_against(address, allowable_types, allowable_netcodes)


def is_wif_valid(wif, allowable_netcodes=None):
    """
    Accept a WIF, and a list of allowable networks (defaulting to just Bitcoin mainnet), return
    the network that the wif is a part of, or None if it doesn't validate.
    """
    return _check_against(wif, ["wif"], allowable_netcodes)


def is_public_bip32_valid(hwif, allowable_netcodes=None):
    """
    Accept a text representation of a BIP32 public wallet, and a list of allowable networks (defaulting
    to just Bitcoin mainnet), return the network that the wif is a part of, or None if it doesn't validate.
    """
    return _check_against(hwif, ["pub32"], allowable_netcodes)


def is_private_bip32_valid(hwif, allowable_netcodes=None):
    """
    Accept a text representation of a BIP32 private wallet, and a list of allowable networks (defaulting
    to just Bitcoin mainnet), return the network that the wif is a part of, or None if it doesn't validate.
    """
    return _check_against(hwif, ["prv32"], allowable_netcodes)
