class ExitCodeError(Exception):
    """An exception indicating that a process should exit with a specific error code.

    It's common that applications need to signal an exit from somewhere within their
    command-line handling code, and often the most straightforward way to do that is with an
    exception. This exception can be used to signal these kinds of exits.

    Args:
        msg: The text message associated with the exception.
        code: The ExitCode associated with the exception.
    """

    def __init__(self, msg, code):
        super().__init__(msg)
        self.code = code

    def __repr__(self):
        return 'ExitCodeError(msg="{}", code={})'.format(self.args[0], self.code)
