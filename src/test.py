from nailclipper import *
import os
import platform

tm = ThumbnailManager(
    thumbnail_generators = {None: ThumbnailGenerator(
        mask = './resources/mask.png',
        resize_style = ResizeStyle.FILL,
        
    )}
)

path = tm.get_thumbnail('./resources/apples.jpg')
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
