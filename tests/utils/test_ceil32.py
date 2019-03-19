import pytest

from eth_abi.utils.numeric import (
    ceil32,
)


@pytest.mark.parametrize(
    'value,expected',
    (
        (0, 0),
        (1, 32),
        (31, 32),
        (32, 32),
        (33, 64),
        (63, 64),
        (64, 64),
        (100, 128),
    )
)
def test_ceil32(value, expected):
    actual = ceil32(value)
    assert actual == expected
