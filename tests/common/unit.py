from decimal import (
    Decimal,
)
import re

from eth_utils import (
    decode_hex,
)

from eth_abi.utils.padding import (
    zpad32_right,
)

WORD_DESC_RE = re.compile(r'^(([0f])<)?([0-9a-f]+)(>([0f]))?( \(([0-9]+) wide\))?$')


def make_word(description: str) -> bytes:
    r"""
    Converts a "description" of an N-byte word into an N-byte word.  A
    description is either a hex representation of a byte string (e.g.
    'deafbeef') or a hex representation along with a fill directive (i.e.
    'leftpadchar<' or '>rightpadchar') and an optional byte width directive
    (e.g. '(4 wide)').  Generated words are 32 bytes wide by default.

    Examples
    --------
    >>> # Left padding examples
    >>> assert make_word('0<deadbeef') == zpad32(b'\xde\xad\xbe\xef')
    >>> assert make_word('f<deadbeef') == fpad32(b'\xde\xad\xbe\xef')
    >>> assert make_word('deadbeef') == zpad32(b'\xde\xad\xbe\xef')
    >>> assert make_word('deadbeef (8 wide)') == b'\x00\x00\x00\x00\xde\xad\xbe\xef'
    >>> # Right padding examples
    >>> assert make_word('deadbeef>0') == zpad32_right(b'\xde\xad\xbe\xef')
    >>> assert make_word('deadbeef>0 (8 wide)') == b'\xde\xad\xbe\xef\x00\x00\x00\x00'

    """
    match = WORD_DESC_RE.search(description)
    if match is None:
        raise ValueError('Word description invalid')

    _, left_fill, hex_str, _, right_fill, _, width = match.groups()

    if width is not None:
        width = int(width) * 2
    else:
        width = 64

    if left_fill is not None:
        return decode_hex(hex_str.rjust(width, left_fill))

    if right_fill is not None:
        return decode_hex(hex_str.ljust(width, right_fill))

    return decode_hex(hex_str.rjust(width, '0'))


def words(*descriptions: str) -> bytes:
    r"""
    Converts multiple word descriptions into 32-byte words joined into a single
    byte string.

    Examples
    --------
    >>> assert words('1') == zpad32(b'\x01')
    >>> assert words('1', '2f>0') == zpad32(b'\x01') + zpad32_right(b'\x2f')

    """
    return b''.join(make_word(d) for d in descriptions)


