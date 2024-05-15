from enum import Enum
from urllib.parse import urlparse
from pathlib import Path
from platformdirs import user_cache_dir
from thumbnail_providers.pillow import PillowThumbnailProvider
from PIL import Image
import os
import time
import platform
import hashlib
import tempfile

class Size(Enum):
    NORMAL  = (128 , 128 )
    LARGE   = (256 , 256 )
    XLARGE  = (512 , 512 )
    XXLARGE = (1024, 1024)

class RefreshPolicy():

    _takes_args = ['INTERVAL']

    @staticmethod
    def FREEDESKTOP(thumbnail_path, file_uri):
        if urlparse(file_uri).scheme != 'file':
            return False
        image = Image.open(thumbnail_path)
        file_mtime = os.stat(file_path).st_mtime
        file_size = os.path.getsize(file_path)
        return (not self.options['is_shared'] and not 'Thumb::MTime' in image.text)
            or ('Thumb::MTime' in image.text and file_mtime != image.text['Thumb::MTime'])
            or ('Thumb::Size' in image.text and file_size != image.text['Thumb::Size'])
    
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
        return Path.Home() / '.cache/thumbnails'

class CacheDir(Enum):
    FREEDESKTOP = _get_xdg_home()
    NAILCLIPPER = user_cache_dir('nailclipper', 'Nathaniel Markham') / 'thumbnails'
    TEMP        = object()
    AUTO        = object()

class CustomSizePolicy(Enum):
    RESIZE = 'resize'
    CACHE = 'cache'

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
        self.providers = options.get('providers', [PillowThumbnailProvider])
        #self.is_shared = options.get('is_shared', False) #TODO: implement this part of the Freedesktop spec
        self.cache_dir = Path(options.get('cache_dir', CacheDir.NAILCLIPPER))
        self.refresh_policy = options.get('refresh_policy', RefreshPolicy.FREEDESKTOP)
        self.non_standard_cache_dir = Path(options.get('non_standard_cache_dir', CacheDir.AUTO))
        self._tempdir = tempfile.TemporaryDirectory()

        if self.refresh_policy.__name__ in RefreshPolicy._takes_args:
            self.refresh_policy = self.refresh_policy()
    
    def __del__(self):
        self._tempdir.cleanup()

    def get_thumbnail(self, uri, size):
        if len(urlparse(uri).scheme) <= 1:
            uri = Path(uri).resolve().as_uri()
        
        save_path = self._thumbnail_path(uri, size)
        
        if save_path.exists() and not self.RefreshPolicy(save_path, uri):
            return save_path
        
        return self._create_thumbnail(uri, size, save_path)

    def _create_thumbnail(self, uri, size, save_path):

        generate_size = size
        if size not in Size and self.custom_size_policy == CustomSizePolicy.RESIZE:
            try:
                generate_size = [x for x in Size if x[0] > size[0] and x[1] > size[1]][0]
            except IndexError:
                generate_size = Size.XXLARGE
        
        parsed = urlparse(uri)
        
        for provider in self.providers:
            if parsed.scheme == 'file'
                and provider.hasattr('from_file')
                and provider.from_file(Path(parsed.path), generate_size, save_path):
                return save_path
            elif provider.hasattr('from_url')
                and provider.from_url(uri, generate_size, save_path):
                return save_path
    
    def _thumbnail_path(self, uri, size):
        md5 = hashlib.md5()
        md5.update(uri)
        thumbdir = self._thumbnail_cache_dir(size)
        if size not in Size:
            return thumbdir / f'({size[0]}x{size[1]}){md5.hexdigest()}.png'
        else:
            return thumbdir / f'{md5.hexdigest()}.png'
    
    def _thumbnail_cache_dir(self, size):

        if size not in Size:
            if self.non_standard_cache_dir == CacheDir.AUTO:
                if self.cache_dir == CacheDir.FREEDESKTOP:
                    return CachDir.NAILCLIPPER
            elif self.non_standard_cache_dir == CacheDir.TEMP:
                return self._tempdir.name
        
        if self.cache_dir == CacheDir.AUTO:
            return CacheDir.NAILCLIPPER
        elif self.cache_dir == CacheDir.TEMP:
            return self._tempdir.name
        else:
            return self.cache_dir

    def save_fail(self, uri):
        pass