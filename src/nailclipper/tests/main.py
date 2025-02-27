import unittest as ut
from nailclipper import ThumbnailManager
from nailclipper.enums import *
from nailclipper.iconset import IconSet
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import shutil
import itertools
import math
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
        self.configure(thumbnail_manager=ThumbnailManager.freedesktop_thumbnail_manager(), test_cache_dir=CacheDir.FREEDESKTOP)
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
        self.configure(thumbnail_manager=ThumbnailManager.simple_thumbnail_manager(), test_file_globs=['red.*', 'green.*', 'blue.*', 'script.sh'])
        super().setUp()

    def test_thumbnail_creation(self):
        for file in self.test_files:
            thumbnail = self.tm.get_thumbnail(file)
            self.generated_thumbnails.append(thumbnail)
            self.assertTrue(thumbnail, f'Thumbnail creation for {file} failed.')
            self.assertTrue(thumbnail.exists(), f'Thumbnail file {thumbnail} for {file} does not exist.')
            self.assertIn(self.test_cache_dir, thumbnail.parents, f'Thumbnail for {file} was put in the wrong cache directory.')
            if file.stem in ['red', 'green', 'blue']:
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
                self.assertEqual(thumbnail, IconSet.default_icons['script'])

#class ThumbnailRenderersTest(ThumbnailManagerTestCaseBase):
#    pass

#class ThumbnailGeneratorTest(ThumbnailManagerTestCaseBase):
#    pass

if __name__ == '__main__':
    ut.main()