CORRECT_TUPLE_ENCODINGS = [
    # (type string, python value, abi encoding, packed encoding)

    # Empty tuples
    (
        '()', (), b'', b'',
    ),
    (
        '((),((),((),())))',
        ((), ((), ((), ()))),
        b'',
        b'',
    ),

    # Static tuples
    (
        '(uint32)',
        (6,),
        words('6'),
        words('6 (4 wide)'),
    ),
    (
        '(uint32,uint32)',
        (2 ** 32 - 1, 2 ** 32 - 1),
        words('ffffffff', 'ffffffff'),
        words('f<f (4 wide)', 'f<f (4 wide)')
    ),
    (
        '(bytes32,bytes32)',
        (zpad32_right(b'a'), zpad32_right(b'b')),
        words('61>0', '62>0'),
        words('61>0', '62>0'),
    ),
    (
        '(address,uint32,bytes32,int32)',
        (
            '0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1',
            1,
            zpad32_right(b'stupid pink animal'),
            0,
        ),
        words(
            '82a978b3f5962a5b0957d9ee9eef472ee55b42f1',
            '1',
            '7374757069642070696e6b20616e696d616c>0',
            '0',
        ),
        words(
            '82a978b3f5962a5b0957d9ee9eef472ee55b42f1 (20 wide)',
            '1 (4 wide)',
            '7374757069642070696e6b20616e696d616c>0',
            '0 (4 wide)',
        ),
    ),

    # Dynamic tuples
    (
        '(bytes32[])',
        ((zpad32_right(b'a'), zpad32_right(b'b')),),
        words('20', '2', '61>0', '62>0'),
        words('61>0', '62>0'),
    ),
    (
        '(uint256,bytes)',
        (0, b''),
        words('0', '40', '0', '0'),
        words('0'),
    ),
    (
        '(int,(int,int[]))',
        (1, (2, (3, 3))),
        words('1', '40', '2', '40', '2', '3', '3'),
        words('1', '2', '3', '3'),
    ),
    (
        '((int[],int),int)',
        (((1, 1), 2), 3),
        words('40', '3', '40', '2', '2', '1', '1'),
        words('1', '1', '2', '3'),
    ),
    (
        '((bytes,bool),(bytes,bool))',
        ((b'david attenborough', False), (b'boaty mcboatface', True)),
        words(
            '40',  # offset of first (bytes,bool)
            'c0',  # offset of second (bytes,bool)
            '40',  # offset of bytes in first (bytes,bool)
            '0',  # encoding for `False`
            '12',  # length of b'david attenborough'
            '646176696420617474656e626f726f756768>0',  # encoding of b'david attenborough'
            '40',  # offset of bytes in second (bytes,bool)
            '1',  # encoding for `True`
            '10',  # length of b'boaty mcboatface'
            '626f617479206d63626f617466616365>0',  # encoding of b'boaty mcboatface'
        ),
        decode_hex(
            '646176696420617474656e626f726f756768'  # encoding of b'david attenborough'
            '00'  # encoding for `False`
            '626f617479206d63626f617466616365'  # encoding of b'boaty mcboatface'
            '01'  # encoding for `True`
        ),
    ),

    # Tuple arrays
    (
        '((int,int)[])',
        (((1, 2), (3, 4)),),
        words('20', '2', '1', '2', '3', '4'),
        words('1', '2', '3', '4'),
    ),
    (
        '((int,int[],(int,int)[]),(int,int),int)',
        (
            (
                1,
                (2, 3),
                ((4, 5), (6, 7)),
            ),
            (8, 9),
            10,
        ),
        words(
            '80',  # offset of dynamic tuple
            '8',  # outer tuple static tuple
            '9',
            'a',  # outer tuple int
            '1',  # beginning of dynamic tuple (int)
            '60',  # offset of dynamic tuple list of ints
            'c0',  # offset of dynamic tuple list of tuples
            '2',  # size of list of ints
            '2',
            '3',
            '2',  # size of list of tuples
            '4',  # beginning of first tuple
            '5',
            '6',  # beginning of second tuple
            '7',
        ),
        words('1', '2', '3', '4', '5', '6', '7', '8', '9', 'a'),
    ),
    (
        '(int,int)[][]',
        (
            ((1, 2),),
            ((3, 4), (5, 6)),
            ((7, 8), (9, 10), (11, 12)),
        ),
        words(
            '3',  # size of outer dynamic list
            '60',  # offset of first dynamic list
            'c0',  # offset of second dynamic list
            '160',  # offset of third dynamic list
            '1',  # size of first list
            '1',  # start of first tuple
            '2',
            '2',  # size of second list
            '3',  # start of second tuple
            '4',
            '5',  # start of third tuple
            '6',
            '3',  # size of third list
            '7',  # start of fourth tuple
            '8',
            '9',  # start of fifth tuple
            'a',
            'b',  # start of sixth tuple
            'c',
        ),
        words('1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c'),
    ),
    (
        '((int,int)[][2])',
        (
            (
                ((1, 2), (3, 4)),
                ((5, 6), (7, 8), (9, 10)),
            ),
        ),
        words(
            '20',  # offset of constant size array
            '40',  # offset of first dynamic list of tuples
            'e0',  # offset of second dynamic list of tuples
            '2',  # size of first list
            '1',  # start of first tuple
            '2',
            '3',  # start of second tuple
            '4',
            '3',  # size of second list
            '5',  # start of third tuple
            '6',
            '7',  # start of fourth tuple
            '8',
            '9',  # start of fifth tuple
            'a',
        ),
        words('1', '2', '3', '4', '5', '6', '7', '8', '9', 'a'),
    ),
]

