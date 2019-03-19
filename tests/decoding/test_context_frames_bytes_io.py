import pytest

from eth_abi.decoding import (
    ContextFramesBytesIO,
)


@pytest.fixture
def byte_string():
    return bytes(range(100))


@pytest.fixture
def byte_stream(byte_string):
    return ContextFramesBytesIO(byte_string)


def test_read_seek_tell_work_as_normal(byte_string, byte_stream):
    assert byte_stream.tell() == 0
    assert byte_stream.read() == byte_string
    assert byte_stream.tell() == len(byte_string)

    byte_stream.seek(0)

    assert byte_stream.tell() == 0
    assert byte_stream.read() == byte_string
    assert byte_stream.tell() == len(byte_string)


def test_pushing_and_popping_frames(byte_string, byte_stream):
    byte_stream.push_frame(5)
    assert byte_stream.read(5) == byte_string[5:10]
    byte_stream.seek_in_frame(1)
    assert byte_stream.read(1) == byte_string[6:7]

    byte_stream.seek_in_frame(5)
    byte_stream.push_frame(2)
    assert byte_stream.read(5) == byte_string[7:12]
    byte_stream.seek_in_frame(2)
    assert byte_stream.read(1) == byte_string[9:10]

    byte_stream.pop_frame()
    assert byte_stream.read(5) == byte_string[10:15]

    byte_stream.pop_frame()
    assert byte_stream.read(5) == byte_string[0:5]

    with pytest.raises(IndexError):
        byte_stream.pop_frame()
