import os
import tempfile
import mimetypes
from pathlib import Path
from urllib.parse import urlparse, unquote

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from nailclipper.renderers import PillowRenderer, Html2ImageRenderer, Pdf2ImageRenderer
from nailclipper.enums import *

class ThumbnailGenerator:

    def __init__(self,
            renderers = [PillowRenderer, Pdf2ImageRenderer, Html2ImageRenderer],
            resize_style = ResizeStyle.FIT,
            mask = None,
            resample = Resample.AUTO,
            upscale = True,
            background = (0, 0, 0, 0),
            foreground = None,
            size = Size.NORMAL):

        #TODO: implement 'shared' thumbnails part of the Freedesktop spec

        self.renderers = renderers
        self.resize_style = resize_style
        self.mask = mask
        self.resample = resample
        self.upscale = upscale
        self.background = background
        self.foreground = foreground
        self.size = size

        if type(self.renderers[0]) == type:
            self.renderers = [x() for x in self.renderers]
    
    def init(self):
        for renderer in self.renderers:
            renderer.init()

    def create_thumbnail(self, uri, save_path):

        save_path.parent.mkdir(parents=True, exist_ok=True)

        image = self._render_thumbnail(uri, self.size)

        if image is None:
            return image
        
        image = image.convert('RGBA')
        image = self._resize_image(image, self.size, self.resize_style)

        background = self._create_ground(self.background, image.size, self.size)
        image = self._apply_layer(background, image)

        if self.foreground:
            foreground = self._create_ground(self.foreground, image.size, self.size)
            image = self._apply_layer(image, foreground)

        if self.mask:
            image = self._apply_mask(image, Image.open(self.mask))

        metadata = self._thumbnail_metadata(uri)

        image.save(save_path, 'png', pnginfo=metadata)
        
        return save_path
    
    def _render_thumbnail(self, uri, size):
        success = False
        parsed = urlparse(uri)
        image = None

        file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        file.close()
        path = file.name
        for renderer in self.renderers:
            if renderer.is_supported(uri):
                if parsed.scheme == 'file' and hasattr(renderer, 'from_file') and renderer.from_file(Path(parsed.path), size, file.name):
                    success = True
                    break
                elif hasattr(renderer, 'from_url') and renderer.from_url(uri, size, file.name):
                    success = True
                    break
        
        if success:
            image = Image.open(file.name)
        
        del file
        
        return image
    
    def _apply_layer(self, image1, image2):
        pos = (
            int((image1.size[0] - image2.size[0]) / 2),
            int((image1.size[1] - image2.size[1]) / 2)
        )
        image1.alpha_composite(image2, pos)
        return image1
    
    def _create_ground(self, ground, image_size, desired_size):
        if self.resize_style == ResizeStyle.FIT:
            bg_size = image_size
        else:
            bg_size = desired_size
        
        if type(ground) is str:
            ground = Image.open(ground)
            ground = self._resize_image(ground, bg_size, ResizeStyle.FILL)
        else:
            ground = Image.new('RGBA', bg_size, ground)
        
        return ground
    
    def _apply_mask(self, image, mask):
        masked = Image.new(image.mode, image.size, (0, 0, 0, 0))
        mask = self._resize_image(mask, image.size, ResizeStyle.STRETCH)
        masked.paste(image, (0, 0), mask=mask)
        return masked
    
    def _resize_image(self, image, size, resize_style):

        resample = self.resample

        if resample == Resample.AUTO:
            if max(image.size) < 128 and self.upscale:
                resample = Resample.NEAREST
            else:
                resample = Resample.BILINEAR

        if not self.upscale and (image_size[0] > desired_size[0] or image_size[1] > desired_size[1]):
            size = self._fit_size(desired_size, image_size)

        if resize_style == ResizeStyle.FILL:
            x, y, w, h = self._fill_size(image.size, size)
            image = image.resize((w, h), resample=resample)
            image = image.crop((x, y, x+size[0], y+size[1]))
        elif resize_style == ResizeStyle.STRETCH:
            image = image.resize(size, resample=resample)
        else:
            image = image.resize(self._fit_size(image.size, size), resample=resample)
        
        return image
    
    def _fit_size(self, image_size, desired_size):
        r1 = image_size[0] / image_size[1]
        r2 = desired_size[0] / desired_size[1]
        if r1 > r2:
            w = desired_size[0]
            h = (desired_size[0]/image_size[0])*image_size[1]
        else:
            h = desired_size[1]
            w = (desired_size[1]/image_size[1])*image_size[0]
        return (int(w), int(h))

    def _fill_size(self, image_size, desired_size):
        r1 = image_size[0] / image_size[1]
        r2 = desired_size[0] / desired_size[1]
        if r1 < r2:
            w = desired_size[0]
            h = (desired_size[0]/image_size[0])*image_size[1]
            x = 0
            y = (h - desired_size[1]) / 2
        else:
            h = desired_size[1]
            w = (desired_size[1]/image_size[1])*image_size[0]
            x = (w - desired_size[0]) / 2
            y = 0
        return (int(x), int(y), int(w), int(h))
    
    def _thumbnail_metadata(self, uri):
        metadata = PngInfo()
        parsed = urlparse(uri)
        if parsed.scheme == 'file':
            path = Path(unquote(parsed.path))
            metadata.add_text('Thumb::MTime', str(os.stat(path).st_mtime))
            metadata.add_text('Thumb::MSize', str(os.path.getsize(path)))
        metadata.add_text('Thumb::URI', uri)
        mimetype = mimetypes.guess_type(uri, strict=False)[0]
        if mimetype is not None:
            metadata.add_text('Thumb::Mimetype', mimetype)
        return metadata