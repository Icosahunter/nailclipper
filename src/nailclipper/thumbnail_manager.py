import os
import hashlib
import tempfile
import mimetypes
from warnings import warn
from pathlib import Path
from urllib.parse import urlparse, unquote

from platformdirs import user_cache_dir
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from nailclipper.thumbnail_generator import ThumbnailGenerator
from nailclipper.enums import *

class ComplianceError(ValueError):
    pass

class ThumbnailManager:

    def __init__(self,
            cache_folders = { None: '.' },
            thumbnail_generators = { None: ThumbnailGenerator() },
            cache_dir = CacheDir.AUTO,
            appname = None,
            appauthor = None,
            compliance = Compliance.NONE,
            refresh_policy = RefreshPolicy.AUTO):

        #TODO: implement 'shared' thumbnails part of the Freedesktop spec

        self.cache_folders = cache_folders
        self.thumbnail_generators = thumbnail_generators
        self.cache_dir = cache_dir
        self.appname = appname
        self.appauthor = appauthor
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
        if len(urlparse(uri).scheme) <= 1:
            uri = Path(uri).resolve().as_uri()
        
        save_path = self._thumbnail_path(uri, style)
        
        if save_path.exists() and not self.RefreshPolicy(save_path, uri):
            return save_path
        
        return self.thumbnail_generators[style].create_thumbnail(uri, save_path)
    
    def _thumbnail_path(self, uri, style):
        md5 = hashlib.md5()
        md5.update(uri.encode('ascii'))
        return self._thumbnail_cache_dir(uri) / self.cache_folders[style] / f'{md5.hexdigest()}.png'

    def _thumbnail_cache_dir(self, uri):
        
        if self.cache_dir == CacheDir.AUTO:
            if self.appname and self.appauthor:
                return user_cache_dir(appname, appauthor) / 'thumbnails'
            else:
                warn('appname and appauthor not set, using temporary directory for cache_dir.')
                return Path(self._tempdir.name)
        elif self.cache_dir == CacheDir.TEMP:
            return Path(self._tempdir.name)
        else:
            return self.cache_dir

    def save_fail(self, uri):
        pass