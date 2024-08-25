from pathlib import Path
import mimetypes
import shutil

class MimetypeIconSet:

    def __init__(self, mimetype_map={}):
        self.mimetype_map = mimetype_map

    def is_supported(self, uri):
        if None in self.mimetype_map:
            return True
        else:
            return mimetypes.guess_type(uri)[0] in self.mimetype_map

    def from_url(self, url, size, save_path):
        return self.from_file(url, size, save_path)

    def from_file(self, file, size, save_path):
        mimetype = mimetypes.guess_type(file)[0]
        if mimetype in self.mimetype_map:
            shutil.copy(self.mimetype_map[mimetype], save_path)
            return True
        elif None in self.mimetype_map:
            shutil.copy(self.mimetype_map[None], save_path)
            return True
        else:
            return False
