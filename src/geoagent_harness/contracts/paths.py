from pathlib import PurePosixPath

class TabularError(ValueError):
    pass


def relative_path(value, area):
    if not isinstance(value,str): raise TabularError('File reference must be a string')
    parsed = PurePosixPath(value)
    if area == 'input' and not parsed.is_absolute() and parsed.parts and parsed.parts[0] != 'data':
        # Both a filename and a normalized nested reference resolve below input.
        # Validate the original spelling before prefixing; never normalize traversal.
        if str(parsed) != value or '..' in parsed.parts or value in {'.','..'}:
            raise TabularError('Use a normalized relative path under data/input')
        value = 'data/input/' + value
        parsed = PurePosixPath(value)
    if parsed.is_absolute() or str(parsed) != value or '\\' in value or any(ord(c)<32 for c in value) or '..' in parsed.parts or len(parsed.parts)<3 or parsed.parts[:2] != ('data',area):
        raise TabularError('Use a normalized relative path under data/' + area)
    return value

