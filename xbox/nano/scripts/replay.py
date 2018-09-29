import dpkt
import logging
import argparse
from xbox.nano.render.client.sdl import SDLClient
from xbox.nano.render.client.file import FileClient
from xbox.nano.protocol import NanoProtocol, StreamerProtocol, ControlProtocol


class DummyStreamerProtocol(StreamerProtocol):
    def send_message(self, msg):
        pass


class DummyControlProtocol(ControlProtocol):
    def send_message(self, msg):
        pass


def replay(client, pcap_file, tcp_port, udp_port):
    with open(pcap_file, 'rb') as fh:
        proto = NanoProtocol(client, None, None, None, None)
        proto.streamer_protocol = DummyStreamerProtocol('', 0, proto)
        proto.control_protocol = DummyControlProtocol('', 0, proto)

        proto.control_protocol.on_message += proto._on_control_message
        proto.streamer_protocol.on_message += proto._on_streamer_message

        client.open(proto)

        for ts, buf in dpkt.pcap.Reader(fh):
            eth = dpkt.ethernet.Ethernet(buf)

            # Make sure the Ethernet data contains an IP packet
            if not isinstance(eth.data, dpkt.ip.IP):
                continue

            ip = eth.data

            if isinstance(ip.data, dpkt.tcp.TCP):
                if ip.data.sport != tcp_port and ip.data.dport != tcp_port:
                    continue

                from_client = ip.data.dport == tcp_port

                if not from_client:
                    proto.control_protocol.handle(ip.data.data)

            elif isinstance(ip.data, dpkt.udp.UDP):
                if ip.data.sport != udp_port and ip.data.dport != udp_port:
                    continue

                from_client = ip.data.dport == udp_port
                if not from_client:
                    proto.streamer_protocol.handle(ip.data.data, '')

            else:
                continue

            client.pump()


def main():
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(
        description='Parse PCAP files and replay SG sessions'
    )
    parser.add_argument('file', help='Path to PCAP')
    parser.add_argument('tcp_port', type=int, help='Server TCP Port (console)')
    parser.add_argument('udp_port', type=int, help='Server UDP Port (console)')
    parser.add_argument('--output', '-o', help='Write stream to file')
    parser.add_argument('--frames', '-f', action='store_true',
                        help='Save single frames')
    args = parser.parse_args()

    if args.output:
        client = FileClient(args.output, save_frames=args.frames)
    else:
        client = SDLClient(1280, 720)

    replay(client, args.file, args.tcp_port, args.udp_port)


if __name__ == '__main__':
    main()
