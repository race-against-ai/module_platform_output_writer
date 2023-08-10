import pynng
import json
import select

from platform_output_writer.dynamics_platform import DynamicsPlatform

PLATFORM_CONTROLLER_PYNNG_ADDRESS = "ipc:///tmp/RAAI/driver_input_reader.ipc"
CONTROL_PANEL_PYNNG_ADDRESS = "ipc:///tmp/RAAI/control_panel.ipc"


def receive_data(sub: pynng.Sub0) -> str:
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
    decoded_data = decoded_data[i + 1 :]
    return decoded_data


def read_config(config_file_path: str) -> dict:
    if os.path.isfile(config_file_path):
        with open(config_file_path, 'r') as file:
            return json.load(file)
    else:
        return create_config(config_file_path)


def create_config(config_file_path: str) -> dict:
    """wrote this to ensure that a config file always exists, ports have to be adjusted if necessary"""
    print("No Config File found, creating new one from Template")
    print("---!Using default argments for a Config file")
    template = {
        "pynng": {
            "publishers": {
            },
            "subscribers": {
                "driver_input_receiver": {
                    "address": "ipc:///tmp/RAAI/driver_input_reader.ipc",
                    "topics": {
                        "driver_input": "driver_input"
                    }
                },
                "control_panel_receiver": {
                    "address": "ipc:///tmp/RAAI/control_panel.ipc",
                    "topics": {
                        "platform": "platform"
                    }
                }
            }
        }
    }


class PlatformWriter:
    def __init__(self, config_file: str = "./platform_output_writer_config.json") -> None:
        # Setting up the Platform
        self.dynamics_platform = DynamicsPlatform()
        self.config = read_config(config_file)
        # Setting up the pynng receiver
        input_address = self.config["pynng"]["subscribers"]["driver_input_receiver"]["address"]
        input_topic = self.config["pynng"]["subscribers"]["driver_input_receiver"]["topics"]["driver_input"]
        self.driver_input_receiver = pynng.Sub0()
        self.driver_input_receiver.subscribe(input_topic)
        self.driver_input_receiver.dial(input_address, block=False)

        panel_address = self.config["pynng"]["subscribers"]["control_panel_receiver"]["address"]
        panel_topic = self.config["pynng"]["subscribers"]["control_panel_receiver"]["topics"]["platform"]
        self.control_panel_receiver = pynng.Sub0()
        self.control_panel_receiver.subscribe(panel_topic)
        self.control_panel_receiver.dial(panel_address, block=False)

        # initializing the dictionaries with expected values
        self.driver_input = {
            "throttle": 0.0,
            "brake": 0.0,
            "clutch": 0.0,
            "steering": 0.0,
            "tilt_x": 0.0,
            "tilt_y": 0.0,
            "vibration": 0.0,
        }

        self.panel_config = {"platform_status": True}

        self.inputs = [self.driver_input_receiver.recv_fd, self.control_panel_receiver.recv_fd]
        self.fd_dict = {
            self.driver_input_receiver.recv_fd: [self.driver_input_receiver, self.driver_input],
            self.control_panel_receiver.recv_fd: [self.control_panel_receiver, self.panel_config],
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
        throttle = self.driver_input["throttle"]
        brake = self.driver_input["brake"]
        clutch = self.driver_input["clutch"]
        steering = self.driver_input["steering"]

        tilt_x = self.driver_input["tilt_x"]
        tilt_y = self.driver_input["tilt_y"]
        rpm = self.driver_input["vibration"]

        platform_status = self.panel_config["platform_status"]

        if platform_status:
            # disabled because the tilt was erratic and wayyy too much
            # self.dynamics_platform.send_to_platform(acc_x=tilt_x, acc_y=tilt_y, rpm=rpm)
            self.dynamics_platform.update(
                throttle_percent=throttle, brake_percent=brake, steering_percent=steering, force_none_rmp=False
            )

        else:
            # self.dynamics_platform.send_to_platform(acc_x=0.0, acc_y=0.0, rpm=0)
            self.dynamics_platform.update(0, 0, 0, True)

    def run(self):
        """Main Function. Run in a Loop"""
        self.receive_socket_data()
        self.process_platform_data()
        # print(self.panel_config)
