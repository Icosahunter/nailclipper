from pathlib import Path
from warnings import warn

class Pdf2ImageRenderer:

    p2i = None

    @staticmethod
    def init():
        try:
            import pdf2image
            Pdf2ImageRenderer.p2i = pdf2image
        except Exception as e:
            warn(f'Could not load Pdf2ImageRenderer: {e}')

    @staticmethod
    def is_supported(uri):
        return Path(uri).suffix == '.pdf'

    @staticmethod
    def from_file(file, size, save_path):
        try:
            image = Pdf2ImageRenderer.p2i.convert_from_path(file, single_file=True)[0]
            image.save(save_path)
            return True
        except Exception as e:
            warn(f'Could not generate thumbnail from {file} using Pdf2ImageRenderer: {e}')
            return False