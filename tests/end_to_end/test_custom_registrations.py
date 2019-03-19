from eth_abi.abi import (
    decode_single,
    encode_single,
)
from eth_abi.decoding import (
    BaseDecoder,
)
from eth_abi.encoding import (
    BaseEncoder,
)
from eth_abi.exceptions import (
    DecodingError,
    EncodingError,
)
from eth_abi.registry import (
    registry,
)

NULL_ENCODING = b'\x00' * 32


def encode_null(x):
    if x is not None:
        raise EncodingError('Unsupported value')

    return NULL_ENCODING


def decode_null(stream):
    if stream.read(32) != NULL_ENCODING:
        raise DecodingError('Not enough data or wrong data')

    return None


class EncodeNull(BaseEncoder):
    word_width = None

    @classmethod
    def from_type_str(cls, type_str, registry):
        word_width = int(type_str[4:])
        return cls(word_width=word_width)

    def encode(self, value):
        self.validate_value(value)
        return NULL_ENCODING * self.word_width

    def validate_value(self, value):
        if value is not None:
            raise EncodingError('Unsupported value')


class DecodeNull(BaseDecoder):
    word_width = None

    @classmethod
    def from_type_str(cls, type_str, registry):
        word_width = int(type_str[4:])
        return cls(word_width=word_width)

    def decode(self, stream):
        byts = stream.read(32 * self.word_width)
        if byts != NULL_ENCODING * self.word_width:
            raise DecodingError('Not enough data or wrong data')

        return None


def test_register_and_use_callables():
    registry.register('null', encode_null, decode_null)

    try:
        assert encode_single('null', None) == NULL_ENCODING
        assert decode_single('null', NULL_ENCODING) is None

        encoded_tuple = encode_single('(int,null)', (1, None))

        assert encoded_tuple == b'\x00' * 31 + b'\x01' + NULL_ENCODING
        assert decode_single('(int,null)', encoded_tuple) == (1, None)
    finally:
        registry.unregister('null')


def test_register_and_use_coder_classes():
    registry.register(
        lambda x: x.startswith('null'),
        EncodeNull,
        DecodeNull,
        label='null',
    )

    try:
        assert encode_single('null2', None) == NULL_ENCODING * 2
        assert decode_single('null2', NULL_ENCODING * 2) is None

        encoded_tuple = encode_single('(int,null2)', (1, None))

        assert encoded_tuple == b'\x00' * 31 + b'\x01' + NULL_ENCODING * 2
        assert decode_single('(int,null2)', encoded_tuple) == (1, None)
    finally:
        registry.unregister('null')
