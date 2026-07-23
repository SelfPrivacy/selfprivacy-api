import gettext

_ = gettext.gettext


KANIDM_DESCRIPTION = _(
    "Kanidm is the identity and authentication service that manages users and access to system services."
)

KANIDM_PROBLEMS = _(
    "In some cases, a Kanidm update may introduce breaking changes affecting the API, CLI commands, or configuration compatibility."
)

KANIDM_DEBUG_HELP = _(
    "Console commands to debug:\n"
    '"systemctl status kanidm.service"\n'
    '"journalctl -u kanidm.service -f"'
)
