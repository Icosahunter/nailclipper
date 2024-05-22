import os
import time
import platform
import hashlib
import tempfile
import mimetypes
import warnings
from pathlib import Path
from urllib.parse import urlparse, unquote

from platformdirs import user_cache_dir
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from nailclipper.renderers import PillowRenderer, Html2ImageRenderer, Pdf2ImageRenderer

class ComplianceError(ValueError):
    pass

class Size:
    """ Thumnail size constants from the Freedesktop thumbnail spec """
    NORMAL  = (128 , 128 )
    LARGE   = (256 , 256 )
    XLARGE  = (512 , 512 )
    XXLARGE = (1024, 1024)

freedesktop_sizes = [Size.NORMAL, Size.LARGE, Size.XLARGE, Size.XXLARGE]

class RefreshPolicy:
    """ Methods for determining if a thumbnail needs to be updated """

    @classmethod
    def _takes_args(self, val):
        return val in [self.INTERVAL]

    @staticmethod
    def FREEDESKTOP(thumbnail_path, file_uri):
        """ Thumbnail update algorithm from the Freedesktop thumbnail spec """
        if urlparse(file_uri).scheme != 'file':
            return False
        image = Image.open(thumbnail_path)
        file_path = unquote(urlparse(file_uri).path)
        file_mtime = os.stat(file_path).st_mtime
        file_size = os.path.getsize(file_path)
        return ((not self._options['is_shared'] and not 'Thumb::MTime' in image.text) 
            or ('Thumb::MTime' in image.text and file_mtime != image.text['Thumb::MTime']) 
            or ('Thumb::Size' in image.text and file_size != image.text['Thumb::Size']))
    
    @staticmethod
    def INTERVAL(days=10):
        """ Update algorithm based on how old a thumbnail is in days """
        # This method returns a method, so you can specify the update interval
        def interval_check(thumbnail_path, file_uri):
            thumb_mtime = os.stat(thumbnail_path).st_mtime
            return (time.time() - thumb_mtime) >= (days*24*60*60)
        return interval_check
    
    @staticmethod
    def AUTO(thumbnail_path, file_uri):
        """ This is the same as RefreshPolicy.FREEDESKTOP for local files, but uses RefreshPolicy.INTERVAL(30) for all other content."""
        if urlparse(file_uri).scheme == 'file':
            return RefreshPolicy.FREEDESKTOP(thumbnail_path, file_uri)
        else:
            return RefreshPolicy.INTERVAL(days=30)(thumbnail_path, file_uri)

    @staticmethod
    def NEVER(thumbnail_path, file_uri):
        """ Never update the thumbnail once created. """
        return False

def get_xdg_home():
    """ Gets the XDG cache directory. For windows this returns the same cache location that the Windows version of KDE Dolphin uses (AppData/.cache). """
    if platform.system() == 'Windows':
        return Path(os.path.expandvars('%LOCALAPPDATA%')) / 'cache'
    elif os.environ.get('XDG_CACHE_HOME', None):
        return Path(os.environ.get('XDG_CACHE_HOME'))
    else:
        return Path.home() / '.cache'

class CacheDir:
    """ Default cache directory options. """
    FREEDESKTOP = get_xdg_home() / 'thumbnails'
    TEMP        = object()
    AUTO        = object()
    APPLICATION = object()

class CustomSizePolicy:
    # TODO: Implement this
    RESIZE = object()
    CACHE  = object()

class ResizeStyle:
    """ Options for how to resize rendered images. """
    FIT     = object()
    FILL    = object()
    PADDING = object()
    STRETCH = object()

class Resample:
    """ Options for how to resample resized rendered images. """
    NEAREST  = Image.Resampling.NEAREST
    BILINEAR = Image.Resampling.BILINEAR
    AUTO     = object()

class Compliance:
    """ Enforces compliance with a specification by raising an exception if a configuration option doesn't meet the spec. """
    def FREEDESKTOP(options):
        return (
            options['size_folders'][Size.NORMAL] == 'normal'
            and options['size_folders'][Size.LARGE] == 'large'
            and options['size_folders'][Size.XLARGE] == 'x-large'
            and options['size_folders'][Size.XXLARGE] == 'xx-large'
            and options['resize_style'] in [ResizeStyle.FIT, ResizeStyle.PADDING]
            and options['mask'] == None
            and options['foreground'] == None
            and options['cache_dir'] == CacheDir.FREEDESKTOP
            and options['none_standard_cache_dir'] != FREEDESKTOP
            and options['refresh_policy'] in [RefreshPolicy.FREEDESKTOP, RefreshPolicy.AUTO]
        )

    def FREEDESKTOP_STRICT(options):
        return (
            options['size_folders'][Size.NORMAL] == 'normal'
            and options['size_folders'][Size.LARGE] == 'large'
            and options['size_folders'][Size.XLARGE] == 'x-large'
            and options['size_folders'][Size.XXLARGE] == 'xx-large'
            and options['background'] == (0, 0, 0, 0)
            and options['resize_style'] == ResizeStyle.FIT
            and options['mask'] == None
            and options['foreground'] == None
            and options['cache_dir'] == CacheDir.FREEDESKTOP
            and options['none_standard_cache_dir'] == CacheDir.TEMP
            and options['refresh_policy'] in [RefreshPolicy.FREEDESKTOP, RefreshPolicy.AUTO]
            and options['resample'] == Resample.AUTO
            and options['upcale'] == True
        )

    def NONE(options):
        return True

