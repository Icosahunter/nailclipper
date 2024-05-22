from nailclipper import *
import os
import platform

tm = ThumbnailManager(
    resize_style = ResizeStyle.FILL,
    mask = '../mask.png',
    background = (255, 255, 255, 255)
)

path = tm.get_thumbnail('../apples.jpg')
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