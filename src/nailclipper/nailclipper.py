from urllib.parse import urlparse
from pathlib import Path
from platformdirs import user_cache_dir
from nailclipper.renderers.pillow import PillowRenderer
from PIL import Image
from PIL.PngImagePlugin import PngInfo

import os
import time
import platform
import hashlib
import tempfile
import mimetypes

class Size:
    NORMAL  = (128 , 128 )
    LARGE   = (256 , 256 )
    XLARGE  = (512 , 512 )
    XXLARGE = (1024, 1024)

standard_sizes = [Size.NORMAL, Size.LARGE, Size.XLARGE, Size.XXLARGE]

class RefreshPolicy:

    @classmethod
    def _takes_args(self, val):
        return val in [self.INTERVAL]

    @staticmethod
    def FREEDESKTOP(thumbnail_path, file_uri):
        if urlparse(file_uri).scheme != 'file':
            return False
        image = Image.open(thumbnail_path)
        file_mtime = os.stat(file_path).st_mtime
        file_size = os.path.getsize(file_path)
        return ((not self.options['is_shared'] and not 'Thumb::MTime' in image.text) 
            or ('Thumb::MTime' in image.text and file_mtime != image.text['Thumb::MTime']) 
            or ('Thumb::Size' in image.text and file_size != image.text['Thumb::Size']))
    
    @staticmethod
    def INTERVAL(days=10):
        def interval_check(thumbnail_path, file_uri):
            thumb_mtime = os.stat(thumbnail_path).st_mtime
            return (time.time() - thumb_mtime) >= (days*24*60*60)
        return interval_check
    
    @staticmethod
    def AUTO(thumbnail_path, file_uri):
        if urlparse(file_uri).scheme == 'file':
            return RefreshPolicy.FREEDESKTOP(thumbnail_path, file_uri)
        else:
            return RefreshPolicy.INTERVAL(days=30)(thumbnail_path, file_uri)

    @staticmethod
    def NEVER(thumbnail_path, file_uri):
        return False

def _get_xdg_home():
    if platform.system() == 'Windows':
        return Path(os.path.expandvars('%LOCALAPPDATA%')) / 'cache/thumbnails'
    elif os.environ.get('XDG_CACHE_HOME', None):
        return Path(os.environ.get('XDG_CACHE_HOME')) / 'thumbnails'
    else:
        return Path.home() / '.cache/thumbnails'

class CacheDir:
    FREEDESKTOP = _get_xdg_home()
    NAILCLIPPER = Path(user_cache_dir('nailclipper', 'Icosahunter')) / 'thumbnails'
    TEMP        = object()
    AUTO        = object()

class CustomSizePolicy:
    RESIZE = object()
    CACHE  = object()

class ResizeStyle:
    FIT     = object()
    FILL    = object()
    PADDING = object()
    STRETCH = object()

class Resample:
    NEAREST  = Image.Resampling.NEAREST
    BILINEAR = Image.Resampling.BILINEAR
    AUTO     = object()

