import sys

from eth_utils import (
    big_endian_to_int,
    decode_hex,
    int_to_big_endian,
    to_normalized_address,
)
from eth_utils.toolz import (
    complement,
)
from hypothesis import (
    example,
    given,
    settings,
    strategies as st,
)
import pytest

from eth_abi.constants import (
    TT256M1,
)
from eth_abi.decoding import (
    AddressDecoder,
    BooleanDecoder,
    BytesDecoder,
    ByteStringDecoder,
    ContextFramesBytesIO,
    DynamicArrayDecoder,
    SignedFixedDecoder,
    SignedIntegerDecoder,
    StringDecoder,
    TupleDecoder,
    UnsignedFixedDecoder,
    UnsignedIntegerDecoder,
)
from eth_abi.exceptions import (
    DecodingError,
    InsufficientDataBytes,
    NonEmptyPaddingBytes,
)
from eth_abi.registry import (
    registry,
)
from eth_abi.utils.numeric import (
    ceil32,
)
from eth_abi.utils.padding import (
    zpad32,
)


def is_utf8_decodable(value):
    try:
        value.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def is_utf8_encodable(value):
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def is_non_empty_non_null_byte_string(value):
    return value and big_endian_to_int(value) != 0


def is_valid_padding_bytes(padding_bytes, data_bytes):
    # Empty padding is always valid
    if len(padding_bytes) == 0:
        return True

    leading_data_bit_is_one = (data_bytes[0] & 0b10000000) == 0b10000000

    if leading_data_bit_is_one:
        # All padding bits must be 1
        if padding_bytes.replace(b'\xff', b'') == b'':
            return True
    else:
        # All padding bits must be 0
        if padding_bytes.replace(b'\x00', b'') == b'':
            return True

    return False


def all_bytes_equal(test_bytes, target):
    if sys.version_info.major < 3:
        return all(byte == chr(target) for byte in test_bytes)
    else:
        return all(byte == target for byte in test_bytes)


@settings(max_examples=250)
@given(
    integer_bit_size=st.integers(min_value=1, max_value=32).map(lambda v: v * 8),
    stream_bytes=st.binary(min_size=0, max_size=32),
    data_byte_size=st.integers(min_value=0, max_value=32),
)
def test_decode_unsigned_int(integer_bit_size, stream_bytes, data_byte_size):
    if integer_bit_size % 8 != 0:
        with pytest.raises(ValueError):
            UnsignedIntegerDecoder(
                value_bit_size=integer_bit_size,
                data_byte_size=data_byte_size,
            )
        return
    elif integer_bit_size > data_byte_size * 8:
        with pytest.raises(ValueError):
            UnsignedIntegerDecoder(
                value_bit_size=integer_bit_size,
                data_byte_size=data_byte_size,
            )
        return
    else:
        decoder = UnsignedIntegerDecoder(
            value_bit_size=integer_bit_size,
            data_byte_size=data_byte_size,
        )

    stream = ContextFramesBytesIO(stream_bytes)
    actual_value = big_endian_to_int(stream_bytes[:data_byte_size])

    if len(stream_bytes) < data_byte_size:
        with pytest.raises(InsufficientDataBytes):
            decoder(stream)
        return
    elif actual_value > 2 ** integer_bit_size - 1:
        with pytest.raises(NonEmptyPaddingBytes):
            decoder(stream)
        return
    else:
        decoded_value = decoder(stream)

    assert decoded_value == actual_value


