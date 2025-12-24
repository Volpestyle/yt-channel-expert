class YTChannelExpertError(Exception):
    """Base exception for the package."""

class PackBuildError(YTChannelExpertError):
    pass

class PackReadError(YTChannelExpertError):
    pass

class IngestionError(YTChannelExpertError):
    pass
