import re

from hypothesis import (
    event,
    given,
    settings,
    strategies as st,
)

from eth_abi.registry import (
    BaseEquals,
    Equals,
    has_arrlist,
    is_base_tuple,
)
from tests.common.strategies import (
    malformed_type_strs,
    type_strs,
)


@given(st.text())
def test_equals_has_expected_behavior(s):
    pos_predicate = Equals(s)
    neg_predicate = Equals(s + 'a')

    # Matches correct strings
    assert pos_predicate(s)
    assert not neg_predicate(s)

    # Can be equal/unequal
    assert pos_predicate == Equals(s)
    assert pos_predicate != neg_predicate


def test_equals_can_be_dict_key():
    pred = Equals('foo')
    assert {pred: 'bar'}[pred] == 'bar'


def test_equals_has_expected_repr():
    assert repr(Equals('foo')) == "<Equals (== 'foo')>"


ARRAY_RE = re.compile(r'\[\d*\]')


@settings(max_examples=200)
@given(type_strs)
def test_base_equals_has_expected_behavior_for_parsable_types(type_str):
    is_int = BaseEquals('int')
    is_int_with_sub = BaseEquals('int', with_sub=True)
    is_int_with_no_sub = BaseEquals('int', with_sub=False)

    # Should not match tuple types
    if type_str.startswith('('):
        assert not is_int(type_str)
        assert not is_int_with_sub(type_str)
        assert not is_int_with_no_sub(type_str)
        event('No match for tuple type')

    # Should not match array types
    elif ARRAY_RE.search(type_str):
        assert not is_int(type_str)
        assert not is_int_with_sub(type_str)
        assert not is_int_with_no_sub(type_str)
        event('No match for array type')

    # Should match types with int base
    elif type_str.startswith('int'):
        assert is_int(type_str)
        event('Match for base')

        if type_str == 'int':
            assert is_int_with_no_sub(type_str)
            assert not is_int_with_sub(type_str)
            event('Match for base with no sub')
        else:
            assert not is_int_with_no_sub(type_str)
            assert is_int_with_sub(type_str)
            event('Match for base with sub')

    # Should not match any other types
    else:
        assert not is_int(type_str)
        assert not is_int_with_sub(type_str)
        assert not is_int_with_no_sub(type_str)
        event('No match for other base')


def test_base_equals_can_be_dict_key():
    pred = BaseEquals('foo')
    assert {pred: 'bar'}[pred] == 'bar'


def test_base_equals_has_expected_repr():
    assert repr(BaseEquals('foo')) == "<BaseEquals (base == 'foo')>"
    assert (
        repr(BaseEquals('foo', with_sub=True)) ==
        "<BaseEquals (base == 'foo' and sub is not None)>"
    )
    assert (
        repr(BaseEquals('foo', with_sub=False)) ==
        "<BaseEquals (base == 'foo' and sub is None)>"
    )


@given(type_strs)
def test_has_arrlist_has_expected_behavior_for_parsable_types(type_str):
    # Should not match tuple types
    if type_str.startswith('('):
        assert not has_arrlist(type_str)
        event('No match for tuple type')

    # Should match array types
    elif ARRAY_RE.search(type_str):
        assert has_arrlist(type_str)
        event('Match for array type')

    # Should not match any other types
    else:
        assert not has_arrlist(type_str)
        event('No match for non-array type')


@given(type_strs)
def test_is_base_tuple_has_expected_behavior_for_parsable_types(type_str):
    # Should match tuple types
    if type_str.endswith(')'):
        assert is_base_tuple(type_str)
        event('Match for tuple type')

    # Should not match any other types
    else:
        assert not is_base_tuple(type_str)
        event('No match for non-tuple type')


@given(malformed_type_strs)
def test_predicates_have_expected_behavior_for_malformed_types(malformed_type_str):
    is_int = BaseEquals('int')
    is_int_with_sub = BaseEquals('int', with_sub=True)
    is_int_with_no_sub = BaseEquals('int', with_sub=False)

    # Should not match unparsable types
    assert not is_int(malformed_type_str)
    assert not is_int_with_sub(malformed_type_str)
    assert not is_int_with_no_sub(malformed_type_str)

    assert not has_arrlist(malformed_type_str)
    assert not is_base_tuple(malformed_type_str)
