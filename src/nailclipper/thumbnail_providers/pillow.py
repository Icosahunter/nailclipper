from PIL import Image

class PillowThumbnailProvider:

    supported = [x for x, y in Image.registered_extensions().items() if y in Image.OPEN]

    @staticmethod
    def from_file(file, size, save_path):
        try:
            image = Image.open(file)
            image.thumbnail(size)
            image.save(save_path)
            return True
        except:
            return False
