from pathlib import Path

class Pdf2ImageRenderer:

    def __init__(self):
        import pdf2image
        self.p2i = pdf2image

    def is_supported(self, uri):
        return Path(uri).suffix == '.pdf'

    def from_file(self, file, size, save_path):
        image = self.p2i.convert_from_path(file, single_file=True)[0]
        image.save(save_path)
        return True