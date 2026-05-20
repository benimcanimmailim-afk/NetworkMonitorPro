import json
import os

class ConfigManager:
    def __init__(self):
        appdata_path = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'NetMonitorV5')
        if not os.path.exists(appdata_path): 
            os.makedirs(appdata_path)
        self.config_file = os.path.join(appdata_path, "config.json")

    def load_all_packages(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                return json.load(f)
        return {}

    def save_package(self, name, package_data):
        # package_data artık şu yapıda olacak: [{"ip": "...", "tag": "..."}, ...]
        data = self.load_all_packages()
        data[name] = package_data
        with open(self.config_file, "w") as f:
            json.dump(data, f)

    def delete_package(self, name):
        data = self.load_all_packages()
        if name in data:
            del data[name]
            with open(self.config_file, "w") as f:
                json.dump(data, f)
            return True
        return False