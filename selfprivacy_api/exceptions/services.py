import gettext
import logging

from selfprivacy_api.exceptions import REPORT_IT_TO_SUPPORT_CHATS
from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)

_ = gettext.gettext

logger = logging.getLogger(__name__)


class ServiceNotFoundError(AbstractException):
    code = 404

    def __init__(self, service_id: str, log: bool = True):
        self.service_id = service_id

        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("No such service: %(service_id)s. %(REPORT_IT_TO_SUPPORT_CHATS)s"),
            locale=locale,
        ) % {
            "service_id": self.service_id,
            "REPORT_IT_TO_SUPPORT_CHATS": t.translate(
                text=REPORT_IT_TO_SUPPORT_CHATS, locale=locale
            ),
        }


class LegacySpModulesFlakeError(AbstractException):
    def __init__(self, log: bool = True):
        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "Service modules cannot be changed because legacy service modules "
                "have not been migrated.\n"
                "Legacy service module flake is still present.\n"
                "Restart the SelfPrivacy API service to re-run the migration, then try again.\n"
                "%(REPORT_IT_TO_SUPPORT_CHATS)s"
            ),
            locale=locale,
        ) % {
            "REPORT_IT_TO_SUPPORT_CHATS": t.translate(
                text=REPORT_IT_TO_SUPPORT_CHATS, locale=locale
            ),
        }


class VolumeNotFoundError(AbstractException):
    code = 404

    def __init__(self, volume_name: str, log: bool = True):
        self.volume_name = volume_name

        super().__init__(log=log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("No such volume: %(volume_name)s. %(REPORT_IT_TO_SUPPORT_CHATS)s"),
            locale=locale,
        ) % {
            "volume_name": self.volume_name,
            "REPORT_IT_TO_SUPPORT_CHATS": t.translate(
                text=REPORT_IT_TO_SUPPORT_CHATS, locale=locale
            ),
        }


class MoveNotEnoughSpaceError(AbstractException):
    code = 413

    def __init__(self, target_volume: BlockDevice, log: bool = True):
        self.target_volume = target_volume
        super().__init__(log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        # TODO(nhnn): Maybe print how much space is needed? I'm not sure how to properly translate that, though.
        return t.translate(
            text=_(
                "Not enough space on %(volume_display_name)s, failed to move service."
            ),
            locale=locale,
        ) % {"volume_display_name": self.target_volume.get_display_name()}


class MoveVolumeNotMountedError(AbstractException):
    code = 503

    def __init__(self, target_volume: BlockDevice, log: bool = True):
        self.volume_display_name = target_volume.get_display_name()
        super().__init__(log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Volume %(volume_display_name)s is not mounted."), locale=locale
        ) % {"volume_display_name": self.volume_display_name}


class ServiceNotMovableError(AbstractException):
    code = 400

    def __init__(self, service_name: str, log: bool = True):
        self.service_name = service_name
        super().__init__(log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Service %(service_name)s is not movable."), locale=locale
        ) % {"service_name": self.service_name}


class ServiceIsAlreadyOnVolumeError(AbstractException):
    code = 400

    def __init__(self, service_name: str, target_volume: BlockDevice, log: bool = True):
        self.service_name = service_name
        self.volume_display_name = target_volume.get_display_name()
        super().__init__(log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "Service %(service_name)s is already on volume %(volume_display_name)s."
            ),
            locale=locale,
        ) % {
            "service_name": self.service_name,
            "volume_display_name": self.volume_display_name,
        }


class ServiceHasNothingToMoveError(AbstractException):
    code = 400

    def __init__(self, service_name: str, log: bool = True):
        self.service_name = service_name
        super().__init__(log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "Service %(service_name)s cannot be moved as it has no defined storage location."
            ),
            locale=locale,
        ) % {"service_name": self.service_name}


class ServerDoesNotUseBindsError(AbstractException):
    code = 400

    def __init__(self, service_name: str, log: bool = True):
        self.service_name = service_name
        super().__init__(log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                "Service %(service_name)s cannot be moved as server doesn't use binds."
            ),
            locale=locale,
        ) % {"service_name": self.service_name}


class BindError(AbstractException):
    """Base exception for bind operations."""

    code = 500


class NoSuchDriveError(BindError):
    code = 404

    def __init__(self, drive_name: str, log: bool = True):
        self.drive_name = drive_name
        super().__init__(log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("No such drive: %(drive_name)s"),
            locale=locale,
        ) % {"drive_name": self.drive_name}


class BindDirectoryNotFoundError(BindError):
    def __init__(self, path: str, log: bool = True):
        self.path = path
        super().__init__(log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Directory %(path)s was not found."),
            locale=locale,
        ) % {"path": self.path}


class BindPathNotDirectoryError(BindError):
    def __init__(self, path: str, log: bool = True):
        self.path = path
        super().__init__(log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("%(path)s is not a directory."),
            locale=locale,
        ) % {"path": self.path}


class BindPathNotOwnedError(BindError):
    def __init__(self, path: str, owner: str, log: bool = True):
        self.path = path
        self.owner = owner
        super().__init__(log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("%(path)s is not owned by %(owner)s."),
            locale=locale,
        ) % {"path": self.path, "owner": self.owner}


class BindTargetNotFoundError(BindError):
    def __init__(self, path: str, log: bool = True):
        self.path = path
        super().__init__(log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Cannot bind to a non-existing path: %(path)s"),
            locale=locale,
        ) % {"path": self.path}


class BindOperationFailedError(BindError):
    def __init__(self, source: str, target: str, details: str, log: bool = True):
        self.source = source
        self.target = target
        self.details = details
        super().__init__(log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Unable to bind %(source)s to %(target)s: %(details)s"),
            locale=locale,
        ) % {
            "source": self.source,
            "target": self.target,
            "details": self.details,
        }


class UnbindTargetNotFoundError(BindError):
    def __init__(self, path: str, log: bool = True):
        self.path = path
        super().__init__(log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Cannot unbind a non-existing path: %(path)s"),
            locale=locale,
        ) % {"path": self.path}


class UnbindOperationFailedError(BindError):
    def __init__(self, path: str, details: str, log: bool = True):
        self.path = path
        self.details = details
        super().__init__(log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Unable to unmount folder %(path)s: %(details)s"),
            locale=locale,
        ) % {"path": self.path, "details": self.details}


class BindOwnershipFailedError(BindError):
    def __init__(self, path: str, details: str, log: bool = True):
        self.path = path
        self.details = details
        super().__init__(log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Unable to set ownership of %(path)s: %(details)s"),
            locale=locale,
        ) % {"path": self.path, "details": self.details}


class SystemServiceOperationNotSupportedError(AbstractException):
    code = 400

    def __init__(self, service_name: str, log: bool = True):
        self.service_name = service_name
        super().__init__(log)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_("Operation is not supported for system service %(service_name)s."),
            locale=locale,
        ) % {
            "service_name": self.service_name,
        }