@settings(max_examples=250)
@given(
    integer_bit_size=st.integers(min_value=1, max_value=32).map(lambda v: v * 8),
    stream_bytes=st.binary(min_size=0, max_size=32),
    data_byte_size=st.integers(min_value=0, max_value=32),
)
@example(8, b'\x00\x80', 2)
@example(8, b'\xff\xff', 2)
def test_decode_signed_int(integer_bit_size, stream_bytes, data_byte_size):
    if integer_bit_size % 8 != 0:
        with pytest.raises(ValueError):
            SignedIntegerDecoder(
                value_bit_size=integer_bit_size,
                data_byte_size=data_byte_size,
            )
        return
    elif integer_bit_size > data_byte_size * 8:
        with pytest.raises(ValueError):
            SignedIntegerDecoder(
                value_bit_size=integer_bit_size,
                data_byte_size=data_byte_size,
            )
        return
    else:
        decoder = SignedIntegerDecoder(
            value_bit_size=integer_bit_size,
            data_byte_size=data_byte_size,
        )

    stream = ContextFramesBytesIO(stream_bytes)

    padding_bytes = data_byte_size - integer_bit_size // 8

    raw_value = big_endian_to_int(stream_bytes[padding_bytes:data_byte_size])
    if raw_value >= 2 ** (integer_bit_size - 1):
        actual_value = raw_value - 2 ** integer_bit_size
    else:
        actual_value = raw_value

    if len(stream_bytes) < data_byte_size:
        with pytest.raises(InsufficientDataBytes):
            decoder(stream)
        return
    elif (
        (actual_value >= 0 and not all_bytes_equal(stream_bytes[:padding_bytes], 0)) or
        (actual_value < 0 and not all_bytes_equal(stream_bytes[:padding_bytes], 255))
    ):
        with pytest.raises(NonEmptyPaddingBytes):
            decoder(stream)
        return
    else:
        decoded_value = decoder(stream)

    assert decoded_value == actual_value


@settings(max_examples=250)
@given(
    _bytes=st.binary(min_size=0, max_size=256),
    pad_size=st.integers(min_value=0, max_value=32),
)
def test_decode_bytes(_bytes, pad_size):
    size_bytes = zpad32(int_to_big_endian(len(_bytes)))
    padded_bytes = _bytes + b'\x00' * pad_size
    stream_bytes = size_bytes + padded_bytes
    stream = ContextFramesBytesIO(stream_bytes)

    decoder = ByteStringDecoder()

    if len(padded_bytes) < ceil32(len(_bytes)):
        with pytest.raises(InsufficientDataBytes):
            decoder(stream)
        return

    decoded_value = decoder(stream)
    assert decoded_value == _bytes


@settings(max_examples=250)
@given(
    _strings=st.text(min_size=0, max_size=256).filter(is_utf8_encodable),
    pad_size=st.integers(min_value=0, max_value=32),
)
def test_decode_strings(_strings, pad_size):
    size_bytes = zpad32(int_to_big_endian(len(_strings.encode("utf-8"))))
    padded_bytes = _strings.encode("utf-8") + b'\x00' * pad_size
    stream_bytes = size_bytes + padded_bytes
    stream = ContextFramesBytesIO(stream_bytes)

    decoder = StringDecoder()

    if len(padded_bytes) < ceil32(len(_strings.encode("utf-8"))):
        with pytest.raises(InsufficientDataBytes):
            decoder(stream)
        return

    decoded_value = decoder(stream)
    assert decoded_value == _strings


@settings(max_examples=250)
@given(
    _bytes=st.binary(min_size=0, max_size=256).filter(complement(is_utf8_decodable)),
    pad_size=st.integers(min_value=0, max_value=32),
)
def test_decode_strings_raises(_bytes, pad_size):
    size_bytes = zpad32(int_to_big_endian(len(_bytes)))
    padded_bytes = _bytes + b'\x00' * pad_size
    stream_bytes = size_bytes + padded_bytes
    stream = ContextFramesBytesIO(stream_bytes)

    decoder = StringDecoder()

    if len(padded_bytes) < ceil32(len(_bytes)):
        with pytest.raises(InsufficientDataBytes):
            decoder(stream)
        return

    with pytest.raises(DecodingError):
        decoder(stream)


