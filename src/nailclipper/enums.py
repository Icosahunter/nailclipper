import os
import time
from pathlib import Path
from urllib.parse import urlparse, unquote
import platform
import re

from PIL import Image

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
        file_mtime = str(os.stat(file_path).st_mtime)
        file_size = str(os.path.getsize(file_path))
        return ((not 'Thumb::MTime' in image.text) # When implementing shared cache, add 'and not thumbnail_manager.is_shared' check somehow
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
    @staticmethod
    def FREEDESKTOP(tm):
        return (
            tm.cache_folders[Size.NORMAL] == 'normal'
            and tm.cache_folders[Size.LARGE] == 'large'
            and tm.cache_folders[Size.XLARGE] == 'x-large'
            and tm.cache_folders[Size.XXLARGE] == 'xx-large'
            and tm.cache_dir == CacheDir.FREEDESKTOP
            and re.match(r'fail\/.+-.+', tm.fail_folder)
            and tm.refresh_policy in [RefreshPolicy.FREEDESKTOP, RefreshPolicy.AUTO]
            and all((
                tg.resize_style in [ResizeStyle.FIT, ResizeStyle.PADDING]
                and tg.mask == None
                and tg.foreground == None
                for tg in tm.thumbnail_generators.values()
            ))
        )

    @staticmethod
    def FREEDESKTOP_STRICT(tm):
        return (
            tm.cache_folders[Size.NORMAL] == 'normal'
            and tm.cache_folders[Size.LARGE] == 'large'
            and tm.cache_folders[Size.XLARGE] == 'x-large'
            and tm.cache_folders[Size.XXLARGE] == 'xx-large'
            and tm.cache_dir == CacheDir.FREEDESKTOP
            and re.match(r'fail\/.+-.+', tm.fail_folder)
            and tm.refresh_policy in [RefreshPolicy.FREEDESKTOP, RefreshPolicy.AUTO]
            and all((
                tg.background == (0, 0, 0, 0)
                and tg.resize_style == ResizeStyle.FIT
                and tg.mask == None
                and tg.foreground == None
                and tg.resample == Resample.AUTO
                and tg.upscale == True
                for tg in tm.thumbnail_generators.values()
            ))

        )

    @staticmethod
    def NONE(options):
        return True
