from pydantic import BaseModel


class OwnedPath(BaseModel):
    """
    A convenient interface for explicitly defining ownership of service folders.
    One overrides Service.get_owned_paths() for this.

    Why this exists?:
    One could use Bind to define ownership but then one would need to handle drive which
    is unnecessary and produces code duplication.

    It is also somewhat semantically wrong to include Owned Path into Bind
    instead of user and group. Because owner and group in Bind are applied to
    the original folder on the drive, not to the binding path. But maybe it is
    ok since they are technically both owned. Idk yet.
    """

    path: str
    owner: str
    group: str
