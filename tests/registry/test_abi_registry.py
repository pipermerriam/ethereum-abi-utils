import copy
import itertools

import pytest

from eth_abi import (
    decoding,
    encoding,
    exceptions,
)
from eth_abi.registry import (
    ABIRegistry,
    BaseEquals,
    has_arrlist,
    registry as default_registry,
)


@pytest.fixture
def registry():
    reg = ABIRegistry()

    reg.register(
        has_arrlist,
        encoding.BaseArrayEncoder, decoding.BaseArrayDecoder,
        label='has_arrlist',
    )
    reg.register(
        BaseEquals('address'),
        encoding.AddressEncoder, decoding.AddressDecoder,
        label='address',
    )

    return reg


@pytest.mark.parametrize(
    'type_str, encoder_class, decoder_class',
    (
        ('address', encoding.AddressEncoder, decoding.AddressDecoder),
        ('bool', encoding.BooleanEncoder, decoding.BooleanDecoder),
        ('bytes12', encoding.BytesEncoder, decoding.BytesDecoder),
        ('function', encoding.BytesEncoder, decoding.BytesDecoder),
        ('bytes', encoding.ByteStringEncoder, decoding.ByteStringDecoder),
        ('int', encoding.SignedIntegerEncoder, decoding.SignedIntegerDecoder),
        ('int128', encoding.SignedIntegerEncoder, decoding.SignedIntegerDecoder),
        ('string', encoding.TextStringEncoder, decoding.StringDecoder),
        ('uint', encoding.UnsignedIntegerEncoder, decoding.UnsignedIntegerDecoder),
        ('uint8', encoding.UnsignedIntegerEncoder, decoding.UnsignedIntegerDecoder),
        ('int[]', encoding.DynamicArrayEncoder, decoding.DynamicArrayDecoder),
        ('int[2]', encoding.SizedArrayEncoder, decoding.SizedArrayDecoder),
        ('int[2][]', encoding.DynamicArrayEncoder, decoding.DynamicArrayDecoder),
        ('int[][2]', encoding.SizedArrayEncoder, decoding.SizedArrayDecoder),
    ),
)
def test_default_registry_gives_correct_basic_coders(type_str, encoder_class, decoder_class):
    assert isinstance(default_registry.get_encoder(type_str), encoder_class)
    assert isinstance(default_registry.get_decoder(type_str), decoder_class)


def test_cache_resets_after_register_and_register_works(registry: ABIRegistry):
    # Populate cache
    registry.get_encoder('address')
    registry.get_decoder('address')

    # Perform cache resetting action
    registry.register(
        BaseEquals('address', with_sub=False),
        encoding.AddressEncoder, decoding.AddressDecoder,
        label='address without sub',
    )

    # Confirm cache reset
    pattern = r'Multiple matching entries .* encoder registry'
    with pytest.raises(ValueError, match=pattern):
        registry.get_encoder('address')

    pattern = r'Multiple matching entries .* decoder registry'
    with pytest.raises(ValueError, match=pattern):
        registry.get_decoder('address')


def test_cache_resets_after_unregister_and_unregister_works(registry: ABIRegistry):
    # Populate cache
    registry.get_encoder('address')
    registry.get_decoder('address')

    # Perform cache resetting action
    registry.unregister('address')

    # Confirm cache reset
    with pytest.raises(ValueError, match=r'No matching entries .* encoder registry'):
        registry.get_encoder('address')
    with pytest.raises(ValueError, match=r'No matching entries .* decoder registry'):
        registry.get_decoder('address')


def test_can_register_and_unregister_string_lookups(registry: ABIRegistry):
    registry.register(
        'bool',
        encoding.BooleanEncoder,
        decoding.BooleanDecoder,
    )

    assert isinstance(registry.get_encoder('bool'), encoding.BooleanEncoder)
    assert isinstance(registry.get_decoder('bool'), decoding.BooleanDecoder)

    registry.unregister('bool')

    with pytest.raises(ValueError, match=r'No matching entries .* encoder registry'):
        registry.get_encoder('bool')
    with pytest.raises(ValueError, match=r'No matching entries .* decoder registry'):
        registry.get_decoder('bool')


def test_registry_should_reject_unknown_types(registry: ABIRegistry):
    with pytest.raises(TypeError):
        registry.register(True, None, None)
    with pytest.raises(TypeError):
        registry.unregister(True)


def test_can_unregister_by_equality(registry: ABIRegistry):
    registry.unregister(BaseEquals('address'))

    with pytest.raises(ValueError, match=r'No matching entries .* encoder registry'):
        registry.get_encoder('address')
    with pytest.raises(ValueError, match=r'No matching entries .* decoder registry'):
        registry.get_decoder('address')


def test_can_register_simple_callables(registry: ABIRegistry):
    def encode_bool(x):
        return x
    decode_bool = encode_bool

    registry.register('bool', encode_bool, decode_bool)

    assert registry.get_encoder('bool') is encode_bool
    assert registry.get_decoder('bool') is decode_bool


def test_unregister_unknown_lookups(registry: ABIRegistry):
    with pytest.raises(KeyError, match=r'Matcher .* not found in encoder registry'):
        registry.unregister(lambda x: x)
    with pytest.raises(KeyError, match=r'Label .* not found in encoder registry'):
        registry.unregister('foo')


def test_looking_up_unparsable_type_causes_error(registry: ABIRegistry):
    with pytest.raises(exceptions.ParseError, match='Parse error at'):
        registry.get_encoder('uint[]256')


def test_copying_copies_internal_mappings(registry: ABIRegistry):
    c1 = registry.copy()
    c2 = copy.copy(registry)
    c3 = copy.deepcopy(registry)

    for x, y in itertools.combinations((registry, c1, c2, c3), 2):
        # Objects are different
        assert id(x) != id(y)

        # Internal mapping objects are different
        assert id(x._encoders) != id(y._encoders)
        assert id(x._decoders) != id(y._decoders)

        # Coders can be found for existing registrations
        assert isinstance(x.get_encoder('address'), encoding.AddressEncoder)
        assert isinstance(x.get_decoder('address'), decoding.AddressDecoder)
        assert isinstance(y.get_encoder('address'), encoding.AddressEncoder)
        assert isinstance(y.get_decoder('address'), decoding.AddressDecoder)
