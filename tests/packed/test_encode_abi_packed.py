import pytest

from eth_abi.grammar import (
    parse,
)
from eth_abi.packed import (
    encode_abi_packed,
)
from tests.common.unit import (
    CORRECT_TUPLE_ENCODINGS,
)


@pytest.mark.parametrize(
    'type_str,python_value,_,packed_encoding',
    CORRECT_TUPLE_ENCODINGS,
)
def test_encode_abi(type_str, python_value, _, packed_encoding):
    abi_type = parse(type_str)
    if abi_type.arrlist is not None:
        pytest.skip('ABI coding functions do not support array types')

    types = [t.to_type_str() for t in abi_type.components]

    actual = encode_abi_packed(types, python_value)
    assert actual == packed_encoding
