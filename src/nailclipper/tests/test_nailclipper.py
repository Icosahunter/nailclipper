import unittest as ut
from nailclipper import ThumbnailManager, ThumbnailGenerator
from nailclipper.enums import *
from nailclipper.renderers import IconSet
from pathlib import Path
from tempfile import TemporaryDirectory
import tomllib
import os
import shutil
import itertools
import math
import sys
from hashlib import md5
from PIL import Image

class ThumbnailManagerTestCase(ut.TestCase):

    def configure(self,
                  thumbnail_manager=ThumbnailManager(),
                  test_files_dir=Path(__file__).parent / 'resources',
                  test_file_globs=['red.*', 'green.*', 'blue.*'],
                  test_cache_dir=Path('./cache/thumbnails/')):
        self.tm = thumbnail_manager
        self.test_files_dir = test_files_dir
        self.test_file_globs = test_file_globs
        self.test_cache_dir = test_cache_dir
        self.configured = True

    def setUp(self):

        if not hasattr(self, 'configured'):
            self.configure()

        self.tempdir = TemporaryDirectory()
        self.test_dir = Path(self.tempdir.name)
        self.generated_thumbnails = []
        shutil.copytree(self.test_files_dir, self.test_dir, dirs_exist_ok=True)
        self.test_files = list(itertools.chain(*(self.test_dir.glob(x) for x in self.test_file_globs)))
        os.chdir(self.test_dir)
        self.addCleanup(self.tempdir.cleanup)
        self.addCleanup(lambda : (file.unlink() for file in self.generated_thumbnails if self.test_cache_dir in file.parents))

    def test_thumbnail_creation(self):
        for file in self.test_files:
            thumbnail = self.tm.get_thumbnail(file)
            self.generated_thumbnails.append(thumbnail)
            self.assertTrue(thumbnail, f'Thumbnail creation for {file} failed.')
            self.assertTrue(thumbnail.exists(), f'Thumbnail file {thumbnail} for {file} does not exist.')
            self.assertIn(self.test_cache_dir, thumbnail.parents, f'Thumbnail for {file} was put in the wrong cache directory.')
            expected_color = None
            if file.stem == 'red':
                expected_color = (255,0,0,255)
            elif file.stem == 'green':
                expected_color = (0,255,0,255)
            elif file.stem == 'blue':
                expected_color = (0,0,255,255)
            actual_color = None
            with Image.open(thumbnail) as im:
                actual_color = im.getcolors()
            if actual_color:
                actual_color = actual_color[0][1]
            color_distance = math.dist(expected_color, actual_color)
            self.assertLess(color_distance, 3, f'Thumbnail for {file} does not match source image.')

    def test_thumbnail_refresh(self):
        file_1 = self.test_dir / 'red.jpg'
        file_2 = self.test_dir / 'green.jpg'

        thumbnail = self.tm.get_thumbnail(file_1)
        mtime_1 = os.stat(thumbnail).st_mtime
        color_1 = None
        with Image.open(thumbnail) as im:
            color_1 = im.getcolors()

        thumbnail = self.tm.get_thumbnail(file_2)
        mtime_2 = os.stat(thumbnail).st_mtime
        color_2 = None
        with Image.open(thumbnail) as im:
            color_2 = im.getcolors()

        thumbnail = self.tm.get_thumbnail(file_1)
        mtime_3 = os.stat(thumbnail).st_mtime
        color_3 = None
        with Image.open(thumbnail) as im:
            color_3 = im.getcolors()

        shutil.copy(file_2, file_1)
        thumbnail = self.tm.get_thumbnail(file_1)
        mtime_4 = os.stat(thumbnail).st_mtime
        color_4 = None
        with Image.open(thumbnail) as im:
            color_4 = im.getcolors()

        self.assertEqual(mtime_1, mtime_3, 'New thumbnail was created with no change in source file.')
        self.assertEqual(color_1, color_3, 'Thumbnails do not match with no change in source file.')
        self.assertGreater(mtime_4, mtime_1, 'New thumbnail was NOT created when source file changed.')
        self.assertEqual(color_2, color_4, 'New thumbnail after altered source file does not match the altered file.')

    def test_thumbnail_sizes(self):
        file = self.test_files[0]
        thumbnail = self.tm.get_thumbnail(file)
        self.generated_thumbnails.append(thumbnail)
        self.assertEqual(thumbnail.parent, self.test_cache_dir, f'Thumbnail of size {Size.NORMAL} was put in the wrong directory.')
        im_size = None
        with Image.open(thumbnail) as im:
            im_size = im.size
        self.assertEqual(max(im_size), Size.NORMAL[0], f'Thumbnail size does not match requested size.')

