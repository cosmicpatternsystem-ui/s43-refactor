class TemporaryPause(Exception):
    def __init__(self, message="", pause_sec=None):
        super().__init__(message)
        self.pause_sec = pause_sec