class Preset:
    
    DEFAULT = {
            'size_folders': {
                    Size.NORMAL: 'normal',
                    Size.LARGE: 'large',
                    Size.XLARGE: 'x-large',
                    Size.XXLARGE: 'xx-large',
                    None: 'custom'
                },
            'renderers': [PillowRenderer, Pdf2ImageRenderer, Html2ImageRenderer],
            'resize_style': ResizeStyle.FIT,
            'mask': None,
            'resample': Resample.AUTO,
            'cache_dir': CacheDir.AUTO,
            'appname': None,
            'appauthor': None,
            'upscale': True,
            'background': (0, 0, 0, 0),
            'foreground': None,
            'compliance': Compliance.NONE,
            'refresh_policy': RefreshPolicy.AUTO,
            'non_standard_cache_dir': CacheDir.AUTO
        }

class ThumbnailManager:

    def __init__(self, preset=Preset.DEFAULT, **options):

        #TODO: implement 'shared' thumbnails part of the Freedesktop spec

        self._options = preset.copy()
        self._options.update(options)

        if type(self._options['renderers'][0]) == type:
            self._options['renderers'] = [x() for x in self._options['renderers']]

        if type(self._options['cache_dir']) == str:
            self._options['cache_dir'] = Path(self.cache_dir)

        if type(self._options['non_standard_cache_dir']) == str:
            self._options['non_standard_cache_dir'] = Path(self._options['non_standard_cache_dir'])

        self._tempdir = tempfile.TemporaryDirectory()

        if RefreshPolicy._takes_args(self._options['refresh_policy']):
            self._options['refresh_policy'] = self._options['refresh_policy']()
        
        if not self._options['compliance'](self._options):
            raise ComplianceError('Options do not meet specified compliance spec.')
    
    def __del__(self):
        self._tempdir.cleanup()

    def get_thumbnail(self, uri, size=Size.NORMAL):
        if len(urlparse(uri).scheme) <= 1:
            uri = Path(uri).resolve().as_uri()
        
        save_path = self._thumbnail_path(uri, size)
        
        if save_path.exists() and not self.RefreshPolicy(save_path, uri):
            return save_path
        
        return self._create_thumbnail(uri, size, save_path)
    
    def _create_thumbnail(self, uri, size, save_path):

        save_path.parent.mkdir(parents=True)

        renderpath = self._render_thumbnail(uri, size)

        if renderpath is None:
            return None
        
        image = Image.open(renderpath)
        image = image.convert('RGBA')
        image = self._resize_image(image, size, self._options['resize_style'])

        background = self._create_ground(self._options['background'], image.size, size)
        image = self._apply_layer(background, image)

        if self._options['foreground']:
            foreground = self._create_ground(self._options['foreground'], image.size, size)
            image = self._apply_layer(image, foreground)

        if self._options['mask']:
            image = self._apply_mask(image, Image.open(self._options['mask']))

        metadata = self._thumbnail_metadata(uri)

        image.save(save_path, 'png', pnginfo=metadata)
        
        return save_path
    
    def _render_thumbnail(self, uri, size):
        temppath = Path(self._tempdir.name) / '~image.png'
        success = False
        parsed = urlparse(uri)

        for renderer in self._options['renderers']:
            if renderer.is_supported(uri):
                if parsed.scheme == 'file' and hasattr(renderer, 'from_file') and renderer.from_file(Path(parsed.path), size, temppath):
                    success = True
                    break
                elif hasattr(renderer, 'from_url') and renderer.from_url(uri, size, temppath):
                    success = True
                    break

        if success:
            return temppath
        else:
            return None
    
    def _apply_layer(self, image1, image2):
        pos = (
            int((image1.size[0] - image2.size[0]) / 2),
            int((image1.size[1] - image2.size[1]) / 2)
        )
        image1.alpha_composite(image2, pos)
        return image1
    
    def _create_ground(self, ground, image_size, desired_size):
        if self._options['resize_style'] == ResizeStyle.FIT:
            bg_size = image.size
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

        resample = self._options['resample']

        if resample == Resample.AUTO:
            if max(image.size) < 128 and self._options['upscale']:
                resample = Resample.NEAREST
            else:
                resample = Resample.BILINEAR

        if not self._options['upscale'] and (image_size[0] > desired_size[0] or image_size[1] > desired_size[1]):
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
    
    def _thumbnail_path(self, uri, size):
        md5 = hashlib.md5()
        md5.update(uri.encode('ascii'))
        thumbdir = self._thumbnail_cache_dir(uri, size)

        if size in freedesktop_sizes:
            return thumbdir / self._options['size_folders'][size] / f'{md5.hexdigest()}.png'
        else:
            return thumbdir / self._options['size_folders'][None] / f'({size[0]}x{size[1]}){md5.hexdigest()}.png'

    def _thumbnail_cache_dir(self, uri, size):

        non_standard = size not in freedesktop_sizes or urlparse(uri).scheme != 'file'

        if non_standard:
            if self._options['non_standard_cache_dir'] == CacheDir.AUTO:
                if self._options['cache_dir'] == CacheDir.FREEDESKTOP:
                    if self._options['appname'] and self._options['appauthor']:
                        return user_cache_dir(appname, appauthor) / 'thumbnails'
                    else:
                        warnings.warn('appname and appauthor not set, using temporary directory for non_standard_cache_dir.')
                        return Path(self._tempdir.name)
            elif self._options['non_standard_cache_dir'] == CacheDir.TEMP:
                return Path(self._tempdir.name)
            else:
                return self._options['non_standard_cache_dir']
        
        if self._options['cache_dir'] == CacheDir.AUTO:
            if self._options['appname'] and self._options['appauthor']:
                return user_cache_dir(appname, appauthor) / 'thumbnails'
            else:
                warnings.warn('appname and appauthor not set, using temporary directory for cache_dir.')
                return Path(self._tempdir.name)
        elif self._options['cache_dir'] == CacheDir.TEMP:
            return Path(self._tempdir.name)
        else:
            return self._options['cache_dir']

    def save_fail(self, uri):
        pass