class FreedesktopThumbnailManagerTestCase(ThumbnailManagerTestCase):

    def setUp(self):
        appname = ThumbnailManager.__module__.split('.')[0]
        appver = None
        with open(Path(__file__).parents[3] / 'pyproject.toml', 'rb') as f:
            appver = tomllib.load(f)['project']['version']
        self.configure(thumbnail_manager=ThumbnailManager.freedesktop_thumbnail_manager(appname, appver), test_cache_dir=CacheDir.FREEDESKTOP)
        super().setUp()

    def test_thumbnail_sizes(self):
        file = self.test_files[0]
        for dir, size in [('normal', Size.NORMAL), ('large', Size.LARGE), ('x-large', Size.XLARGE), ('xx-large', Size.XXLARGE)]:
            thumbnail = self.tm.get_thumbnail(file, size)
            self.generated_thumbnails.append(thumbnail)
            self.assertEqual(thumbnail.parent, self.test_cache_dir / dir, f'Thumbnail of size "{dir}" {size} was put in the wrong directory.')
            im_size = None
            with Image.open(thumbnail) as im:
                im_size = im.size
            self.assertEqual(max(im_size), size[0], f'Thumbnail size does not match requested size.')

class ImageThumbnailManagerTestCase(ThumbnailManagerTestCase):
    def setUp(self):
        self.configure(thumbnail_manager=ThumbnailManager.image_thumbnail_manager(), test_file_globs=['red.jpg', 'green.jpg', 'blue.jpg', 'red.png', 'green.png', 'blue.png'])
        super().setUp()

class SimpleThumbnailManagerTestCase(ThumbnailManagerTestCase):
    def setUp(self):
        self.configure(thumbnail_manager=ThumbnailManager.simple_thumbnail_manager())
        super().setUp()

class IconThumbnailManagerTestCase(ThumbnailManagerTestCase):
    def setUp(self):
        self.configure(thumbnail_manager=ThumbnailManager.icon_thumbnail_manager(), test_file_globs=['red.jpg', 'green.jpg', 'blue.jpg', 'script.sh'])
        super().setUp()

    def test_thumbnail_creation(self):
        for file in self.test_files:
            thumbnail = self.tm.get_thumbnail(file)
            self.generated_thumbnails.append(thumbnail)
            self.assertTrue(thumbnail, f'Thumbnail creation for {file} failed.')
            self.assertTrue(thumbnail.exists(), f'Thumbnail file {thumbnail} for {file} does not exist.')
            self.assertIn(self.test_cache_dir, thumbnail.parents, f'Thumbnail for {file} was put in the wrong cache directory.')
            if file.name in ['red', 'green', 'blue']:
                expected_color = None
                if file.stem == 'red':
                    expected_color = (255,0,0,255)
                elif file.stem == 'green':
                    expected_color = (0,255,0,255)
                elif file.stem == 'blue':
                    expected_color = (0,0,255,255)
                actual_color = None
                with Image.open(thumbnail) as im:
                    actual_color = im.getcolors()
                if actual_color:
                    actual_color = actual_color[0][1]
                color_distance = math.dist(expected_color, actual_color)
                self.assertLess(color_distance, 3, f'Thumbnail for {file} does not match source image.')
            else:
                icon_hash = ''
                with open(IconSet.default_icons['script'], 'rb') as f:
                    icon_hash = md5().update(f.read())
                thumbnail_hash = ''
                with open(thumbnail, 'rb') as f:
                    thumbnail_hash = md5().update(f.read())
                self.assertEqual(thumbnail_hash, icon_hash)

#class ThumbnailRenderersTest(ThumbnailManagerTestCaseBase):
#    pass

