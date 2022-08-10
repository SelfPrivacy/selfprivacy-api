from typing import Optional
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel

from selfprivacy_api.dependencies import get_token_header

import selfprivacy_api.actions.system as system_actions

router = APIRouter(
    prefix="/system",
    tags=["system"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/configuration/timezone")
async def get_timezone():
    """Get the timezone of the server"""
    return system_actions.get_timezone()


class ChangeTimezoneRequestBody(BaseModel):
    """Change the timezone of the server"""

    timezone: str


@router.put("/configuration/timezone")
async def change_timezone(timezone: ChangeTimezoneRequestBody):
    """Change the timezone of the server"""
    try:
        system_actions.change_timezone(timezone.timezone)
    except system_actions.InvalidTimezone as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"timezone": timezone.timezone}


@router.get("/configuration/autoUpgrade")
async def get_auto_upgrade_settings():
    """Get the auto-upgrade settings"""
    return system_actions.get_auto_upgrade_settings().dict()


class AutoUpgradeSettings(BaseModel):
    """Settings for auto-upgrading user data"""

    enable: Optional[bool] = None
    allowReboot: Optional[bool] = None


@router.put("/configuration/autoUpgrade")
async def set_auto_upgrade_settings(settings: AutoUpgradeSettings):
    """Set the auto-upgrade settings"""
    system_actions.set_auto_upgrade_settings(settings.enable, settings.allowReboot)
    return "Auto-upgrade settings changed"


@router.get("/configuration/apply")
async def apply_configuration():
    """Apply the configuration"""
    return_code = system_actions.rebuild_system()
    return return_code


@router.get("/configuration/rollback")
async def rollback_configuration():
    """Rollback the configuration"""
    return_code = system_actions.rollback_system()
    return return_code


@router.get("/configuration/upgrade")
async def upgrade_configuration():
    """Upgrade the configuration"""
    return_code = system_actions.upgrade_system()
    return return_code


@router.get("/reboot")
async def reboot_system():
    """Reboot the system"""
    system_actions.reboot_system()
    return "System reboot has started"


@router.get("/version")
async def get_system_version():
    """Get the system version"""
    return {"system_version": system_actions.get_system_version()}


@router.get("/pythonVersion")
async def get_python_version():
    """Get the Python version"""
    return system_actions.get_python_version()


@router.get("/configuration/pull")
async def pull_configuration():
    """Pull the configuration"""
    action_result = system_actions.pull_repository_changes()
    if action_result.status == 0:
        return action_result.dict()
    raise HTTPException(status_code=500, detail=action_result.dict())