CORRECT_SINGLE_ENCODINGS = CORRECT_TUPLE_ENCODINGS + [
    #####
    # (type string, python value, abi encoding, packed encoding)
    #####

    # uint<M>
    ('uint8', 255, words('ff'), b'\xff'),
    ('uint8', 21, words('15'), b'\x15'),
    ('uint8', 1, words('1'), b'\x01'),
    ('uint256', 2 ** 256 - 1, words('f<f'), words('f<f')),
    ('uint256', 2 ** 256 - 100, words('f<9c'), words('f<9c')),
    ('uint256', 21, words('15'), words('15')),
    ('uint256', 1, words('1'), words('1')),

    # int<M>
    ('int8', 21, words('15'), b'\x15'),
    ('int8', 1, words('1'), b'\x01'),
    ('int8', -1, words('f<f'), b'\xff'),
    ('int8', -100, words('f<9c'), b'\x9c'),
    ('int256', 21, words('15'), words('15')),
    ('int256', 1, words('1'), words('1')),
    ('int256', -1, words('f<f'), words('f<f')),
    ('int256', -100, words('f<9c'), words('f<9c')),

    # address
    (
        'address',
        '0x0000000000000000000000000000000000000000',
        words('0'),
        words('0 (20 wide)'),
    ),
    (
        'address',
        '0xd3cda913deb6f67967b99d67acdfa1712c293601',
        words('d3cda913deb6f67967b99d67acdfa1712c293601'),
        decode_hex('d3cda913deb6f67967b99d67acdfa1712c293601'),
    ),
    (
        'address',
        '0x0005c901078781c232a2a521c2af7980f8385ee9',
        words('0005c901078781c232a2a521c2af7980f8385ee9'),
        decode_hex('0005c901078781c232a2a521c2af7980f8385ee9'),
    ),
    (
        'address',
        '0x5c901078781c232a2a521c2af7980f8385ee9000',
        words('5c901078781c232a2a521c2af7980f8385ee9000'),
        decode_hex('5c901078781c232a2a521c2af7980f8385ee9000'),
    ),

    # uint, int
    ('uint', 2 ** 256 - 1, words('f<f'), words('f<f')),
    ('uint', 2 ** 256 - 100, words('f<9c'), words('f<9c')),
    ('uint', 21, words('15'), words('15')),
    ('uint', 1, words('1'), words('1')),
    ('int', 21, words('15'), words('15')),
    ('int', 1, words('1'), words('1')),
    ('int', -1, words('f<f'), words('f<f')),
    ('int', -100, words('f<9c'), words('f<9c')),

    # bool
    ('bool', True, words('1'), b'\x01'),
    ('bool', False, words('0'), b'\x00'),

    # fixed<M>x<N>
    ('fixed8x1', Decimal('127e-1'), words('7f'), b'\x7f'),
    ('fixed8x1', Decimal('1e-1'), words('1'), b'\x01'),
    ('fixed8x1', Decimal('0'), words('0'), b'\x00'),
    ('fixed8x1', Decimal('-1e-1'), words('f<f'), b'\xff'),
    ('fixed8x1', Decimal('-128e-1'), words('f<80'), b'\x80'),

    ('fixed128x18', Decimal('127e-18'), words('7f'), words('7f (16 wide)')),
    ('fixed128x18', Decimal('1e-18'), words('1'), words('1 (16 wide)')),
    ('fixed128x18', Decimal('0'), words('0'), words('0 (16 wide)')),
    ('fixed128x18', Decimal('-1e-18'), words('f<f'), words('f<f (16 wide)')),
    ('fixed128x18', Decimal('-128e-18'), words('f<80'), words('f<80 (16 wide)')),

    ('fixed256x80', Decimal('127e-80'), words('7f'), words('7f')),
    ('fixed256x80', Decimal('1e-80'), words('1'), words('1')),
    ('fixed256x80', Decimal('0'), words('0'), words('0')),
    ('fixed256x80', Decimal('-1e-80'), words('f<f'), words('f<f')),
    ('fixed256x80', Decimal('-128e-80'), words('f<80'), words('f<80')),

    # ufixed<M>x<N>
    ('ufixed8x1', Decimal('255e-1'), words('ff'), b'\xff'),
    ('ufixed8x1', Decimal('254e-1'), words('fe'), b'\xfe'),
    ('ufixed8x1', Decimal('1e-1'), words('1'), b'\x01'),
    ('ufixed8x1', Decimal('0'), words('0'), b'\x00'),

    ('ufixed128x18', Decimal('255e-18'), words('ff'), words('ff (16 wide)')),
    ('ufixed128x18', Decimal('254e-18'), words('fe'), words('fe (16 wide)')),
    ('ufixed128x18', Decimal('1e-18'), words('1'), words('1 (16 wide)')),
    ('ufixed128x18', Decimal('0'), words('0'), words('0 (16 wide)')),

    ('ufixed256x80', Decimal('255e-80'), words('ff'), words('ff')),
    ('ufixed256x80', Decimal('254e-80'), words('fe'), words('fe')),
    ('ufixed256x80', Decimal('1e-80'), words('1'), words('1')),
    ('ufixed256x80', Decimal('0'), words('0'), words('0')),

    # fixed, ufixed
    ('fixed', Decimal('127e-18'), words('7f'), words('7f (16 wide)')),
    ('fixed', Decimal('1e-18'), words('1'), words('1 (16 wide)')),
    ('fixed', Decimal('0'), words('0'), words('0 (16 wide)')),
    ('fixed', Decimal('-1e-18'), words('f<f'), words('f<f (16 wide)')),
    ('fixed', Decimal('-128e-18'), words('f<80'), words('f<80 (16 wide)')),
    ('ufixed', Decimal('255e-18'), words('ff'), words('ff (16 wide)')),
    ('ufixed', Decimal('254e-18'), words('fe'), words('fe (16 wide)')),
    ('ufixed', Decimal('1e-18'), words('1'), words('1 (16 wide)')),
    ('ufixed', Decimal('0'), words('0'), words('0 (16 wide)')),

    # bytes<M>
    ('bytes32', zpad32_right(b'test'), words('74657374>0'), zpad32_right(b'test')),
    (
        'bytes32',
        zpad32_right(b'abcdefghijklmnopqrstuvwxyz'),
        words('6162636465666768696a6b6c6d6e6f707172737475767778797a>0'),
        words('6162636465666768696a6b6c6d6e6f707172737475767778797a>0'),
    ),
    (
        'bytes32',
        zpad32_right(b'0123456789!@#$%^&*()'),
        words('3031323334353637383921402324255e262a2829>0'),
        words('3031323334353637383921402324255e262a2829>0'),
    ),
    (
        'bytes32',
        zpad32_right(b'abc' + 5 * b'\x00' + b'abc'),
        words('6162630000000000616263>0'),
        words('6162630000000000616263>0'),
    ),
    ('bytes1', b'a', words('61>0'), b'a'),

    # bytes
    ('bytes', b'', words('0', '0'), b''),
    ('bytes', b'\xde', words('1', 'de>0'), b'\xde'),
]

NOT_ENCODABLE = [
    # Wrong value type
    ('((bytes,bool),(bytes,bool))', ((b'david attenborough', 0), (b'boaty mcboatface', True))),
    ('(uint32)', ('6',)),
    ('int[]', 6),
    ('bool[2]', (True, 2)),
    ('bool', 1),
    ('uint', True),
    ('int', True),
    ('bytes', 129),
    ('fixed8x1', 0.1),  # only Decimal and int are allowed

    # List size mismatch
    ('int[3]', (6, 2)),

    # Bytes string is wrong size
    ('bytes5', b'asdfgt'),

    # Addresses aren't 20 bytes long
    ('address', '0x8deebe59332ebc3f81935e311f0fb8556cf573'),
    ('address', decode_hex('0x8deebe59332ebc3f81935e311f0fb8556cf573')),

    # Values out of bounds
    ('uint8', 256),
    ('uint8', -1),
    ('int8', 128),
    ('int8', -129),
    ('string', -129),
    ('fixed8x1', Decimal('128e-1')),
    ('fixed8x1', Decimal('-129e-1')),
    ('ufixed8x1', Decimal('256e-1')),
    ('ufixed8x1', Decimal('-1e-1')),
    ('fixed8x1', Decimal('1e-2')),
]