@settings(max_examples=250)
@given(
    stream_bytes=st.binary(min_size=1, max_size=32),
    data_byte_size=st.integers(min_value=1, max_value=32),
)
def test_decode_boolean(stream_bytes, data_byte_size):
    stream = ContextFramesBytesIO(stream_bytes)

    decoder = BooleanDecoder(data_byte_size=data_byte_size)

    if len(stream_bytes) < data_byte_size:
        with pytest.raises(InsufficientDataBytes):
            decoder(stream)
        return

    padding_bytes = stream_bytes[:data_byte_size][:-1]
    if is_non_empty_non_null_byte_string(padding_bytes):
        with pytest.raises(NonEmptyPaddingBytes):
            decoder(stream)
        return

    byte_value = stream_bytes[data_byte_size - 1]

    if byte_value in {0, b'\x00'}:
        actual_value = False
    elif byte_value in {1, b'\x01'}:
        actual_value = True
    else:
        with pytest.raises(NonEmptyPaddingBytes):
            decoder(stream)
        return

    decoded_value = decoder(stream)
    assert decoded_value is actual_value


@settings(max_examples=250)
@given(
    value_byte_size=st.integers(min_value=1, max_value=32),
    stream_bytes=st.binary(min_size=0, max_size=32),
    data_byte_size=st.integers(min_value=0, max_value=32),
)
def test_decode_bytes_xx(value_byte_size, stream_bytes, data_byte_size):
    if value_byte_size > data_byte_size:
        with pytest.raises(ValueError):
            BytesDecoder(
                value_bit_size=value_byte_size * 8,
                data_byte_size=data_byte_size,
            )
        return
    else:
        decoder = BytesDecoder(
            value_bit_size=value_byte_size * 8,
            data_byte_size=data_byte_size,
        )

    stream = ContextFramesBytesIO(stream_bytes)
    actual_value = stream_bytes[:value_byte_size]
    padding_bytes = stream_bytes[value_byte_size:data_byte_size]

    if len(stream_bytes) < data_byte_size:
        with pytest.raises(InsufficientDataBytes):
            decoder(stream)
        return
    elif is_non_empty_non_null_byte_string(padding_bytes):
        with pytest.raises(NonEmptyPaddingBytes):
            decoder(stream)
        return
    else:
        decoded_value = decoder(stream)

    assert decoded_value == actual_value


@settings(max_examples=250)
@given(
    address_bytes=st.binary(min_size=0, max_size=32),
    padding_size=st.integers(min_value=10, max_value=14),
    data_byte_size=st.integers(min_value=0, max_value=32),
)
def test_decode_address(address_bytes, padding_size, data_byte_size):
    stream_bytes = b'\x00' * padding_size + address_bytes
    if data_byte_size < 20:
        with pytest.raises(ValueError):
            AddressDecoder(
                data_byte_size=data_byte_size,
            )
        return
    else:
        decoder = AddressDecoder(
            data_byte_size=data_byte_size,
        )

    stream = ContextFramesBytesIO(stream_bytes)
    padding_bytes = stream_bytes[:data_byte_size][:-20]

    if len(stream_bytes) < data_byte_size:
        with pytest.raises(InsufficientDataBytes):
            decoder(stream)
        return
    elif is_non_empty_non_null_byte_string(padding_bytes):
        with pytest.raises(NonEmptyPaddingBytes):
            decoder(stream)
        return
    else:
        decoded_value = decoder(stream)

    actual_value = to_normalized_address(stream_bytes[:data_byte_size][-20:])

    assert decoded_value == actual_value


@settings(max_examples=250)
@given(
    array_size=st.integers(min_value=0, max_value=32),
    array_values=st.lists(
        st.integers(min_value=0, max_value=TT256M1),
        min_size=0, max_size=64,
    ).map(tuple),
)
def test_decode_array_of_unsigned_integers(array_size, array_values):
    size_bytes = zpad32(int_to_big_endian(array_size))
    values_bytes = b''.join((
        zpad32(int_to_big_endian(v)) for v in array_values
    ))
    stream_bytes = size_bytes + values_bytes

    decoder = DynamicArrayDecoder(
        item_decoder=UnsignedIntegerDecoder(value_bit_size=256),
    )
    stream = ContextFramesBytesIO(stream_bytes)

    if len(array_values) < array_size:
        with pytest.raises(InsufficientDataBytes):
            decoder(stream)
        return

    actual_values = decoder(stream)
    assert actual_values == array_values[:array_size]


