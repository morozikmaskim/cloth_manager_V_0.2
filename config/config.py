import configparser
import os

class ConfigManager:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Файл конфигурации {config_file} не найден!")
        self.config.read(config_file)
        self.db_config = self.config['Database']

    def get_connection_string(self):
        return (
            f'DRIVER={self.db_config.get("DRIVER", "")};'
            f'SERVER={self.db_config.get("SERVER", "")};'
            f'DATABASE={self.db_config.get("DATABASE", "")};'
            f'Trusted_Connection={self.db_config.get("Trusted_Connection", "yes")};'
        )