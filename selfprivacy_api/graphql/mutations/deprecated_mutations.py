"""Deprecated mutations

There was made a mistake, where mutations were not grouped, and were instead
placed in the root of mutations schema. In this file, we import all the
mutations from and provide them to the root for backwards compatibility.
"""

import strawberry
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.user import UserMutationReturn
from selfprivacy_api.graphql.mutations.api_mutations import (
    ApiKeyMutationReturn,
    ApiMutations,
    DeviceApiTokenMutationReturn,
)
from selfprivacy_api.graphql.mutations.job_mutations import JobMutations
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericJobMutationReturn,
    GenericMutationReturn,
)
from selfprivacy_api.graphql.mutations.services_mutations import (
    ServiceJobMutationReturn,
    ServiceMutationReturn,
    ServicesMutations,
)
from selfprivacy_api.graphql.mutations.storage_mutations import StorageMutations
from selfprivacy_api.graphql.mutations.system_mutations import (
    AutoUpgradeSettingsMutationReturn,
    SystemMutations,
    TimezoneMutationReturn,
)
from selfprivacy_api.graphql.mutations.users_mutations import UsersMutations


def deprecated_mutation(func, group, auth=True):
    return strawberry.mutation(
        resolver=func,
        permission_classes=[IsAuthenticated] if auth else [],
        deprecation_reason=f"Use `{group}.{func.__name__}` instead",
    )


@strawberry.type
class DeprecatedApiMutations:
    get_new_recovery_api_key: ApiKeyMutationReturn = deprecated_mutation(
        ApiMutations.get_new_recovery_api_key,
        "api",
    )

    use_recovery_api_key: DeviceApiTokenMutationReturn = deprecated_mutation(
        ApiMutations.use_recovery_api_key,
        "api",
        auth=False,
    )

    refresh_device_api_token: DeviceApiTokenMutationReturn = deprecated_mutation(
        ApiMutations.refresh_device_api_token,
        "api",
    )

    delete_device_api_token: GenericMutationReturn = deprecated_mutation(
        ApiMutations.delete_device_api_token,
        "api",
    )

    get_new_device_api_key: ApiKeyMutationReturn = deprecated_mutation(
        ApiMutations.get_new_device_api_key,
        "api",
    )

    invalidate_new_device_api_key: GenericMutationReturn = deprecated_mutation(
        ApiMutations.invalidate_new_device_api_key,
        "api",
    )

    authorize_with_new_device_api_key: DeviceApiTokenMutationReturn = (
        deprecated_mutation(
            ApiMutations.authorize_with_new_device_api_key,
            "api",
            auth=False,
        )
    )


@strawberry.type
class DeprecatedSystemMutations:
    change_timezone: TimezoneMutationReturn = deprecated_mutation(
        SystemMutations.change_timezone,
        "system",
    )

    change_auto_upgrade_settings: AutoUpgradeSettingsMutationReturn = (
        deprecated_mutation(
            SystemMutations.change_auto_upgrade_settings,
            "system",
        )
    )

    run_system_rebuild: GenericMutationReturn = deprecated_mutation(
        SystemMutations.run_system_rebuild,
        "system",
    )

    run_system_rollback: GenericMutationReturn = deprecated_mutation(
        SystemMutations.run_system_rollback,
        "system",
    )

    run_system_upgrade: GenericMutationReturn = deprecated_mutation(
        SystemMutations.run_system_upgrade,
        "system",
    )

    reboot_system: GenericMutationReturn = deprecated_mutation(
        SystemMutations.reboot_system,
        "system",
    )

    pull_repository_changes: GenericMutationReturn = deprecated_mutation(
        SystemMutations.pull_repository_changes,
        "system",
    )

    set_ssh_settings: GenericMutationReturn = deprecated_mutation(
        SystemMutations.change_ssh_settings,
        "system",
    )


@strawberry.type
class DeprecatedUsersMutations:
    create_user: UserMutationReturn = deprecated_mutation(
        UsersMutations.create_user,
        "users",
    )

    delete_user: GenericMutationReturn = deprecated_mutation(
        UsersMutations.delete_user,
        "users",
    )

    update_user: UserMutationReturn = deprecated_mutation(
        UsersMutations.update_user,
        "users",
    )

    add_ssh_key: UserMutationReturn = deprecated_mutation(
        UsersMutations.add_ssh_key,
        "users",
    )

    remove_ssh_key: UserMutationReturn = deprecated_mutation(
        UsersMutations.remove_ssh_key,
        "users",
    )


@strawberry.type
class DeprecatedStorageMutations:
    resize_volume: GenericMutationReturn = deprecated_mutation(
        StorageMutations.resize_volume,
        "storage",
    )

    mount_volume: GenericMutationReturn = deprecated_mutation(
        StorageMutations.mount_volume,
        "storage",
    )

    unmount_volume: GenericMutationReturn = deprecated_mutation(
        StorageMutations.unmount_volume,
        "storage",
    )

    migrate_to_binds: GenericJobMutationReturn = deprecated_mutation(
        StorageMutations.migrate_to_binds,
        "storage",
    )


@strawberry.type
class DeprecatedServicesMutations:
    enable_service: ServiceMutationReturn = deprecated_mutation(
        ServicesMutations.enable_service,
        "services",
    )

    disable_service: ServiceMutationReturn = deprecated_mutation(
        ServicesMutations.disable_service,
        "services",
    )

    stop_service: ServiceMutationReturn = deprecated_mutation(
        ServicesMutations.stop_service,
        "services",
    )

    start_service: ServiceMutationReturn = deprecated_mutation(
        ServicesMutations.start_service,
        "services",
    )

    restart_service: ServiceMutationReturn = deprecated_mutation(
        ServicesMutations.restart_service,
        "services",
    )

    move_service: ServiceJobMutationReturn = deprecated_mutation(
        ServicesMutations.move_service,
        "services",
    )


@strawberry.type
class DeprecatedJobMutations:
    remove_job: GenericMutationReturn = deprecated_mutation(
        JobMutations.remove_job,
        "jobs",
    )
