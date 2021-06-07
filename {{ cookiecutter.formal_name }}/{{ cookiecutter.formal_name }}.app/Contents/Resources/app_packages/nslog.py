# Python writes all console output to stdout/stderr. However, in production,
# iOS devices don't record stdout/stderr; only the Apple System Log is preserved.
#
# This handler redirects sys.stdout and sys.stderr to the Apple System Log
# by creating a wrapper around NSLog, and monkeypatching that wrapper over
# sys.stdout and sys.stderr
#
# It also installs a custom exception hook. This is done because there's
# no nice C API to generate the familiar Python traceback. The custom
# hook uses the Python API to generate a traceback, clean it up a little
# to remove details that aren't helpful, and annotate the resulting string
# onto the `sys` module as `sys._traceback`; this can be retrieved by the
# C API and used.

import ctypes
import io
import re
import sys
import traceback

# Name of the UTF-16 encoding with the system byte order.
if sys.byteorder == 'little':
    UTF16_NATIVE = 'utf-16-le'
elif sys.byteorder == 'big':
    UTF16_NATIVE = 'utf-16-be'
else:
    raise AssertionError('Unknown byte order: ' + sys.byteorder)


class CFTypeRef(ctypes.c_void_p):
    pass

CFIndex = ctypes.c_long
UniChar = ctypes.c_uint16

CoreFoundation = ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
Foundation = ctypes.CDLL('/System/Library/Frameworks/Foundation.framework/Foundation')

# void CFRelease(CFTypeRef arg)
CoreFoundation.CFRelease.restype = None
CoreFoundation.CFRelease.argtypes = [CFTypeRef]

# CFStringRef CFStringCreateWithCharacters(CFAllocatorRef alloc, const UniChar *chars, CFIndex numChars)
CoreFoundation.CFStringCreateWithCharacters.restype = CFTypeRef
CoreFoundation.CFStringCreateWithCharacters.argtypes = [CFTypeRef, ctypes.POINTER(UniChar), CFIndex]

# void NSLog(NSString *format, ...)
Foundation.NSLog.restype = None
Foundation.NSLog.argtypes = [CFTypeRef]


def _cfstr(s):
    """Create a ``CFString`` from the given Python :class:`str`."""
    encoded = s.encode(UTF16_NATIVE)
    assert len(encoded) % 2 == 0
    arr = (UniChar * (len(encoded)//2)).from_buffer_copy(encoded)
    cfstring = CoreFoundation.CFStringCreateWithCharacters(None, arr, len(arr))
    assert cfstring is not None
    return cfstring


# Format string for a single object.
FORMAT = _cfstr('%@')


def nslog(s):
    """Log the given Python :class:`str` to the system log."""
    cfstring = _cfstr(s)
    Foundation.NSLog(FORMAT, cfstring)
    CoreFoundation.CFRelease(cfstring)


class NSLogWriter(io.TextIOBase):
    """An output-only text stream that writes to the system log."""
    def write(self, s):
        if not hasattr(self, 'buf'):
            self.buf = s
        else:
            self.buf += s

        lines = self.buf.split('\n')
        for line in lines[:-1]:
            nslog(line)
        self.buf = lines[-1]
        return len(s)

    @property
    def encoding(self):
        return UTF16_NATIVE


# Replace stdout and stderr with a single NSLogWriter
sys.stdout = sys.stderr = NSLogWriter()

# Install a custom exception hook.
def custom_exception_hook(exc_type, value, tb):
    # Drop the top two stack frames; these are internal
    # wrapper logic, and not in the control of the user.
    clean_tb = tb.tb_next.tb_next

    # Print the trimmed stack trace to a string buffer
    buffer = io.StringIO()
    traceback.print_exception(exc_type, value, clean_tb, file=buffer)

    # Also take the opportunity to clean up the source path,
    # so paths only refer to the "app local" path
    clean_traceback = re.sub(
        r'^  File \"/.*/(.*?).app/Contents/Resources/',
        r'  File "\1.app/Contents/Resources/',
        buffer.getvalue(),
        flags=re.MULTILINE,
    )

    # Annotate the clean traceback onto the sys module.
    sys._traceback = clean_traceback

    # Perform the default exception hook behavior
    # with the full original stack trace.
    sys.__excepthook__(exc_type, value, tb)

sys.excepthook = custom_exception_hook
