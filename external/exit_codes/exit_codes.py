try:
    from enum import IntEnum as Base
except ImportError:
    Base = object


class ExitCode(Base):
    """Exit status codes.

    Note:
        If the Enum library is available (Python 3.4+) or backports to
        earlier versions, ExitCodes will be an IntEnum, otherwise
        ExitCodes will be a regular class with integer class attributes.

    These mimic those on many Unixes (and provided by `os`) but make them
    available on all platforms.

        OK           Successful termination
        USAGE        Command-line usage error
        DATA_ERR     Invalid data
        NO_INPUT     No input provided
        NO_USER      User unknown
        NO_HOST      Hostname unknown
        UNAVAILABLE  Service unavailable
        SOFTWARE     Internal software error
        OS_ERR       System error (e.g., can't fork)
        OS_FILE      File missing
        CANT_CREATE  Can't create (user) output file
        IO_ERR       Input/output error
        TEMP_FAIL    A temporary failure; the user is invited to retry
        PROTOCOL     A protocol error
        NO_PERM      Permission denied
        CONFIG       Configuration error

    In addition, aliases with similar names to those provided by the
    `os` module are provided to ease porting, but they have short and
    less readable names.

    """

    """Successful termination"""
    OK = 0

    """Command-line usage error"""
    USAGE = 64

    """Invalid data"""
    DATA_ERR = 65

    """No input provided"""
    NO_INPUT = 66

    """User unknown"""
    NO_USER = 67

    """Hostname unknown"""
    NO_HOST = 68

    """Service unavailable"""
    UNAVAILABLE = 69

    """Internal software error"""
    SOFTWARE = 70

    """System error (e.g., can't fork)"""
    OS_ERR = 71

    """File missing"""
    OS_FILE = 72

    """Can't create (user) output file"""
    CANT_CREATE = 73

    """Input/output error"""
    IO_ERR = 74

    """A temporary failure; the user is invited to retry"""
    TEMP_FAIL = 75

    """A protocol error"""
    PROTOCOL = 76

    """Permission denied"""
    NO_PERM = 77

    """Configuration error"""
    CONFIG = 78

    # Aliases which have the same name as those in the standard
    # library os module, without the leading EX_. These are to
    # allow for easier porting as EX_FOO may be globally replaced
    # with ExitCode.FOO.  For new code, prefer the easier to read
    # names above.

    DATAERR = DATA_ERR
    NOINPUT = NO_INPUT
    NOUSER = NO_USER
    NOHOST = NO_HOST
    OSERR = OS_ERR
    OSFILE = OS_FILE
    CANTCREAT = CANT_CREATE
    IOERR = IO_ERR
    TEMPFAIL = TEMP_FAIL
    NOPERM = NO_PERM
