import os
import pytest
import json

from xbox.nano.channel import Channel
from xbox.nano.enum import ChannelClass


@pytest.fixture(scope='session')
def packets():
    # Who cares about RAM anyway?
    data = {}
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'packets')
    for f in os.listdir(data_path):
        with open(os.path.join(data_path, f), 'rb') as fh:
            data[f] = fh.read()

    return data


@pytest.fixture(scope='session')
def json_messages():
    # Who cares about RAM anyway?
    data = {}
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'json_msg')
    for f in os.listdir(data_path):
        with open(os.path.join(data_path, f), 'rt') as fh:
            data[f] = json.load(fh)

    return data


@pytest.fixture(scope='session')
def channels():
    return {
        0: None,
        1024: Channel(None, None, 1024, ChannelClass.Video, 0),
        1025: Channel(None, None, 1025, ChannelClass.Audio, 0),
        1026: Channel(None, None, 1026, ChannelClass.ChatAudio, 0),
        1027: Channel(None, None, 1027, ChannelClass.Control, 0),
        1028: Channel(None, None, 1028, ChannelClass.Input, 0),
        1029: Channel(None, None, 1029, ChannelClass.InputFeedback, 0)
    }
