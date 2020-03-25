import struct
import construct
from datetime import datetime


class ReferenceTimestampAdapter(construct.Adapter):
    """
    Construct-Adapter for JSON field.
    Parses and dumps JSON.
    """
    def __init__(self):
        super(self.__class__, self).__init__(construct.Int64ul)

    def _encode(self, obj, context, path):
        if not isinstance(obj, datetime):
            raise TypeError('Object not of type datetime')
        # Timestamp in microseconds since epoch (uint64 LE)
        return int(obj.timestamp() * 1000)

    def _decode(self, obj, context, path):
        # Convert from microsecond since epoch to datetime (uint64 LE)
        return datetime.utcfromtimestamp(obj / 1000)
