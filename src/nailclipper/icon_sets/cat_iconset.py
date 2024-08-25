from pathlib import Path
import shutil
import itertools

balmy_file_icons_dir = Path(__file__).parents[2] / 'resources/balmy-file-icons'

class CategoryIconSet:

    categories = {'spreadsheet': ['.ods', '.xls', '.xlt', '.xlw', '.xlr', '.xlsx', '.xlsm', '.xlsb', '.xltx', '.xltm', '.csv', '.tsv', '.ics', '.vcf'], 'model': ['.3ds', '.f3d', '.3mf', '.smt', '.stp', '.step', '.stl', '.obj', '.gcode', '.scad'], 'text': ['.txt', '.md'], 'document': ['.doc', '.dot', '.docx', '.docm', '.dotx', '.dotm', '.ebook', '.log', '.msg', '.odt', '.org', '.pages', '.pdf', '.rtf', '.rst', '.tex', '.txt', '.wpd', '.wps', '.mobi', '.epub', '.azw1', '.azw3', '.azw4', '.azw6', '.azw', '.cbr', '.cbz', '.xps'], 'image': ['.3dm', '.3ds', '.max', '.avif', '.bmp', '.dds', '.gif', '.heic', '.heif', '.jpg', '.jpeg', '.jxl', '.png', '.psd', '.xcf', '.tga', '.thm', '.tif', '.tiff', '.ai', '.eps', '.ps', '.svg', '.dwg', '.dxf', '.gpx', '.kml', '.kmz', '.webp'], 'presentation': ['.ppt', '.pptx', '.odp', '.pptx', '.pptm', '.potx', '.potm', '.ppsx', '.ppsm'], 'archive': ['.7z', '.a', '.aar', '.apk', '.ar', '.bz2', '.br', '.cab', '.cpio', '.deb', '.dmg', '.egg', '.gz', '.iso', '.jar', '.lha', '.lz', '.lz4', '.lzma', '.lzo', '.mar', '.pea', '.rar', '.rpm', '.s7z', '.shar', '.tar', '.tbz2', '.tgz', '.tlz', '.txz', '.war', '.whl', '.xpi', '.zip', '.zipx', '.zst', '.xz', '.pak'], 'audio': ['.aac', '.aiff', '.ape', '.au', '.flac', '.gsm', '.it', '.m3u', '.m4a', '.mid', '.mod', '.mp3', '.mpa', '.ogg', '.pls', '.ra', '.s3m', '.sid', '.wav', '.wma', '.xm'], 'video': ['.3g2', '.3gp', '.aaf', '.asf', '.avchd', '.avi', '.car', '.dav', '.drc', '.flv', '.m2v', '.m2ts', '.m4p', '.m4v', '.mkv', '.mng', '.mov', '.mp2', '.mp4', '.mpe', '.mpeg', '.mpg', '.mpv', '.mts', '.mxf', '.nsv', '.ogv', '.ogm', '.ogx', '.qt', '.rm', '.rmvb', '.roq', '.srt', '.svi', '.vob', '.webm', '.wmv', '.xba', '.yuv'], 'font': ['.eot', '.otf', '.ttf', '.woff', '.woff2'], 'executable': ['.exe', '.msi', '.bin', '.app', '.dmg'], 'script': ['.bat', '.bash', '.csh', '.fish', '.zsh', '.ksh', '.sh'], 'code': ['.1.ada', '.2.ada', '.ada', '.adb', '.ads', '.asm', '.asp', '.aspx', '.bas', '.c++', '.c', '.cbl', '.cc', '.class', '.clj', '.cob', '.cpp', '.cs', '.cxx', '.d', '.diff', '.dll', '.e', '.el', '.f', '.f77', '.f90', '.for', '.fth', '.ftn', '.go', '.groovy', '.h', '.hh', '.hpp', '.hs', '.htm', '.html', '.hxx', '.inc', '.java', '.js', '.json', '.jsp', '.jsx', '.kt', '.kts', '.lhs', '.lisp', '.lua', '.m', '.m4', '.nim', '.patch', '.php', '.php3', '.php4', '.php5', '.phtml', '.pl', '.po', '.pp', '.prql', '.py', '.ps1', '.psd1', '.psm1', '.ps1xml', '.psc1', '.pssc', '.psrc', '.r', '.rb', '.rs', '.s', '.scala', '.sql', '.swg', '.swift', '.v', '.vb', '.vcxproj', '.wll', '.xcodeproj', '.xml', '.xll', '.zig'], 'shortcut': ['.url', '.lnk', '.desktop', '.webloc']}

    def __init__(self, category_map={
        'shortcut': balmy_file_icons_dir / 'shortcut.png',
        'document': balmy_file_icons_dir / 'document.png',
        'video': balmy_file_icons_dir / 'video.png',
        'text': balmy_file_icons_dir / 'text.png',
        'spreadsheet': balmy_file_icons_dir / 'spreadsheet.png',
        'executable': balmy_file_icons_dir / 'executable.png',
        'presentation': balmy_file_icons_dir / 'presentation.png',
        'photo': balmy_file_icons_dir / 'photo.png',
        'code': balmy_file_icons_dir / 'code.png',
        'audio': balmy_file_icons_dir / 'audio.png',
        'font': balmy_file_icons_dir / 'font.png',
        'script': balmy_file_icons_dir / 'font.png',
        'model': balmy_file_icons_dir / 'model.png',
        None: balmy_file_icons_dir / 'blank.png'}):
        self.category_map = category_map

    def is_supported(self, uri):
        if None in self.category_map:
            return True
        else:
            return Path(uri).suffix in list(itertools.chain.from_iterable(self.categories.values()))

    def from_url(self, url, size, save_path):
        return self.from_file(url, size, save_path)

    def from_file(self, file, size, save_path):
        ext = Path(file).suffix
        if ext in self.category_map:
            shutil.copy(self.category_map[ext], save_path)
            return True
        elif None in self.category_map:
            shutil.copy(self.category_map[None], save_path)
            return True
        else:
            return False
