import hashlib
import tempfile
from pathlib import Path
from nailclipper.iconset import IconSet
from nailclipper.renderers.html2image import Html2ImageRenderer
from nailclipper.renderers.pdf2image import Pdf2ImageRenderer
from nailclipper.renderers.pillow import PillowRenderer
from nailclipper.thumbnail_generator import ThumbnailGenerator
from nailclipper.enums import *

class ComplianceError(ValueError):
    pass

class ThumbnailManager:

    def __init__(self,
            cache_folders = { None: '.' },
            thumbnail_generators = { None: ThumbnailGenerator() },
            cache_dir = CacheDir.AUTO,
            compliance = Compliance.NONE,
            refresh_policy = RefreshPolicy.AUTO):

        #TODO: implement 'shared' thumbnails part of the Freedesktop spec

        self.cache_folders = cache_folders
        self.thumbnail_generators = thumbnail_generators
        self.cache_dir = cache_dir
        self.compliance = compliance
        self.refresh_policy = refresh_policy

        if type(self.cache_dir) == str:
            self.cache_dir = Path(self.cache_dir)

        self._tempdir = tempfile.TemporaryDirectory()

        if RefreshPolicy._takes_args(self.refresh_policy):
            self.refresh_policy = self.refresh_policy()

        #if not self.compliance(self):
        #    raise ComplianceError(f'Options do not meet specified compliance spec "{self.compliance.__name__}"')

        for tg in set(thumbnail_generators.values()):
            tg.init()

    def __del__(self):
        self._tempdir.cleanup()

    def get_thumbnail(self, uri, style=None):

        uri = str(uri)

        if len(urlparse(uri).scheme) <= 1:
            uri = Path(uri).resolve().as_uri()

        save_path = self._thumbnail_path(uri, style)

        if save_path.exists() and not self.refresh_policy(save_path, uri):
            return save_path

        return self.thumbnail_generators[style].create_thumbnail(uri, save_path)

    def _thumbnail_path(self, uri, style):
        md5 = hashlib.md5()
        md5.update(uri.encode('ascii'))
        return self._thumbnail_cache_dir(uri) / self.cache_folders[style] / f'{md5.hexdigest()}.png'

    def _thumbnail_cache_dir(self, uri):
        if self.cache_dir == CacheDir.AUTO:
                return Path('./cache/thumbnails/')
        elif self.cache_dir == CacheDir.TEMP:
            return Path(self._tempdir.name)
        else:
            return self.cache_dir

    def save_fail(self, uri):
        pass

    @staticmethod
    def image_thumbnail_manager(
        cache_dir,
        size,
        mask = None,
        background = (0, 0, 0, 0),
        foreground = None):
        resize_style = ResizeStyle.FIT
        if mask:
            resize_style = ResizeStyle.FILL
        return ThumbnailManager(
            thumbnail_generators = { None: ThumbnailGenerator(size=size, mask=mask, background=background, foreground=foreground, resize_style=resize_style, renderers=[PillowRenderer]) },
            cache_dir = cache_dir
        )

    @staticmethod
    def simple_thumbnail_manager(
        cache_dir,
        size,
        mask = None,
        background = (0, 0, 0, 0),
        foreground = None):
        resize_style = ResizeStyle.FIT
        if mask:
            resize_style = ResizeStyle.FILL
        return ThumbnailManager(
            thumbnail_generators = { None: ThumbnailGenerator(size=size, mask=mask, background=background, foreground=foreground, resize_style=resize_style) },
            cache_dir = cache_dir
        )

    @staticmethod
    def icon_thumbnail_manager(
        cache_dir,
        size,
        mask = None,
        background = (0, 0, 0, 0),
        foreground = None,
        iconset = IconSet):
        resize_style = ResizeStyle.FIT
        if mask:
            resize_style = ResizeStyle.FILL
        return ThumbnailManager(
            thumbnail_generators = { None: ThumbnailGenerator(size=size, mask=mask, background=background, foreground=foreground, resize_style=resize_style, renderers=[PillowRenderer, Pdf2ImageRenderer, Html2ImageRenderer, iconset]) },
            cache_dir = cache_dir
        )

    @staticmethod
    def freedesktop_thumbnail_manager():
        return ThumbnailManager(
            cache_folders = {
                None: 'normal',
                Size.NORMAL: 'normal',
                Size.LARGE: 'large',
                Size.XLARGE: 'x-large',
                Size.XXLARGE: 'xx-large'
            },
            thumbnail_generators = {
                None: ThumbnailGenerator(),
                Size.NORMAL: ThumbnailGenerator(),
                Size.LARGE: ThumbnailGenerator(size=Size.LARGE),
                Size.XLARGE: ThumbnailGenerator(size=Size.XLARGE),
                Size.XXLARGE: ThumbnailGenerator(size=Size.XXLARGE)
            },
            cache_dir = CacheDir.FREEDESKTOP,
            compliance = Compliance.FREEDESKTOP,
            refresh_policy = RefreshPolicy.FREEDESKTOP
        )
