from pathlib import Path
from warnings import warn

class Html2ImageRenderer:

    h2i = None
    pil = None

    @staticmethod
    def init():
        try:
            from html2image import Html2Image
            import PIL

            Html2ImageRenderer.pil = PIL
            try:
                Html2ImageRenderer.h2i = Html2Image(size=(2048, 2048))
            except:
                Html2ImageRenderer.h2i = Html2Image(size=(2048, 2048), browser_executable="google-chrome-stable")
        except Exception as e:
            warn(f'Could not load Html2ImageRenderer: {e}')

    @staticmethod
    def is_supported(uri):
        return Path(uri).suffix in ['.apng', '.avif', '.gif', '.jpeg', '.jpg', '.png', '.svg', '.webp', '.bmp', '.ico', '.pdf', '.txt', '.md']

    @staticmethod
    def from_url(url, size, save_path):
        try:
            save_folder = str(Path(save_path).parent)
            save_file = str(Path(save_path).name)
            Html2ImageRenderer.h2i.output_path = save_folder
            Html2ImageRenderer.h2i.screenshot(url=url, save_as=save_file)
            image = Html2ImageRenderer.pil.Image.open(save_path)
            image = image.crop(image.getbbox())
            image.save(save_path)
            return True
        except Exception as e:
            warn(f'Could not generate thumbnail for {url} using Html2ImageRenderer: {e}')
            return False

    @staticmethod
    def from_path(file, size, save_path):
        return Html2ImageRenderer.from_url(Path(file).as_uri, size, save_path)
