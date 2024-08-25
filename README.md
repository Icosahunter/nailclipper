# Nailclipper

<p align="center">
    <img src="src/resources/nailclipper.png" width="150">
</p>

Nailclipper is a Python module for managing thumbnails (or possibly other image or file caches). Nailclipper includes the capability to be compliant with the [Freedesktop Thumbnail Specification](https://specifications.freedesktop.org/thumbnail-spec/thumbnail-spec-latest.html) if that is what you want, but it is also highly configurable.

# Status

Nailclipper is currently in development and is not ready for use. Once a release is finished, it will be available on [PyPi](https://pypi.org/)

# Use

There are a two main parts to Nailclipper, the ThumbnailGenerator (which contains configuration for how to render/resize/etc the thumbnails) and the ThumbnailManager (which contains configuration for how to store and retrieve cached thumbnails).

The ThumbnailManager can create different styles of thumbnails (by using different ThumbnailGenerators) and store them in different folders (relative to the cache_dir). You give a name for each of these styles and then use that name when calling the get_thumbnail method. The default name when getting a thumbnail is a `None` value, so you can use this if you don't need different types of thumbnails. Here is an example to clarify:

```python
    from nailclipper import ThumbnailGenerator, ThumbnailManager, ResizeStyle

    small_tg = ThumbnailGenerator(size = (64, 64), resize_style = ResizeStyle.FILL, mask='rounded_square.png')
    normal_tg = ThumbnailGenerator(size = (128, 128), resize_style = ResizeStyle.FILL, mask='rounded_square.png')
    preview_tg = ThumbnailGenerator(size = (1024, 1024), resize_style = ResizeStyle.FIT, upscale = True)

    tm = ThumbnailManager(
        cache_dir = './cache',
        cache_folders = {
            'small': 'thumbnails/small',
            'normal': 'thumbnails/normal',
            'preview': 'previews'
        },
        thumbnail_generators = {
            'small': small_tg,
            'normal': normal_tg,
            'preview': preview_tg
        }
    )

    preview_path = tm.get_thumbnail('my_file.pdf', 'preview')       # get the large unstyled preview image
    small_thumbnail_path = tm.get_thumbnail('my_file.pdf', 'small') # get the small styled thumbnail image
    large_thumbnail_path = tm.get_thumbnail('my_file.pdf', 'large') # get the large styled thumbnail image
```

## ThumbnailManager options:

`appname`: The name of your application. Used with `cache_dir=CacheDir.AUTO`.

`appauthor`: The author of your application. Used with `cache_dir=CacheDir.AUTO`.

`cache_dir`: Can be one of the special CacheDir options or a string or pathlike object. This is the directory where thumbnails will be stored.
- `CacheDir.FREEDESKTOP`: The thumbnail directory as specified by the Freedesktop Thumbnail Specification.
- `CacheDir.TEMP`: Uses a temporary directory that is deleted when the thumbnail manager is deleted.
- `CacheDir.AUTO`: If the appname and appauthor options are set, this puts the thumbnails is the correct cache directory for your application. Otherwise this is the same as CacheDir.TEMP.

`refresh_policy`: Specifies when thumbnails should be updated.
- `RefreshPolicy.FREEDESKTOP`: The Freedesktop Thumbnail Specification thumbnail update algorithm. This uses the file size and last modified time of the file to determine when it needs to be updated.
- `RefreshPolicy.INTERVAL`: Update the thumbnail if it is older than a certain time in days. The default is 10 days, you can specify a different time by calling INTERVAL as a method and passing it desired time in days.
- `RefreshPolicy.AUTO`: Uses `RefreshPolicy.FREEDESKTOP` for files and `RefreshPolicy.INTERVAL` for web content.
- `RefreshPolicy.NEVER`: Never update the thumbnail once it's been generated.

`compliance`: Performs a check to see if the options comply with a certain specification:
- `Compliance.FREEDESKTOP`: The Freedesktop Thumbnail Specification
- `Compliance.FREEDESKTOP_STRICT`: Like FREEDESKTOP but slightly more opinionated and requiring certain optional suggestions from the specification.
- `Compliance.NONE`: Do not perform a check

## ThumbnailGenerator options:

`background`: The background for the thumbnail. This can be a color tuple `(R, G, B, A)` or a path to an image. If an image it will be resized with ResizeStyle.FILL to the final size of the thumbnail. Even if you use ResizeStyle.FIT this can still have use as it will show through for images with transparent parts.

`foreground`: An overlay to put on top of the thumbnail. This can be `None` (doesn't apply a foreground), or a color tuple `(R, G, B, A)` or a path to an image. If an image it will be resized with ResizeStyle.FILL to the final size of the thumbnail.

`mask`: The path to a mask image to apply to the thumbnails. The mask will be scaled with ResizeStyle.STRETCH to the thumbnail size, so it is suggested to supply the mask as the largest size you intend to generate the (masked) thumbnails at. You probably want to use `resize_style=ResizeStyle.FILL` if you are using a mask.

`upscale`: If `true` images are upscaled if the requested thumbnai size is actually larger than the source image.

`resize_style`: Specifies how rendered images are resized to the requested thumbnail size.
- `ResizeStyle.FIT`: Scale the image so it fits within the thumbnail size. The resulting image will have the same aspect ratio as the original.
- `ResizeStyle.FILL`: Scale the image so it completely fills the thumbnail size, thus the image will be cropped if it is a different aspect ratio then the requested size.
- `ResizeStyle.PADDING`: Same as `ResizeStyle.FIT` except the thumbnail is then padded with transparent pixels so it is exactly the requested size.
- `ResizeStyle.STRETCH`: Stretch the image to fit the requested size.

`resample`: How images are resampled during resizing.
- `Resample.NEAREST`: Nearest neighbor resampling, this has no antialiazing.
- `Resample.BILINEAR`: A antialiased resampling.
- `Resample.AUTO`: Uses `Resample.NEAREST` when upscaling very small images and `Resample.BILINEAR` the rest of the time.