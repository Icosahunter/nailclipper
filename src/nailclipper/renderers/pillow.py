from pathlib import Path

class PillowRenderer:

    def __init__(self):
        import PIL
        self.pil = PIL

    def is_supported(self, uri):
        return Path(uri).suffix in [x for x, y in self.pil.Image.registered_extensions().items() if y in self.pil.Image.OPEN]

    def from_file(self, file, size, save_path):
        image = self.pil.Image.open(file)
        image.thumbnail(size)
        image.save(save_path)
        return True
