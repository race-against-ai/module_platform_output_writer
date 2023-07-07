import pynng
import json
import select

from platform_output_writer.dynamics_platform import DynamicsPlatform

PLATFORM_CONTROLLER_PYNNG_ADDRESS = "ipc:///tmp/RAAI/driver_input_reader.ipc"
CONTROL_PANEL_PYNNG_ADDRESS = "ipc:///tmp/RAAI/control_panel.ipc"


def receive_data(sub: pynng.Sub0) -> dict:
    """
    receives data via pynng and returns a variable that stores the content

    :param sub: subscriber
    :param timer: timeout timer for max waiting time for new signal
    """
    msg = sub.recv()
    data = remove_pynng_topic(msg)
    data = json.loads(data)
    return data


def remove_pynng_topic(data, sign: str = " ") -> str:
    """
    removes the topic from data that got received via pynng and returns a variable that stores the content

    :param data: date received from subscriber
    :param sign: last digit from the topic
    """
    decoded_data: str = data.decode()
    i = decoded_data.find(sign)
    decoded_data = decoded_data[i + 1:]
    return decoded_data


class PlatformWriter:

    def __init__(self) -> None:
        # Setting up the Platform
        self.dynamics_platform = DynamicsPlatform()

        # Setting up the pynng receiver
        self.driver_input_receiver = pynng.Sub0()
        self.driver_input_receiver.subscribe("driver_input")
        self.driver_input_receiver.dial(PLATFORM_CONTROLLER_PYNNG_ADDRESS, block=False)

        self.control_panel_receiver = pynng.Sub0()
        self.control_panel_receiver.subscribe("platform")
        self.control_panel_receiver.dial(CONTROL_PANEL_PYNNG_ADDRESS, block=False)

        # initializing the dictionaries with expected values
        self.driver_input = {
            'throttle': 0.0,
            'brake': 0.0,
            'clutch': 0.0,
            'steering': 0.0,
            'tilt_x': 0.0,
            'tilt_y': 0.0,
            'vibration': 0.0
        }

        self.panel_config = {"platform_status": True}

        self.inputs = [self.driver_input_receiver.recv_fd, self.control_panel_receiver.recv_fd]
        self.fd_dict = {
            self.driver_input_receiver.recv_fd: [self.driver_input_receiver, self.driver_input],
            self.control_panel_receiver.recv_fd: [self.control_panel_receiver, self.panel_config]
        }

    def receive_socket_data(self) -> None:
        readable_fds, _, _ = select.select(self.inputs, [], [])

        for readable_fds in readable_fds:
            subscriber = self.fd_dict[readable_fds][0]
            self.fd_dict[readable_fds][1] = receive_data(subscriber)
            # print(self.fd_dict[readable_fds][1])

        self.driver_input = self.fd_dict[self.driver_input_receiver.recv_fd][1]
        self.panel_config = self.fd_dict[self.control_panel_receiver.recv_fd][1]

    def process_platform_data(self) -> None:
        tilt_x = self.driver_input["tilt_x"]
        tilt_y = self.driver_input["tilt_y"]
        rpm = self.driver_input["vibration"]

        platform_status = self.panel_config["platform_status"]

        if platform_status:
            self.dynamics_platform.send_to_platform(acc_x= tilt_x, acc_y=tilt_y, rpm=rpm)

        else:
            self.dynamics_platform.send_to_platform(acc_x=0.0, acc_y=0.0, rpm=0)

    def run(self):
        """Main Function. Run in a Loop"""
        self.receive_socket_data()
        self.process_platform_data()
        # print(self.panel_config)

