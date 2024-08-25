from nailclipper import *
import os
import platform

def test_thumbnail_manager(tm, file, test_name):
    print(f'--- BEGIN {test_name} ---')
    path = tm.get_thumbnail(file)
    print(f'Test thumbnail created at: "{path}"')
    if path and os.path.exists(path):
        if platform.system() == 'Windows':
            os.startfile(path)
        elif platform.system() == 'Linux':
            os.system(f'xdg-open "{path}"')
        elif platform.system() == 'Darwin':
            os.system(f'open "{path}"')
    else:
        print('Thumbnail creation failed!')
    print(f'--- END {test_name} ---\n\n')

simple_tm = ThumbnailManager.simple_thumbnail_manager(
        cache_dir=CacheDir.TEMP,
        size=Size.NORMAL
)

simple_tm_wm = ThumbnailManager.simple_thumbnail_manager(
        cache_dir=CacheDir.TEMP,
        size=Size.NORMAL,
        mask='./resources/test/mask.png'
)

icon_tm = ThumbnailManager.icon_thumbnail_manager(
        cache_dir=CacheDir.TEMP,
        size=Size.NORMAL
)

test_thumbnail_manager(simple_tm, './resources/test/apples.jpg', 'Simple TM JPG Test')
test_thumbnail_manager(simple_tm, './resources/test/hello-world.pdf', 'Simple TM PDF Test')
test_thumbnail_manager(simple_tm_wm, './resources/test/apples.jpg', 'Simple TM With Mask JPG Test')
test_thumbnail_manager(icon_tm, './resources/test/apples.jpg', 'Icon TM JPG Test')
test_thumbnail_manager(icon_tm, './resources/test/unrecognized-extension.qwerty', 'Icon TM Blank Test')
test_thumbnail_manager(icon_tm, './resources/test/hello-world.sh', 'Icon TM Script Test')

input('Press any key to exit...')
