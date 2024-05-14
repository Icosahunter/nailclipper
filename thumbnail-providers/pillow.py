from PIL import Image
from tempfile import Tempfile

class PillowThumbProvider:

    self.supported = [x for x, y in Image.registered_extensions() if y in Image.OPEN]

    def from_file(self, file, size, save_path):
        try:
            image = Image.open(file)
            image.thumbnail(size).save(save_path)
            return True
        except:
            return False