@pytest.mark.parametrize(
    'types,data,expected',
    (
        (
            ('address', 'uint256'),
            (
                '0x'
                '000000000000000000000000abf7d8b5c1322b3e553d2fac90ff006c30f1b875'
                '0000000000000000000000000000000000000000000000000000005d21dba000'
            ),
            ('0xabf7d8b5c1322b3e553d2fac90ff006c30f1b875', 400000000000)
        ),
        (
            ('uint256', 'bytes'),
            (
                '0x'
                '0000000000000000000000000000000000000000000000000000000000000000'
                '0000000000000000000000000000000000000000000000000000000000000040'
                '0000000000000000000000000000000000000000000000000000000000000000'
                '0000000000000000000000000000000000000000000000000000000000000000'
            ),
            (0, b''),
        ),
    ),
)
def test_tuple_decoder(types, data, expected):
    decoders = [registry.get_decoder(t) for t in types]
    decoder = TupleDecoder(decoders=decoders)
    stream = ContextFramesBytesIO(decode_hex(data))
    actual = decoder(stream)
    assert actual == expected


@settings(max_examples=250)
@given(
    value_bit_size=st.integers(min_value=1, max_value=32).map(lambda v: v * 8),
    frac_places=st.integers(min_value=1, max_value=80),
    stream_bytes=st.binary(min_size=0, max_size=32),
    data_byte_size=st.integers(min_value=0, max_value=32),
)
def test_decode_unsigned_fixed(value_bit_size,
                               frac_places,
                               stream_bytes,
                               data_byte_size):
    if value_bit_size > data_byte_size * 8:
        with pytest.raises(ValueError):
            UnsignedFixedDecoder(
                value_bit_size=value_bit_size,
                frac_places=frac_places,
                data_byte_size=data_byte_size,
            )
        return

    decoder = UnsignedFixedDecoder(
        value_bit_size=value_bit_size,
        frac_places=frac_places,
        data_byte_size=data_byte_size,
    )

    stream = ContextFramesBytesIO(stream_bytes)
    padding_bytes = stream_bytes[:data_byte_size][:data_byte_size - value_bit_size // 8]

    if len(stream_bytes) < data_byte_size:
        with pytest.raises(InsufficientDataBytes):
            decoder(stream)
        return

    if is_non_empty_non_null_byte_string(padding_bytes):
        with pytest.raises(NonEmptyPaddingBytes):
            decoder(stream)
        return

    # Ensure no exceptions
    decoder(stream)


@settings(max_examples=250)
@given(
    value_bit_size=st.integers(min_value=1, max_value=32).map(lambda v: v * 8),
    frac_places=st.integers(min_value=1, max_value=80),
    stream_bytes=st.binary(min_size=0, max_size=32),
    data_byte_size=st.integers(min_value=0, max_value=32),
)
def test_decode_signed_fixed(value_bit_size,
                             frac_places,
                             stream_bytes,
                             data_byte_size):
    if value_bit_size > data_byte_size * 8:
        with pytest.raises(ValueError):
            SignedFixedDecoder(
                value_bit_size=value_bit_size,
                frac_places=frac_places,
                data_byte_size=data_byte_size,
            )
        return

    decoder = SignedFixedDecoder(
        value_bit_size=value_bit_size,
        frac_places=frac_places,
        data_byte_size=data_byte_size,
    )

    stream = ContextFramesBytesIO(stream_bytes)

    padding_offset = data_byte_size - value_bit_size // 8
    data_offset = padding_offset + value_bit_size // 8

    padding_bytes = stream_bytes[:data_byte_size][:padding_offset]
    data_bytes = stream_bytes[:data_byte_size][padding_offset:data_offset]

    if len(stream_bytes) < data_byte_size:
        with pytest.raises(InsufficientDataBytes):
            decoder(stream)
        return

    if not is_valid_padding_bytes(padding_bytes, data_bytes):
        with pytest.raises(NonEmptyPaddingBytes):
            decoder(stream)
        return

    actual_value = decoder(stream)

    if padding_bytes:
        if actual_value >= 0:
            assert bytes(set(padding_bytes)) == b'\x00'
        else:
            assert bytes(set(padding_bytes)) == b'\xff'
