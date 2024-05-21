from nailclipper import *
import os
import platform

tm = ThumbnailManager(
    cache_dir = CacheDir.TEMP,
    resize_style = ResizeStyle.FILL,
    #mask = '../mask.png',
    background = '/home/icosahunter/Documents/test/xenoblade_clip.png'
)

path = tm.get_thumbnail('/home/icosahunter/Documents/tau beta pi/tau beta pi - cinco de mayo/cake-slice.svg')
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

input('Press any key to exit...')