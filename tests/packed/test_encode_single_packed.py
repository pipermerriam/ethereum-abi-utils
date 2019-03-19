import pytest

from eth_abi.packed import (
    encode_single_packed,
)
from tests.common.unit import (
    CORRECT_SINGLE_ENCODINGS,
)


@pytest.mark.parametrize(
    'typ,python_value,_,packed_encoding',
    CORRECT_SINGLE_ENCODINGS,
)
def test_encode_single(typ, python_value, _, packed_encoding):
    actual = encode_single_packed(typ, python_value)
    assert actual == packed_encoding
