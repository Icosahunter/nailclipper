from pathlib import Path

class Html2ImageRenderer:

    def __init__(self):
        from html2image import Html2Image
        from PIL import Image
        self.h2i = None
        self.image = Image
        try:
            self.h2i = Html2Image(size=(2048, 2048))
        except:
            try:
                self.h2i = Html2Image(size=(2048, 2048), browser_executable="google-chrome-stable")
            except:
                pass

    def is_supported(self, uri):
        return True

    def from_url(self, url, size, save_path):
        save_folder = str(Path(save_path).parent)
        save_file = str(Path(save_path).name)
        self.h2i.output_path = save_folder
        self.h2i.screenshot(url=url, save_as=save_file)
        image = self.image.open(save_path)
        image = image.crop(image.getbbox())
        image.save(save_path)
        return True
    
    def from_path(self, file, size, save_path):
        self.from_url(Path(file).as_uri, size, save_path)
        return True