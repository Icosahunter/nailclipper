# Nailclipper

Nailclipper is a Python module for managing thumbnails (or possibly other image or file caches). Nailclipper includes the capability to be compliant with the Freedesktop Thumbnail Specification if that is what you want, but it is also highly configurable.

# Status

Nailclipper is currently in development and is not ready for use. Once a release is finished, it will be available on [PyPi](https://pypi.org/)

# Use

Nailclipper is very easy to use. Simply create a thumbnail manager, with options describing how and where you want thumbnails to be created. Then, get thumbnails by calling the get_thumbnail method.

```
    import nailclipper as nc

    tm = nc.ThumbnailManager(
        cache_dir = nc.CacheDir.TEMP,
        resize_style = nc.ResizeStyle.FILL,
        refresh_policy = nc.RefreshPolicy.INTERVAL,
        mask = 'mask.png'
    )

    thumbnail_path = tm.get_thumbnail('myfile.jpg')
```

The ThumbnailManager has a lot of different options for configuration:

`appname`: The name of your application. Used with `cache_dir=CacheDir.AUTO`.

`appauthor`: The author of your application. Used with `cache_dir=CacheDir.AUTO`.

`mask`: The path to a mask image to apply to the thumbnails. The mask will be scaled to the requested thumbnail sizes, so it is suggested to supply the mask as a 1024x1024 (XXLARGE) size. You probably want to use `resize_style=ResizeStyle.FILL` if you are using a mask.

`upscale`: If `true` images are upscaled if the requested thumbnai size is actually larger than the source image.


`cache_dir`: Can be one of the special CacheDir options or a string or pathlike object. This is the directory where thumbnails will be stored.
- `CacheDir.FREEDESKTOP`: The thumbnail directory as specified by the Freedesktop Thumbnail Specification.
- `CacheDir.NAILCLIPPER`: Uses a directory for a 'nailclipper' app in the default application cache directory.
- `CacheDir.TEMP`: Uses a temporary directory that is deleted when the thumbnail manager is deleted.
- `CacheDir.AUTO`: If the appname and appauthor options are set, this puts the thumbnails is the correct cache directory for your application. Otherwise this is the same as CacheDir.NAILCLIPPER.

`non_standard_cache_dir`: In case you want to use non-freedesktop-compliant features, but only sometimes, this puts the non-compliant thumbnails in a different directory.
- `CacheDir.FREEDESKTOP`: While you could use this value for this option... you really shouldn't.
- `CacheDir.NAILCLIPPER`: Uses a directory for a 'nailclipper' app in the default application cache directory.
- `CacheDir.TEMP`: Uses a temporary directory that is deleted when the thumbnail manager is deleted.
- `CacheDir.AUTO`: If cache_dir is FREEDESKTOP, will act the same as CacheDir.AUTO for cache_dir, otherwise it will simply be the same as cache_dir.

`refresh_policy`: Specifies when thumbnails should be updated.
- `RefreshPolicy.FREEDESKTOP`: The Freedesktop Thumbnail Specification thumbnail update algorithm. This uses the file size and last modified time of the file to determine when it needs to be updated.
- `RefreshPolicy.INTERVAL`: Update the thumbnail if it is older than a certain time in days. The default is 10 days, you can specify a different time by calling INTERVAL as a method and passing it desired time in days.
- `RefreshPolicy.AUTO`: Uses `RefreshPolicy.FREEDESKTOP` for files and `RefreshPolicy.INTERVAL` for web content.
- `RefreshPolicy.NEVER`: Never update the thumbnail once it's been generated.

`resize_style`: Specifies how rendered images are resized to the requested thumbnail size.
- `ResizeStyle.FIT`: Scale the image so it fits within the thumbnail size. The resulting image will have the same aspect ratio as the original.
- `ResizeStyle.FILL`: Scale the image so it completely fills the thumbnail size, thus the image will be cropped if it is a different aspect ratio then the requested size.
- `ResizeStyle.PADDING`: Same as `ResizeStyle.FIT` except the thumbnail is then padded with transparent pixels so it is exactly the requested size.
- `ResizeStyle.STRETCH`: Stretch the image to fit the requested size.

`resample`: How images are resampled during resizing.
- `Resample.NEAREST`: Nearest neighbor resampling, this has no antialiazing.
- `Resample.BILINEAR`: A antialiased resampling.
- `Resample.AUTO`: Uses `Resample.NEAREST` when upscaling very small images and `Resample.BILINEAR` the rest of the time.