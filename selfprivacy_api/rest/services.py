"""Basic services legacy api"""
import base64
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from selfprivacy_api.actions.ssh import (
    InvalidPublicKey,
    KeyAlreadyExists,
    KeyNotFound,
    create_ssh_key,
    enable_ssh,
    get_ssh_settings,
    remove_ssh_key,
    set_ssh_settings,
)
from selfprivacy_api.actions.users import UserNotFound, get_user_by_username

from selfprivacy_api.dependencies import get_token_header
from selfprivacy_api.restic_controller import ResticController, ResticStates
from selfprivacy_api.restic_controller import tasks as restic_tasks
from selfprivacy_api.services.bitwarden import Bitwarden
from selfprivacy_api.services.gitea import Gitea
from selfprivacy_api.services.mailserver import MailServer
from selfprivacy_api.services.nextcloud import Nextcloud
from selfprivacy_api.services.ocserv import Ocserv
from selfprivacy_api.services.pleroma import Pleroma
from selfprivacy_api.services.service import ServiceStatus
from selfprivacy_api.utils import WriteUserData, get_dkim_key, get_domain

router = APIRouter(
    prefix="/services",
    tags=["services"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


def service_status_to_return_code(status: ServiceStatus):
    """Converts service status object to return code for
    compatibility with legacy api"""
    if status == ServiceStatus.ACTIVE:
        return 0
    elif status == ServiceStatus.FAILED:
        return 1
    elif status == ServiceStatus.INACTIVE:
        return 3
    elif status == ServiceStatus.OFF:
        return 4
    else:
        return 2


@router.get("/status")
async def get_status():
    """Get the status of the services"""
    mail_status = MailServer.get_status()
    bitwarden_status = Bitwarden.get_status()
    gitea_status = Gitea.get_status()
    nextcloud_status = Nextcloud.get_status()
    ocserv_stauts = Ocserv.get_status()
    pleroma_status = Pleroma.get_status()

    return {
        "imap": service_status_to_return_code(mail_status),
        "smtp": service_status_to_return_code(mail_status),
        "http": 0,
        "bitwarden": service_status_to_return_code(bitwarden_status),
        "gitea": service_status_to_return_code(gitea_status),
        "nextcloud": service_status_to_return_code(nextcloud_status),
        "ocserv": service_status_to_return_code(ocserv_stauts),
        "pleroma": service_status_to_return_code(pleroma_status),
    }


@router.post("/bitwarden/enable")
async def enable_bitwarden():
    """Enable Bitwarden"""
    Bitwarden.enable()
    return {
        "status": 0,
        "message": "Bitwarden enabled",
    }


@router.post("/bitwarden/disable")
async def disable_bitwarden():
    """Disable Bitwarden"""
    Bitwarden.disable()
    return {
        "status": 0,
        "message": "Bitwarden disabled",
    }


@router.post("/gitea/enable")
async def enable_gitea():
    """Enable Gitea"""
    Gitea.enable()
    return {
        "status": 0,
        "message": "Gitea enabled",
    }


@router.post("/gitea/disable")
async def disable_gitea():
    """Disable Gitea"""
    Gitea.disable()
    return {
        "status": 0,
        "message": "Gitea disabled",
    }


@router.get("/mailserver/dkim")
async def get_mailserver_dkim():
    """Get the DKIM record for the mailserver"""
    domain = get_domain()

    dkim = get_dkim_key(domain)
    if dkim is None:
        raise HTTPException(status_code=404, detail="DKIM record not found")
    dkim = base64.b64encode(dkim.encode("utf-8")).decode("utf-8")
    return dkim


@router.post("/nextcloud/enable")
async def enable_nextcloud():
    """Enable Nextcloud"""
    Nextcloud.enable()
    return {
        "status": 0,
        "message": "Nextcloud enabled",
    }


@router.post("/nextcloud/disable")
async def disable_nextcloud():
    """Disable Nextcloud"""
    Nextcloud.disable()
    return {
        "status": 0,
        "message": "Nextcloud disabled",
    }


@router.post("/ocserv/enable")
async def enable_ocserv():
    """Enable Ocserv"""
    Ocserv.enable()
    return {
        "status": 0,
        "message": "Ocserv enabled",
    }


@router.post("/ocserv/disable")
async def disable_ocserv():
    """Disable Ocserv"""
    Ocserv.disable()
    return {
        "status": 0,
        "message": "Ocserv disabled",
    }


@router.post("/pleroma/enable")
async def enable_pleroma():
    """Enable Pleroma"""
    Pleroma.enable()
    return {
        "status": 0,
        "message": "Pleroma enabled",
    }


@router.post("/pleroma/disable")
async def disable_pleroma():
    """Disable Pleroma"""
    Pleroma.disable()
    return {
        "status": 0,
        "message": "Pleroma disabled",
    }


@router.get("/restic/backup/list")
async def get_restic_backup_list():
    restic = ResticController()
    return restic.snapshot_list


@router.put("/restic/backup/create")
async def create_restic_backup():
    restic = ResticController()
    if restic.state is ResticStates.NO_KEY:
        raise HTTPException(status_code=400, detail="Backup key not provided")
    if restic.state is ResticStates.INITIALIZING:
        raise HTTPException(status_code=400, detail="Backup is initializing")
    if restic.state is ResticStates.BACKING_UP:
        raise HTTPException(status_code=409, detail="Backup is already running")
    restic_tasks.start_backup()
    return {
        "status": 0,
        "message": "Backup creation has started",
    }


@router.get("/restic/backup/status")
async def get_restic_backup_status():
    restic = ResticController()

    return {
        "status": restic.state.name,
        "progress": restic.progress,
        "error_message": restic.error_message,
    }


@router.get("/restic/backup/reload")
async def reload_restic_backup():
    restic_tasks.load_snapshots()
    return {
        "status": 0,
        "message": "Snapshots reload started",
    }


class BackupRestoreInput(BaseModel):
    backupId: str


@router.put("/restic/backup/restore")
async def restore_restic_backup(backup: BackupRestoreInput):
    restic = ResticController()
    if restic.state is ResticStates.NO_KEY:
        raise HTTPException(status_code=400, detail="Backup key not provided")
    if restic.state is ResticStates.NOT_INITIALIZED:
        raise HTTPException(
            status_code=400, detail="Backups repository is not initialized"
        )
    if restic.state is ResticStates.BACKING_UP:
        raise HTTPException(status_code=409, detail="Backup is already running")
    if restic.state is ResticStates.INITIALIZING:
        raise HTTPException(status_code=400, detail="Repository is initializing")
    if restic.state is ResticStates.RESTORING:
        raise HTTPException(status_code=409, detail="Restore is already running")

    for backup_item in restic.snapshot_list:
        if backup_item["short_id"] == backup.backupId:
            restic_tasks.restore_from_backup(backup.backupId)
            return {
                "status": 0,
                "message": "Backup restoration procedure started",
            }

    raise HTTPException(status_code=404, detail="Backup not found")


class BackblazeConfigInput(BaseModel):
    accountId: str
    accountKey: str
    bucket: str


@router.put("/restic/backblaze/config")
async def set_backblaze_config(backblaze_config: BackblazeConfigInput):
    with WriteUserData() as data:
        if "backblaze" not in data:
            data["backblaze"] = {}
        data["backblaze"]["accountId"] = backblaze_config.accountId
        data["backblaze"]["accountKey"] = backblaze_config.accountKey
        data["backblaze"]["bucket"] = backblaze_config.bucket

    restic_tasks.update_keys_from_userdata()

    return "New Backblaze settings saved"


@router.post("/ssh/enable")
async def rest_enable_ssh():
    """Enable SSH"""
    enable_ssh()
    return {
        "status": 0,
        "message": "SSH enabled",
    }


@router.get("/ssh")
async def rest_get_ssh():
    """Get the SSH configuration"""
    settings = get_ssh_settings()
    return {
        "enable": settings.enable,
        "passwordAuthentication": settings.passwordAuthentication,
    }


class SshConfigInput(BaseModel):
    enable: Optional[bool] = None
    passwordAuthentication: Optional[bool] = None


@router.put("/ssh")
async def rest_set_ssh(ssh_config: SshConfigInput):
    """Set the SSH configuration"""
    set_ssh_settings(ssh_config.enable, ssh_config.passwordAuthentication)

    return "SSH settings changed"


class SshKeyInput(BaseModel):
    public_key: str


@router.put("/ssh/key/send", status_code=201)
async def rest_send_ssh_key(input: SshKeyInput):
    """Send the SSH key"""
    try:
        create_ssh_key("root", input.public_key)
    except KeyAlreadyExists as error:
        raise HTTPException(status_code=409, detail="Key already exists") from error
    except InvalidPublicKey as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid key type. Only ssh-ed25519 and ssh-rsa are supported",
        ) from error

    return {
        "status": 0,
        "message": "SSH key sent",
    }


@router.get("/ssh/keys/{username}")
async def rest_get_ssh_keys(username: str):
    """Get the SSH keys for a user"""
    user = get_user_by_username(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user.ssh_keys


@router.post("/ssh/keys/{username}", status_code=201)
async def rest_add_ssh_key(username: str, input: SshKeyInput):
    try:
        create_ssh_key(username, input.public_key)
    except KeyAlreadyExists as error:
        raise HTTPException(status_code=409, detail="Key already exists") from error
    except InvalidPublicKey as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid key type. Only ssh-ed25519 and ssh-rsa are supported",
        ) from error
    except UserNotFound as error:
        raise HTTPException(status_code=404, detail="User not found") from error

    return {
        "message": "New SSH key successfully written",
    }


@router.delete("/ssh/keys/{username}")
async def rest_delete_ssh_key(username: str, input: SshKeyInput):
    try:
        remove_ssh_key(username, input.public_key)
    except KeyNotFound as error:
        raise HTTPException(status_code=404, detail="Key not found") from error
    except UserNotFound as error:
        raise HTTPException(status_code=404, detail="User not found") from error
    return {"message": "SSH key deleted"}