class ThumbnailManager:

    def __init__(self, **options):
        self.size_folders = options.get('size_folders',
                {
                    Size.NORMAL: 'normal',
                    Size.LARGE: 'large',
                    Size.XLARGE: 'x-large',
                    Size.XXLARGE: 'xx-large',
                    None: 'custom'
                })
        
        self.renderers = options.get('renderers', [PillowRenderer])
        #self.is_shared = options.get('is_shared', False) #TODO: implement this part of the Freedesktop spec

        self.resize_style = options.get('resize_style', ResizeStyle.FIT)
        self.mask = options.get('mask', None)
        self.resample = options.get('resample', Resample.AUTO)
        self.cache_dir = options.get('cache_dir', CacheDir.AUTO)
        self.appname = options.get('appname', None)
        self.appauthor = options.get('appauthor', None)
        self.upscale = True

        if type(self.cache_dir) == str:
            self.cache_dir = Path(self.cache_dir)

        self.non_standard_cache_dir = options.get('non_standard_cache_dir', CacheDir.AUTO)
        if type(self.non_standard_cache_dir) == str:
            self.non_standard_cache_dir = Path(self.non_standard_cache_dir)

        self._tempdir = tempfile.TemporaryDirectory()

        self.refresh_policy = options.get('refresh_policy', RefreshPolicy.FREEDESKTOP)

        if RefreshPolicy._takes_args(self.refresh_policy):
            self.refresh_policy = self.refresh_policy()
    
    def __del__(self):
        self._tempdir.cleanup()

    def get_thumbnail(self, uri, size=Size.NORMAL):
        if len(urlparse(uri).scheme) <= 1:
            uri = Path(uri).resolve().as_uri()
        
        save_path = self._thumbnail_path(uri, size)
        
        if save_path.exists() and not self.RefreshPolicy(save_path, uri):
            return save_path
        
        generate_size = size
        if size not in standard_sizes and self.custom_size_policy == CustomSizePolicy.RESIZE:
            try:
                generate_size = [x for x in standard_sizes if x[0] > size[0] and x[1] > size[1]][0]
            except IndexError:
                generate_size = Size.XXLARGE
        
        return self._create_thumbnail(uri, size, save_path)

    def _create_thumbnail(self, uri, size, save_path):
        
        parsed = urlparse(uri)
        temppath = Path(self._tempdir.name) / '~image'
        success = False

        save_path.parent.mkdir(parents=True)

        for renderer in self.renderers:
            if parsed.scheme == 'file' and hasattr(renderer, 'from_file') and renderer.from_file(Path(parsed.path), size, temppath):
                success = True
                break
            elif hasattr(renderer, 'from_url') and renderer.from_url(uri, size, temppath):
                success = True
                break

        if not success:
            return None
        
        image = Image.open(temppath)

        image = image.convert('RGBA')

        resample = self.resample

        if resample == Resample.AUTO:
            if max(image.size) < 128 and self.upscale:
                resample = Resample.NEAREST
            else:
                resample = Resample.BILINEAR

        if self.resize_style == ResizeStyle.STRETCH:
            image = image.resize(size, resample=resample)
        elif self.resize_style == ResizeStyle.FILL:
            image = image.resize(self._image_fill_size(image.size, size), resample=resample)
            image = image.crop((0, 0, *size))
        else:
            if self.upscale:
                image = image.resize(self._image_fit_size(image.size, size), resample=resample)
            else:
                image.thumbnail(size, resample=resample)
        
        if self.resize_style == ResizeStyle.PADDING:
            pos = (
                int((size[0] - image.size[0]) / 2),
                int((size[1] - image.size[1]) / 2)
            )
            padded = Image.new(image.mode, size, (0, 0, 0, 0))
            padded.paste(image, pos)
            image = padded

        if self.mask is not None:
            masked = Image.new(image.mode, image.size, (0, 0, 0, 0))
            mask = Image.open(self.mask)
            mask = mask.resize(image.size)
            masked.paste(image, (0, 0), mask=mask)
            image = masked
        
        metadata = self._thumbnail_metadata(uri)

        image.save(save_path, 'png', pnginfo=metadata)
        
        return save_path
    
    def _thumbnail_metadata(self, uri):
        metadata = PngInfo()
        parsed = urlparse(uri)
        if parsed.scheme == 'file':
            path = Path(parsed.path)
            metadata.add_text('Thumb::MTime', str(os.stat(path).st_mtime))
            metadata.add_text('Thumb::MSize', str(os.path.getsize(path)))
        metadata.add_text('Thumb::URI', uri)
        metadata.add_text('Thumb::Mimetype', mimetypes.guess_type(uri)[0])
        return metadata
            
    def _image_fit_size(self, size, desize):
        r1 = size[0] / size[1]
        r2 = desize[0] / desize[1]
        if r1 > r2:
            w = desize[0]
            h = (desize[0]/size[0])*size[1]
        else:
            h = desize[1]
            w = (desize[1]/size[1])*desize[0]
        return (int(w), int(h))
    
    def _image_fill_size(self, size, desize):
        r1 = size[0] / size[1]
        r2 = desize[0] / desize[1]
        if r1 < r2:
            w = desize[0]
            h = (desize[0]/size[0])*size[1]
        else:
            h = desize[1]
            w = (desize[1]/size[1])*desize[0]
        return (int(w), int(h))
    
    def _thumbnail_path(self, uri, size):
        md5 = hashlib.md5()
        md5.update(uri.encode('ascii'))
        thumbdir = self._thumbnail_cache_dir(uri, size)

        if size in standard_sizes:
            return thumbdir / self.size_folders[size] / f'{md5.hexdigest()}.png'
        else:
            return thumbdir / self.size_folders[None] / f'({size[0]}x{size[1]}){md5.hexdigest()}.png'
    
    def _thumbnail_cache_dir(self, uri, size):

        non_standard = size not in standard_sizes or urlparse(uri).scheme != 'file'

        if non_standard:
            if self.non_standard_cache_dir == CacheDir.AUTO:
                if self.cache_dir == CacheDir.FREEDESKTOP:
                    if self.appname and self.appauthor:
                        return user_cache_dir(appname, appauthor)
                    return CacheDir.NAILCLIPPER
            elif self.non_standard_cache_dir == CacheDir.TEMP:
                return Path(self._tempdir.name)
        
        if self.cache_dir == CacheDir.AUTO:
            if self.appname and self.appauthor:
                return user_cache_dir(appname, appauthor)
            return CacheDir.NAILCLIPPER
        elif self.cache_dir == CacheDir.TEMP:
            return Path(self._tempdir.name)
        else:
            return self.cache_dir

    def save_fail(self, uri):
        pass