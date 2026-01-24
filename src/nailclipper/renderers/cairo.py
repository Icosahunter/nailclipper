from warnings import warn
from pathlib  import Path

class CairoRenderer:

    cairo = None

    @staticmethod
    def init():
        try:
            import cairosvg
            CairoRenderer.cairo = cairosvg
        except Exception as e:
            warn(f'Could not load CairoRenderer: {e}')

    @staticmethod
    def is_supported(uri):
        return CairoRenderer.cairo and Path(uri).suffix == '.svg'

    @staticmethod
    def from_file(file, size, save_path):
        try:
            CairoRenderer.cairo.svg2png(url=str(file), write_to=str(save_path))
            return True
        except Exception as e:
            warn(f'Could not generate thumbnail for {file} using CairoRenderer: {e}')
            return False
