# Ethereum Contract

[![Build Status](https://circleci.com/gh/ethereum/eth-abi.svg?style=shield)](https://circleci.com/gh/ethereum/eth-abi)
[![Documentation Status](https://readthedocs.org/projects/eth-abi/badge/?version=latest)](https://readthedocs.org/projects/eth-abi/?badge=latest)
[![PyPi version](https://img.shields.io/pypi/v/eth-abi.svg)](https://pypi.python.org/pypi/eth-abi)

Python utilities for working with the Ethereum ABI.

## Installation

```sh
pip install eth-abi
```

## Documentation

### Decoding

Decoding functions convert abi-encoded binary data generated by the EVM into
python values.

#### `eth_abi.decode_single(typ, data)`

Attempts to decode the abi-encoded bytes in `data` into an equivalent python
value for the abi type `typ`.

**Arguments:**
* `typ` - A `str` value representing an abi type e.g. `'uint256'`, `'bytes[]'`,
  `'(int,int)'`, etc.
* `data` - A `bytes` or `bytearray` value that contains abi-encoded data for a
  value of the abi type `typ`.

**Returns:** A python value that is equivalent to the abi-encoded value in
`data`.

**Example:**
```python
>>> decode_single('uint256', b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0009')
12345
```

#### `eth_abi.decode_abi(types, data)`

Attempts to decode the abi-encoded binary data in `data` into a sequence of
equivalent python values for the abi types given in `types`.

**Arguments:**
* `types` - An iterable of `str` values representing a sequence of abi types
  e.g.  `('uint256', 'bytes[]', '(int,int)')`
* `data` - A `bytes` or `bytearray` value that contains abi-encoded data for a
  sequence of values of the abi types in `types`.

**Returns:** A tuple of python values that are equivalent to the abi-encoded
values in `data`.

**Example:**
```python
>>> decode_abi(['uint256'], b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0009')
(12345,)
>>> decode_abi(['bytes1', 'bytes1'], b'a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
(b'a', b'b')
```

### Encoding

Encoding functions convert python values into abi-encoded binary data that can
be sent to the EVM.

#### `eth_abi.encode_single(typ, arg)`

Attempts to encode the python value `arg` into an abi-encoded binary
representation for the abi type `typ`.

**Arguments:**
* `typ` - A `str` value representing an abi type e.g. `'uint256'`, `'bytes[]'`,
  `'(int,int)'`, etc.
* `arg` - A python value that can be encoded into a binary representation for
  the abi type `typ`.

**Returns:** A `bytes` value that contains an abi-encoded binary representation
of the python value `arg`.

```python
>>> encode_single('uint256', 12345)
b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0009'
```

#### `eth_abi.encode_abi(types, args)`

Attempts to encode the sequence of python values in `args` into an abi-encoded
binary representation for the abi types in `types`.

**Arguments:**
* `types` - An iterable of `str` values representing a sequence of abi types
  e.g.  `('uint256', 'bytes[]', '(int,int)')`
* `args` - An iterable of python values that can be encoded into a binary
  representation for the abi types in `types`.

**Returns:** A `bytes` value that contains an abi-encoded binary representation
of the python values in `args`.

```python
>>> encode_abi(['uint256'], [12345])
b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0009'
>>> encode_abi(['bytes32', 'bytes32'], ['a', 'b'])
b'a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
```

## Development

Clone the repository and then run:

```sh
pip install -e . -r requirements-dev.txt
```

### Running the tests

You can run the tests with:

```sh
py.test tests
```

Or you can install `tox` to run the full test suite.

### Releasing

Pandoc is required for transforming the markdown README to the proper format to
render correctly on pypi.

For Debian-like systems:

```sh
apt install pandoc
```

Or on OSX:

```sh
brew install pandoc
```

To release a new version:

```sh
make release bump=$$VERSION_PART_TO_BUMP$$
```

#### How to bumpversion

The version format for this repo is `{major}.{minor}.{patch}` for stable, and
`{major}.{minor}.{patch}-{stage}.{devnum}` for unstable (`stage` can be alpha
or beta).

To issue the next version in line, specify which part to bump, like `make
release bump=minor` or `make release bump=devnum`.

If you are in a beta version, `make release bump=stage` will switch to a
stable.

To issue an unstable version when the current version is stable, specify the
new version explicitly, like `make release bump="--new-version 4.0.0-alpha.1
devnum"`
