import pytest

from eth_abi.base import (
    BaseCoder,
    parse_tuple_type_str,
    parse_type_str,
)
from eth_abi.grammar import (
    BasicType,
)


class Coder(BaseCoder):
    base = None
    sub = None

    def validate(self):
        if self.base is None:
            raise ValueError('Setting missing')

    @parse_type_str(with_arrlist=False)
    def from_type_str(cls, abi_type, registry):
        return cls(base=abi_type.base, sub=abi_type.sub)


class ArrayCoder(Coder):
    arrlist = None

    @parse_type_str(with_arrlist=True)
    def from_type_str(cls, abi_type, registry):
        return cls(base=abi_type.base, sub=abi_type.sub, arrlist=abi_type.arrlist)


class IntCoder(Coder):
    @parse_type_str('int', with_arrlist=False)
    def from_type_str(cls, abi_type, registry):
        return cls(base=abi_type.base, sub=abi_type.sub)


class IntArrayCoder(ArrayCoder):
    @parse_type_str('int', with_arrlist=True)
    def from_type_str(cls, abi_type, registry):
        return cls(base=abi_type.base, sub=abi_type.sub, arrlist=abi_type.arrlist)


class TupleCoder(BaseCoder):
    components = None

    @parse_tuple_type_str
    def from_type_str(cls, abi_type, registry):
        return cls(components=abi_type.components)


def test_base_coder_requires_that_settings_are_known():
    pattern = 'only accepts keyword arguments which are present'
    with pytest.raises(AttributeError, match=pattern):
        Coder(foo='bar')


def test_base_coder_validates_settings():
    with pytest.raises(ValueError, match='Setting missing'):
        Coder(sub='foo')


def test_base_coder_assigns_all_kwargs_to_instance():
    coder = Coder(base='foo', sub='bar')

    assert coder.base == 'foo'
    assert coder.sub == 'bar'


def test_parse_type_str_normalizes_and_parses_types():
    coder1 = Coder.from_type_str('int', None)

    assert coder1.base == 'int'
    assert coder1.sub == 256


def test_parse_type_str_validates_standard_types():
    with pytest.raises(ValueError, match='integer size must be multiple of 8'):
        Coder.from_type_str('int255', None)


def test_parse_type_str_requires_certain_base_type_if_given():
    with pytest.raises(ValueError, match='expected type with base \'int\''):
        IntCoder.from_type_str('uint256', None)

    with pytest.raises(ValueError, match='expected type with base \'int\''):
        IntArrayCoder.from_type_str('uint256[]', None)


def test_parse_type_str_doesnt_require_base_type_if_not_given():
    coder1 = Coder.from_type_str('uint256', None)
    assert coder1.base == 'uint'
    assert coder1.sub == 256

    coder2 = ArrayCoder.from_type_str('uint256[]', None)
    assert coder2.base == 'uint'
    assert coder2.sub == 256
    assert coder2.arrlist == ((),)


def test_parse_type_str_distinguishes_non_array_and_array_types():
    with pytest.raises(ValueError, match='expected type with no array dimension list'):
        Coder.from_type_str('int256[]', None)
    with pytest.raises(ValueError, match='expected type with array dimension list'):
        ArrayCoder.from_type_str('int256', None)

    with pytest.raises(ValueError, match='expected type with no array dimension list'):
        IntCoder.from_type_str('int256[]', None)
    with pytest.raises(ValueError, match='expected type with array dimension list'):
        IntArrayCoder.from_type_str('int256', None)


def test_parse_tuple_type_str_normalizes_and_parses_types():
    tuple_coder = TupleCoder.from_type_str('(int,int)', None)

    assert tuple_coder.components == (
        BasicType('int', 256, None),
        BasicType('int', 256, None),
    )


def test_parse_tuple_type_str_validates_standard_types():
    with pytest.raises(ValueError, match='integer size must be multiple of 8'):
        TupleCoder.from_type_str('(int255,int)', None)


def test_parse_tuple_type_str_distinguishes_non_tuple_and_tuple_types():
    with pytest.raises(ValueError, match='Cannot create TupleCoder for non-tuple type'):
        TupleCoder.from_type_str('int256', None)
