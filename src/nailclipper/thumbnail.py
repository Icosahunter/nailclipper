from enum import Enum
from PIL import ExifTags, Image
from PIL.PngImagePlugin import PngInfo
from nailclipper.enums import *

MakernoteMetadataTags = {
    'uri': 0,
    'mtime': 1,
    'size': 2,
    'mimetype': 3
}

PNGInfoKeys = {
    'uri': 'Thumb::URI',
    'mtime': 'Thumb::MTime',
    'size': 'Thumb::Size',
    'mimetype': 'Thumb::Mimetype'
}

class Thumbnail:
    def __init__(self, path, image = None, metadata_format = MetadataFormat.PNG_INFO):
        self.metadata = {}
        self.metadata_format = metadata_format
        self._image = image
        self.path = path

    @property
    def image(self):
        self.load()
        return self._image

    def load(self):
        self._image = Image.open(self.path)
        if self.metadata_format == MetadataFormat.EXIF:
            exif_makernote = self._image.getexif().get_ifd(ExifTags.IFD.MakerNote)
            self.metadata = { [x for x,y in MakernoteMetadataTags.items() if y==k][0]:v for k,v in exif_makernote.items()}
        elif self.metadata_format == MetadataFormat.PNG_INFO:
            self.metadata = { [x for x,y in PNGInfoKeys.items() if y==k][0]:v for k,v in self._image.text.items()}

    def save(self):
        if self.metadata_format == MetadataFormat.EXIF:
            exif_makernote = self._image.getexif().get_ifd(ExifTags.IFD.MakerNote)
            exif_makernote.update({MakernoteMetadataTags[k]:v for k, v in self.metadata.items()})
            self._image.save(self.path)
        elif self.metadata_format == MetadataFormat.PNG_INFO:
            png_info = PngInfo()
            for k,v in self.metadata.items():
                png_info.add_text(PNGInfoKeys[k], v)
            self._image.save(self.path, pnginfo=png_info)