class ThumbnailGeneratorTestCase(ut.TestCase):

    def setUp(self):
        self.test_files_dir=Path(__file__).parent / 'resources'
        self.tempdir = TemporaryDirectory()
        self.test_dir = Path(self.tempdir.name)
        self.cache_dir = self.test_dir / 'thumbnails'
        self.generated_thumbnails = []
        shutil.copytree(self.test_files_dir, self.test_dir, dirs_exist_ok=True)
        os.chdir(self.test_dir)
        self.addCleanup(self.tempdir.cleanup)

    def test_resize_style(self):

        tg = ThumbnailGenerator(size=(256, 256), resize_style=ResizeStyle.FILL)
        thumbnail = tg.create_thumbnail(self.test_dir / 'resize.png', self.cache_dir / 'resize_fill.jpg')
        self.generated_thumbnails.append(thumbnail)
        with Image.open(thumbnail) as im:
            self.assertEqual(im.getpixel((127, 0)), (255, 0, 0, 255), 'Top color of FILL resize thumbnail not as expected.')
            self.assertEqual(im.getpixel((127, 127)), (255, 0, 0, 255), 'Middle color of FILL resize thumbnail not as expected.')
            self.assertEqual(im.getpixel((127, 255)), (255, 0, 0, 255), 'Bottom color of FILL resize thumbnail not as expected.')
            self.assertEqual(im.getpixel((0, 127)), (255, 0, 0, 255), 'Left color of FILL resize thumbnail not as expected.')
            self.assertEqual(im.getpixel((255, 127)), (255, 0, 0, 255), 'Right color of FILL resize thumbnail not as expected.')
            self.assertEqual(im.size, (256, 256), 'FILL resize thumbnail size not as expected.')

        tg.resize_style = ResizeStyle.FIT
        thumbnail = tg.create_thumbnail(self.test_dir / 'resize.png', self.cache_dir / 'resize_fit.jpg')
        self.generated_thumbnails.append(thumbnail)
        with Image.open(thumbnail) as im:
            self.assertEqual(im.getpixel((43, 0)), (0, 0, 255, 255), 'Top color of FIT resize thumbnail not as expected.')
            self.assertEqual(im.getpixel((43, 127)), (255, 0, 0, 255), 'Middle color of FIT resize thumbnail not as expected.')
            self.assertEqual(im.getpixel((43, 255)), (0, 0, 255, 255), 'Bottom color of FIT resize thumbnail not as expected.')
            self.assertEqual(im.getpixel((0, 127)), (255, 0, 0, 255), 'Left color of FIT resize thumbnail not as expected.')
            self.assertEqual(im.getpixel((84, 127)), (255, 0, 0, 255), 'Right color of FIT resize thumbnail not as expected.')
            self.assertEqual(im.size, (85, 256), 'FIT resize thumbnail size not as expected.')

        tg.resize_style = ResizeStyle.PADDING
        thumbnail = tg.create_thumbnail(self.test_dir / 'resize.png', self.cache_dir / 'resize_padding.jpg')
        self.generated_thumbnails.append(thumbnail)
        with Image.open(thumbnail) as im:
            self.assertEqual(im.getpixel((127, 0)), (0, 0, 255, 255), 'Top color of PADDING resize thumbnail not as expected.')
            self.assertEqual(im.getpixel((127, 127)), (255, 0, 0, 255), 'Middle color of PADDING resize thumbnail not as expected.')
            self.assertEqual(im.getpixel((127, 255)), (0, 0, 255, 255), 'Bottom color of PADDING resize thumbnail not as expected.')
            self.assertEqual(im.getpixel((0, 127)), (0, 0, 0, 0), 'Left color of PADDING resize thumbnail not as expected.')
            self.assertEqual(im.getpixel((255, 127)), (0, 0, 0, 0), 'Right color of PADDING resize thumbnail not as expected.')
            self.assertEqual(im.size, (256, 256), 'PADDING resize thumbnail size not as expected.')

        tg.resize_style = ResizeStyle.STRETCH
        thumbnail = tg.create_thumbnail(self.test_dir / 'resize.png', self.cache_dir / 'resize_stretch.jpg')
        self.generated_thumbnails.append(thumbnail)
        with Image.open(thumbnail) as im:
            self.assertEqual(im.getpixel((127, 0)), (0, 0, 255, 255), 'Top color of STRETCH resize thumbnail not as expected.')
            self.assertEqual(im.getpixel((127, 127)), (255, 0, 0, 255), 'Middle color of STRETCH resize thumbnail not as expected.')
            self.assertEqual(im.getpixel((127, 255)), (0, 0, 255, 255), 'Bottom color of STRETCH resize thumbnail not as expected.')
            self.assertEqual(im.getpixel((0, 127)), (255, 0, 0, 255), 'Left color of STRETCH resize thumbnail not as expected.')
            self.assertEqual(im.getpixel((255, 127)), (255, 0, 0, 255), 'Right color of STRETCH resize thumbnail not as expected.')
            self.assertEqual(im.size, (256, 256), 'STRETCH resize thumbnail size not as expected.')

    def test_mask(self):
         tg = ThumbnailGenerator(size=(256, 256), mask=self.test_dir / 'mask.png')
         thumbnail = tg.create_thumbnail(self.test_dir / 'red_bg.png', self.cache_dir / 'test_mask.jpg')
         self.generated_thumbnails.append(thumbnail)
         with Image.open(thumbnail) as im:
             self.assertEqual(im.getpixel((127, 0)), (0, 0, 0, 0), 'Top color of mask test thumbnail not as expected.')
             self.assertEqual(im.getpixel((127, 127)), (255, 0, 0, 255), 'Middle color of mask test resize thumbnail not as expected.')
             self.assertEqual(im.getpixel((127, 255)), (0, 0, 0, 0), 'Bottom color of mask test resize thumbnail not as expected.')
             self.assertEqual(im.getpixel((0, 127)), (0, 0, 0, 0), 'Left color of mask test resize thumbnail not as expected.')
             self.assertEqual(im.getpixel((255, 127)), (0, 0, 0, 0), 'Right color of mask test resize thumbnail not as expected.')

    def test_resample(self):
        tg = ThumbnailGenerator(size=(128, 128), resample=Resample.AUTO)
        thumbnail = tg.create_thumbnail(self.test_dir / 'pixel_art.png', self.cache_dir / 'test_resample.jpg')
        self.generated_thumbnails.append(thumbnail)
        with Image.open(thumbnail) as im:
            self.assertEqual(im.getpixel((0, 0)), (0, 0, 0, 255), 'Color of top left corner of first square in pixel_art thumbnail not as expected.')
            self.assertEqual(im.getpixel((7, 7)), (0, 0, 0, 255), 'Color of bottom left corner of first square in pixel_art thumbnail not as expected.')
            self.assertEqual(im.getpixel((8, 0)), (255, 255, 255, 255), 'Color of top left corner of second square in pixel_art thumbnail not as expected.')
            self.assertEqual(im.getpixel((15, 7)), (255, 255, 255, 255), 'Color of bottom left corner of second square in pixel_art thumbnail not as expected.')

    def test_upscale(self):
        tg = ThumbnailGenerator(size=(128, 128), upscale=False)
        thumbnail = tg.create_thumbnail(self.test_dir / 'pixel_art.png', self.cache_dir / 'test_upscale.jpg')
        self.generated_thumbnails.append(thumbnail)
        with Image.open(thumbnail) as im:
            self.assertEqual(im.size, (16, 16), 'No upscale test thumbnail size not as expected.')

        tg = ThumbnailGenerator(size=(128, 128), upscale=True)
        thumbnail = tg.create_thumbnail(self.test_dir / 'pixel_art.png', self.cache_dir / 'test_upscale.jpg')
        self.generated_thumbnails.append(thumbnail)
        with Image.open(thumbnail) as im:
            self.assertEqual(im.size, (128, 128), 'Upscale test thumbnail size not as expected.')

    def test_color_background(self):
        tg = ThumbnailGenerator(size=(256, 256), background=(255, 0, 0))
        thumbnail = tg.create_thumbnail(self.test_dir / 'blue_fg.png', self.cache_dir / 'test_color_bg.jpg')
        self.generated_thumbnails.append(thumbnail)
        with Image.open(thumbnail) as im:
            self.assertEqual(im.getpixel((0, 0)), (255, 0, 0, 255), 'Color of top left corner of test color background thumbnail not as expected.')
            self.assertEqual(im.getpixel((0, 255)), (0, 0, 255, 255), 'Color of bottom left corner of test color background thumbnail not as expected.')
            self.assertEqual(im.getpixel((255, 0)), (0, 0, 255, 255), 'Color of top right corner of test color background thumbnail not as expected.')
            self.assertEqual(im.getpixel((255, 255)), (255, 0, 0, 255), 'Color of bottom right corner of test color background thumbnail not as expected.')

    def test_background_foreground(self):
        tg = ThumbnailGenerator(size=(256, 256), background='red_bg.png', foreground='blue_fg.png')
        thumbnail = tg.create_thumbnail(self.test_dir / 'green_mg.png', self.cache_dir / 'test_bg_fg.jpg')
        self.generated_thumbnails.append(thumbnail)
        with Image.open(thumbnail) as im:
            self.assertEqual(im.getpixel((0, 0)), (0, 255, 0, 255), 'Color of top left corner of test color background thumbnail not as expected.')
            self.assertEqual(im.getpixel((0, 255)), (0, 0, 255, 255), 'Color of bottom left corner of test color background thumbnail not as expected.')
            self.assertEqual(im.getpixel((255, 0)), (0, 0, 255, 255), 'Color of top right corner of test color background thumbnail not as expected.')
            self.assertEqual(im.getpixel((255, 255)), (255, 0, 0, 255), 'Color of bottom right corner of test color background thumbnail not as expected.')

    def test_size(self):
        tg = ThumbnailGenerator(size=(64, 64), resize_style=ResizeStyle.FILL)
        thumbnail = tg.create_thumbnail(self.test_dir / 'red.jpg', self.cache_dir / 'test_size_64x64.jpg')
        self.generated_thumbnails.append(thumbnail)
        with Image.open(thumbnail) as im:
            self.assertEqual(im.size, (64, 64), '64x64 test size thumbnail size not as expected.')

        tg = ThumbnailGenerator(size=(816, 816), resize_style=ResizeStyle.FILL)
        thumbnail = tg.create_thumbnail(self.test_dir / 'red.jpg', self.cache_dir / 'test_size_816x816.jpg')
        self.generated_thumbnails.append(thumbnail)
        with Image.open(thumbnail) as im:
            self.assertEqual(im.size, (816, 816), '816x816 test size thumbnail size not as expected.')

        tg = ThumbnailGenerator(size=(2048, 2048), resize_style=ResizeStyle.FILL)
        thumbnail = tg.create_thumbnail(self.test_dir / 'red.jpg', self.cache_dir / 'test_size_2048x2048.jpg')
        self.generated_thumbnails.append(thumbnail)
        with Image.open(thumbnail) as im:
            self.assertEqual(im.size, (2048, 2048), '2048x2048 test size thumbnail size not as expected.')

        tg = ThumbnailGenerator(size=(256, 1024), resize_style=ResizeStyle.FILL)
        thumbnail = tg.create_thumbnail(self.test_dir / 'red.jpg', self.cache_dir / 'test_size_256x1024.jpg')
        self.generated_thumbnails.append(thumbnail)
        with Image.open(thumbnail) as im:
            self.assertEqual(im.size, (256, 1024), '256x1024 test size thumbnail size not as expected.')

        tg = ThumbnailGenerator(size=(1024, 256), resize_style=ResizeStyle.FILL)
        thumbnail = tg.create_thumbnail(self.test_dir / 'red.jpg', self.cache_dir / 'test_size_1024x256.jpg')
        self.generated_thumbnails.append(thumbnail)
        with Image.open(thumbnail) as im:
            self.assertEqual(im.size, (1024, 256), '1024x256 test size thumbnail size not as expected.')

def print_suite(suite):
    if hasattr(suite, '__iter__'):
        for x in suite:
            print_suite(x)
    else:
        print(suite)

if __name__ == '__main__':
    test_case = sys.argv[1] if len(sys.argv) > 1 else None
    ut.main(defaultTest=test_case)
