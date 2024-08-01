from pydantic import BaseModel
from typing import List


class PortBaseConfig(BaseModel):
    port: str = "COM3"
    baudrate: str = "38400"


class InputSerialConfigItem(PortBaseConfig):
    pass


class OutputSerialConfigItem(PortBaseConfig):
    offset: int = 0


class SerialConfig(BaseModel):
    inputs: List[InputSerialConfigItem] = [InputSerialConfigItem]
    outputs: List[OutputSerialConfigItem] = [OutputSerialConfigItem]


class ArduinoConfig(PortBaseConfig):
    test_message: str = 'test_message'


class ProgramConfig(BaseModel):
    line_count: int = 0


class Config(BaseModel):
    test_status: bool = True
    program_config: ProgramConfig = ProgramConfig()
    arduino_config: ArduinoConfig = ArduinoConfig()
    serial_config: SerialConfig = SerialConfig()
