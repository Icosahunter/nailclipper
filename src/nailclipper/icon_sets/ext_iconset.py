from pathlib import Path
import shutil

class IconSet:

    def __init__(self, extension_map=None):
        self.extension_map = extension_map
    
    def is_supported(self, uri):
        if None in self.extension_map:
            return True
        else:
            return Path(uri).suffix in self.extension_map

    def from_url(self, url, size, save_path):
        return self.from_file(url, size, save_path)

    def from_file(self, file, size, save_path):
        ext = Path(file).suffix
        if ext in self.extension_map:
            shutil.copy(self.extension_map[ext], save_path)
            return True
        elif None in self.extension_map:
            shutil.copy(self.extension_map[None], save_path)
            return True
        else:
            return False