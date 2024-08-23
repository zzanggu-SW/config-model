from pydantic import BaseModel, field_validator, ValidationInfo
from typing import Optional, Union, List
from enum import Enum
import datetime
import json
import os
import shutil


class EncodingEnum(str, Enum):
    ASCII = "ascii"
    UTF8 = "utf-8"
    UTF16 = "utf-16"
    ISO88591 = "iso-8859-1"
    UTF32 = "utf-32"


class FormatEnum(str, Enum):
    STX_ETX = "STX/ETX"
    CRLF = "CRLF"
    LF = "LF"
    CR = "CR"


class ComputerTypeEnum(str, Enum):
    Vision = "vision"
    Server = "server"


class SerialTypeEnum(str, Enum):
    SingleGear = "single_gear"
    MultiGear = "multi_gear"
    TransparentBelt = "transparent_belt"


class PortBaseConfig(BaseModel):
    port: str = "COM3"
    baudrate: int = 38400


class InputSerialConfigItem(PortBaseConfig):
    pin: int = 2

    @field_validator("pin")
    def check_pin_range(cls, v):
        if not 2 <= v <= 9:
            raise ValueError("pin must be between 2 and 9")
        return v


class OutputSerialConfigItem(PortBaseConfig):
    offset: int = 0
    pin: int = 30

    @field_validator("pin")
    def check_pin_range(cls, v):
        if not 30 <= v <= 37:
            raise ValueError("pin must be between 30 and 37")
        return v


class SerialConfig(BaseModel):
    inputs: List[InputSerialConfigItem] = [InputSerialConfigItem]
    outputs: List[OutputSerialConfigItem] = [OutputSerialConfigItem]
    message_encode_type: EncodingEnum = EncodingEnum.UTF8
    message_format_type: FormatEnum = FormatEnum.CRLF
    baudrate: int = 38400
    test_message_to_sorter: str = "0"


class ArduinoConfig(PortBaseConfig):
    test_message: str = "test_message"


class ProgramConfig(BaseModel):
    line_count: int = 0


class Config(BaseModel):
    program_check: bool = False
    test_status: bool = True
    program_config: ProgramConfig = ProgramConfig()
    arduino_config: ArduinoConfig = ArduinoConfig()
    serial_config: SerialConfig = SerialConfig()


class ServerConfig(BaseModel):
    program_check: bool = False
    test_status: bool = True
    program_config: ProgramConfig = ProgramConfig()
    arduino_config: ArduinoConfig = ArduinoConfig()
    serial_config: SerialConfig = SerialConfig()


ExecuteFileMap = {
    ComputerTypeEnum.Vision.value: "vision_config_app.py",
    ComputerTypeEnum.Server.value: "server_config_app.py",
}


class VisionConfig(BaseModel):
    pass


class RootConfig(BaseModel):
    config_type: ComputerTypeEnum = ComputerTypeEnum.Vision
    config: Optional[Union[ServerConfig]] = None

    @field_validator("config", mode="before")
    def validate_config(cls, config, values: ValidationInfo):
        config_type = values.data.get("config_type")

        if not config:
            return

        if config_type == ComputerTypeEnum.Vision:
            if isinstance(config, dict):
                config = VisionConfig(**config)
            elif not isinstance(config, VisionConfig):
                raise ValueError(
                    "When config_type is 'vision', config must be of type VisionConfig"
                )
        elif config_type == ComputerTypeEnum.Server:
            if isinstance(config, dict):
                config = ServerConfig(**config)
            elif not isinstance(config, ServerConfig):
                raise ValueError(
                    "When config_type is 'server', config must be of type ServerConfig"
                )
        return config


def backup_config():
    """Backup the aiofarm_config.json, pyproject.toml, and poetry.lock files to the aiofarm_config_backup directory."""
    
    def backup_file(source_file, backup_file):
        if os.path.exists(source_file):
            shutil.copy2(source_file, backup_file)
            print(f"Backup successful: {backup_file}")
        else:
            print(f"Source file does not exist: {source_file}")
    
    home_dir = os.path.expanduser("~")
    backup_dir = os.path.join(home_dir, "aiofarm_config_backup")

    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Generate a unique timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    
    # List of files to backup
    files_to_backup = {
        "aiofarm_config.json": os.path.join(home_dir, "aiofarm_config.json"),
        "pyproject.toml": os.path.join(home_dir, "pyproject.toml"),
        "poetry.lock": os.path.join(home_dir, "poetry.lock")
    }

    # Backup each file
    for name, source_file in files_to_backup.items():
        backup_file_name = f"{name.split('.')[0]}_{timestamp}.{name.split('.')[1]}"
        backup_file_path = os.path.join(backup_dir, backup_file_name)
        backup_file(source_file, backup_file_path)

def save_config(root_config: RootConfig):
    RootConfig.model_validate(root_config)
    try:
        with open(os.path.expanduser("~/aiofarm_config.json"), "w", encoding="utf-8") as f:
            json.dump(root_config.model_dump(), f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


DEFAULT_SERVER_ROOT = RootConfig(
    config_type=ComputerTypeEnum.Server,
    config=ServerConfig(
        arduino_config=ArduinoConfig(port="COM3"),
        serial_config=SerialConfig(
            inputs=[InputSerialConfigItem(port="COM4")],
            outputs=[
                OutputSerialConfigItem(port="COM5", offset=23),
                OutputSerialConfigItem(port="COM6", offset=23),
            ],
        ),
    ),
)


# DEFAULT_VISION_ROOT_CONFIG = RootConfig(
#     config_type=ComputerTypeEnum.Vision, config=VisionConfig()
# )


def load_server_root_config() -> RootConfig:
    """Server 설정 프레임과 일치하는 RootConfig를 반환합니다."""
    is_wrong_process = False
    try:
        with open(os.path.expanduser("~/aiofarm_config.json"), "r") as f:
            data = json.load(f)
        root_config = RootConfig(**data)
        ServerConfig(**root_config.config.model_dump())
    except Exception as e:
        is_wrong_process = True
        print("Load config Error", e)
        root_config = DEFAULT_SERVER_ROOT

    if root_config.config_type != ComputerTypeEnum.Server or not root_config.config:
        is_wrong_process = True
        root_config: RootConfig = DEFAULT_SERVER_ROOT

    if is_wrong_process:
        with open(os.path.expanduser("~/aiofarm_config.json"), "w") as f:
            json.dump(root_config.model_dump(), f, indent=4)

    return root_config


def load_vision_config() -> None:
    pass


def load_config() -> RootConfig:
    """Load settings from a JSON file and return a Config object."""
    try:
        with open(os.path.expanduser("~/aiofarm_config.json"), "r") as f:
            data = json.load(f)
        config = RootConfig.model_validate(data)
    except Exception as e:
        print("Load config Error", e)
        DEFAULT_CONFIG = RootConfig(
            config_type=ComputerTypeEnum.Server,
            config=ServerConfig(
                arduino_config=ArduinoConfig(port="COM3"),
                serial_config=SerialConfig(
                    inputs=[InputSerialConfigItem(port="COM4")],
                    outputs=[
                        OutputSerialConfigItem(port="COM5", offset=23),
                        OutputSerialConfigItem(port="COM6", offset=23),
                    ],
                ),
            ),
        )
        return DEFAULT_CONFIG
    return config
