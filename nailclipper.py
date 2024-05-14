from enum import Enum
from urllib.parse import urlparse
from pathlib import Path
from appdirs import user_cache_dir
from thumbnail_providers.pillow import PillowThumbnailProvider
from PIL import Image
import os

class Size(Enum):
    NORMAL  = (128 , 128 )
    LARGE   = (256 , 256 )
    XLARGE  = (512 , 512 )
    XXLARGE = (1024, 1024)

class Nailclipper:

    def __init__(self, **options):
        self.options = {
            'size_folders': {
                NORMAL: 'normal',
                LARGE: 'large',
                XLARGE: 'x-large',
                XXLARGE: 'xx-large'
            }
            'providers': [PillowThumbnailProvider],
            'is_shared': False,
            'appname': 'Nailclipper',
            'appauthor': 'Default',
            'linux_integrate': True,
            'freedesktop_compliant': True,
            'cache_dir': None
        }
        self.options.update(options)
        if options['linux_integrate']:
            self.options['cache_dir'] = self.get_xdg_thumbnail_cache_dir()
        else:
            self.options['cache_dir'] = Path(user_cache_dir(self.options['appname'], self.options['appauthor']))
    
    def get_thumbnail(self, uri, size):
        path = Path(uri)
        is_url = urlparse(uri).scheme != ''
        save_path = cache_dir / 
        for provider in self.options['providers']:
            if is_url and provider.hasattr('from_url') and provider.from_url(uri, size, save_path):
                return save_path
            elif path.suffix in provider.supported and provider.from_file(path, size, save_path):
                return save_path

    def save_fail(self, uri):
        pass

    def is_cached(self, path):
        pass

    def is_expired(self, thumbnail_path, file_path)
        image = Image.open(thumbnail_path)
        file_mtime = os.stat(file_path).st_mtime
        file_size = os.path.getsize(file_path)
        return (not self.options['is_shared'] and not 'Thumb::MTime' in image.text)
            or ('Thumb::MTime' in image.text and file_mtime != image.text['Thumb::MTime'])
            or ('Thumb::Size' in image.text and file_size != image.text['Thumb::Size'])

    def get_xdg_thumbnail_cache_dir(self):
        path = os.environ.get('$XDG_CACHE_HOME', None)
        if path is None:
            path = Path(os.environ['$HOME']) / '.cache/thumbnails'
        else:
            path = Path(path) / 'thumbnails'
        return path