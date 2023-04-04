import logging 
import zmq
import carla


# Constants
# TODO: move to another location
ADDR = "127.0.0.1"
PUB_PORT = "8080"
SUB_PORT = "8000"

CAMERA_TOPIC = b"" # TODO: standardize
CONTROL_TOPIC = b"carla/ego_vehicle/control"

class ZmqControl(object):
    """
    Sends: all sensors data
    Receives: acceleration and brake
    """
    
    def __init__(self, pub_addr: str = f"{ADDR}:{PUB_PORT}", sub_addr: str = f"{ADDR}:{SUB_PORT}") -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing ZMQ control")

        self.pub_addr = pub_addr
        self.sub_addr = sub_addr

        context = zmq.Context()
        pub_socket = context.socket(zmq.PUB)
        pub_socket.bind(self.pub_addr)

        sub_socket = context.socket(zmq.SUB)
        sub_socket.bind(self.sub_addr)

        self.pub_socket = pub_socket
        self.sub_socket = sub_socket

    def send_sensors(self, sensors_data) -> bool:
        ""
        # TODO: send sensor via ZMQ
        pass

    def receive_control_raw(self) -> str:
        """
        Receive control as string 
        """
        # TODO: receive sensor via ZMQ
        topic, msg = self.sub_socket.recv_multipart()
        if topic != CONTROL_TOPIC:
            return

        topic, msg = topic.decode('utf-8'), msg.decode('utf-8')
        self.logger.info(f"Received:\n\ttopic: {topic}\n\tmessage: {msg}")
        return msg

    def receive_control(self) -> carla.VehicleControl:
        msg = self.receive_control_raw()
        return ZmqControl.to_vehicle_control(msg)

    @staticmethod
    def to_vehicle_control(string: str) -> carla.VehicleControl:
        vehicle_control = carla.VehicleControl()
        # TODO: standardize string format
        return vehicle_control