import dpkt
import shutil
import textwrap
import argparse
from xbox.nano import packer
from xbox.nano.channel import Channel
from xbox.nano.enum import RtpPayloadType, ChannelClass, \
    ChannelControlPayloadType


channels = {
    0: "None",
    1024: Channel(None, None, 1024, ChannelClass.Video, 0),
    1025: Channel(None, None, 1025, ChannelClass.Audio, 0),
    1026: Channel(None, None, 1026, ChannelClass.ChatAudio, 0),
    1027: Channel(None, None, 1027, ChannelClass.Control, 0),
    1028: Channel(None, None, 1028, ChannelClass.Input, 0),
    1029: Channel(None, None, 1029, ChannelClass.InputFeedback, 0)
}


def parse(pcap_file, tcp_port, udp_port):
    width = shutil.get_terminal_size().columns
    col_width = width // 2 - 3
    wrapper = textwrap.TextWrapper(col_width, replace_whitespace=False)

    with open(pcap_file, 'rb') as fh:
        for ts, buf in dpkt.pcap.Reader(fh):
            eth = dpkt.ethernet.Ethernet(buf)

            # Make sure the Ethernet data contains an IP packet
            if not isinstance(eth.data, dpkt.ip.IP):
                continue

            ip = eth.data

            if isinstance(ip.data, dpkt.tcp.TCP):
                if ip.data.sport != tcp_port and ip.data.dport != tcp_port:
                    continue

                try:
                    msgs = packer.unpack_tcp(ip.data.data, channels)
                    msgs = list(msgs)
                except Exception as e:
                    print("Error: {}".format(e))
                    continue
                is_client = ip.data.dport == tcp_port
            elif isinstance(ip.data, dpkt.udp.UDP):
                if ip.data.sport != udp_port and ip.data.dport != udp_port:
                    continue

                try:
                    msgs = [packer.unpack(ip.data.data, channels)]
                except Exception as e:
                    print("Error: {}".format(e))
                    continue
                is_client = ip.data.dport == udp_port
            else:
                continue

            for msg in msgs:
                payload_type = msg.header.flags.payload_type
                channel_id = msg.header.ssrc.channel_id

                type_str = '%s Seq %i ' % \
                    (RtpPayloadType(payload_type), msg.header.sequence_num)

                if payload_type == RtpPayloadType.ChannelControl:
                    type_str += ' (%s)' % \
                        ChannelControlPayloadType(msg.payload.type)
                # elif payload_type == PayloadType.Streamer:
                #     type_str += ' (Type: %i)' \
                #         % msg.payload.streamer_header.packet_type

                if channel_id != 0:
                    type_str += ' | %s' % channels[channel_id]

                direction = '>' if is_client else '<'
                print(' {} '.format(type_str).center(width, direction))

                lines = str(msg).split('\n')
                for line in lines:
                    line = wrapper.wrap(line)
                    for i in line:
                        if is_client:
                            print('{0: <{1}}'.format(i, col_width), '│')
                        else:
                            print(
                                ' ' * col_width, '│',
                                '{0}'.format(i, col_width)
                            )


def main():
    parser = argparse.ArgumentParser(
        description='Parse PCAP files and show SG sessions'
    )
    parser.add_argument('file', help='Path to PCAP')
    parser.add_argument('tcp_port', type=int, help='Server TCP Port (console)')
    parser.add_argument('udp_port', type=int, help='Server UDP Port (console)')
    args = parser.parse_args()

    parse(args.file, args.tcp_port, args.udp_port)


if __name__ == '__main__':
    main()
