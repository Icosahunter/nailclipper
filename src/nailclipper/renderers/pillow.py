class PillowRenderer:

    @staticmethod
    def supported():
        from PIL import Image
        return [x for x, y in Image.registered_extensions().items() if y in Image.OPEN]

    @staticmethod
    def from_file(file, size, save_path):
        from PIL import Image
        image = Image.open(file)
        image.thumbnail(size)
        image.save(save_path, 'png')
        return True
