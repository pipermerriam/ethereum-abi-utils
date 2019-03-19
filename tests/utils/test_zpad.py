import pytest

from eth_abi.utils.padding import (
    zpad,
)


@pytest.mark.parametrize(
    'value,length,expected',
    (
        (b'', 5, b"\x00\x00\x00\x00\x00"),
        (b'abc', 5, b"\x00\x00abc"),
        (b'abcde', 5, b"abcde"),
        (b'abcdef', 5, b"abcdef"),
    )
)
def test_zpadding(value, length, expected):
    actual = zpad(value, length)
    assert actual == expected
