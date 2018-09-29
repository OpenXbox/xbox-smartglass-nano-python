from xbox.nano.packet import control


def session_create(**kwargs):
    return control.session_create(**kwargs)


def session_create_response(**kwargs):
    return control.session_create_response(**kwargs)


def session_destroy(**kwargs):
    return control.session_destroy(**kwargs)


def video_statistics(**kwargs):
    return control.video_statistics(**kwargs)


def realtime_telemetry(**kwargs):
    return control.realtime_telemetry(**kwargs)


def change_video_quality(unk3, unk4, unk5, unk6, unk7, unk8):
    return control.change_video_quality(
        unk3=unk3,
        unk4=unk4,
        unk5=unk5,
        unk6=unk6,
        unk7=unk7,
        unk8=unk8
    )


def initiate_network_test(**kwargs):
    return control.initiate_network_test(**kwargs)


def network_information(**kwargs):
    return control.network_information(**kwargs)


def network_test_response(**kwargs):
    return control.network_test_response(**kwargs)


def controller_event(event, controller_num):
    return control.controller_event(
        event=event,
        controller_num=controller_num
    )


def control_header(prev_seq_dup, unk1, unk2, opcode, payload):
    return control.control_packet(
        prev_seq_dup=prev_seq_dup,
        unk1=unk1,
        unk2=unk2,
        opcode=opcode,
        payload=payload
    )
