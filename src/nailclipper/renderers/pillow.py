from pathlib import Path
from warnings import warn

class PillowRenderer:

    pil = None

    @staticmethod
    def init():
        try:
            import PIL
            PillowRenderer.pil = PIL
        except Exception as e:
            warn(f'Could not load PillowRenderer: {e}')

    @staticmethod
    def is_supported(uri):
        if PillowRenderer.pil:
            return Path(uri).suffix in [x for x, y in PillowRenderer.pil.Image.registered_extensions().items() if y in PillowRenderer.pil.Image.OPEN]
        else:
            return False

    @staticmethod
    def from_file(file, size, save_path):
        try:
            image = PillowRenderer.pil.Image.open(file)
            image.thumbnail(size)
            image.save(save_path)
            return True
        except Exception as e:
            warn(f'Could not generate thumbnail for {file} using PillowRenderer: {e}')
            return False