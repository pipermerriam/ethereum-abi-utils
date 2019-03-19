import pytest

from eth_abi import (
    encode_abi,
)
from eth_abi.grammar import (
    parse,
)

from ..common.unit import (
    CORRECT_TUPLE_ENCODINGS,
)


@pytest.mark.parametrize(
    'type_str,python_value,abi_encoding,_',
    CORRECT_TUPLE_ENCODINGS,
)
def test_encode_abi(type_str, python_value, abi_encoding, _):
    abi_type = parse(type_str)
    if abi_type.arrlist is not None:
        pytest.skip('ABI coding functions do not support array types')

    types = [t.to_type_str() for t in abi_type.components]

    actual = encode_abi(types, python_value)
    assert actual == abi_encoding
