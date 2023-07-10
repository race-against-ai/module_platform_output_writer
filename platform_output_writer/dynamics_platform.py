import socket


class DynamicsPlatform:
    def __init__(self, destination_address="127.0.0.1", destination_port=40000):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = (destination_address, destination_port)

    def update(
        self, throttle_percent: float, brake_percent: float, steering_percent: float, force_none_rmp: bool = False
    ):
        # X: left - right       pos is right, neg is left, [-1.5; 1.5]      D: 3.0
        # Y: front - back       pos is back, neg is front  [-1.75; 1.75]    D: 3.5
        # Z: up - down          pos is up, neg is down     [-1.5; 1.5]      D: 3.0
        # rpm: vibration, max: 7000, default: 680                           D: 6320

        # rpm amount
        if not force_none_rmp:
            vibration_amount = 680.0 + (6320 * throttle_percent / 100)
        else:
            vibration_amount = 0

        # front-back lean amount
        if brake_percent == 0 and throttle_percent == 0:
            fb_lean = 0.0
        elif throttle_percent > brake_percent:
            fb_lean = 1.75 * throttle_percent / 100
        else:
            fb_lean = -1.75 * brake_percent / 100

        # sideways lean
        lr_lean = -1.5 * steering_percent / 100

        # acc_z is not used, as it is not needed
        self.send_to_platform(rpm=vibration_amount, acc_y=fb_lean, acc_x=lr_lean)

    def send_to_platform(self, acc_x=0.0, acc_y=0.0, acc_z=0.0, rpm=0.0) -> None:
        """
        Sending Information to Platform
        :param acc_x: sidewards tilt (lean)
        :param acc_y: forwards tilt (pivot)
        :param acc_z: upwards movement
        :param rpm: platform vibration
        """
        msg = f'"acceleration_x": {acc_x}, "acceleration_y": {acc_y}, "acceleration_z": {acc_z}, "rpm": {rpm}'
        msg = "{" + msg + "}"
        self.sock.sendto(bytes(msg, "UTF-8"), self.address)
