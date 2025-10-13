#!/bin/bash

xgettext \
  --from-code=UTF-8 \
  --language=Python \
  -k_ \
  -kngettext:1,2 \
  -o selfprivacy_api/locale/messages.pot \
  selfprivacy_api/utils/strings.py \
  selfprivacy_api/repositories/users/exceptions.py \
  selfprivacy_api/repositories/users/exceptions_kanidm.py \
  selfprivacy_api/repositories/tokens/exceptions.py \
  selfprivacy_api/actions/ssh.py \
  selfprivacy_api/actions/users.py \
  selfprivacy_api/actions/api_tokens.py \
  selfprivacy_api/actions/services.py \
  selfprivacy_api/graphql/mutations/job_mutations.py \
  selfprivacy_api/graphql/mutations/api_mutations.py \
  selfprivacy_api/graphql/mutations/backup_mutations.py \
  selfprivacy_api/graphql/mutations/email_passwords_metadata_mutations.py \
  selfprivacy_api/graphql/mutations/system_mutations.py \
  selfprivacy_api/graphql/mutations/users_mutations.py \
  selfprivacy_api/graphql/mutations/storage_mutations.py \
  selfprivacy_api/graphql/mutations/services_mutations.py \
  selfprivacy_api/graphql/queries/monitoring.py \
  selfprivacy_api/jobs/upgrade_system.py \
  selfprivacy_api/jobs/migrate_to_binds.py \
  selfprivacy_api/models/services.py \



## generate .po

# msginit \
#   --locale=ru_RU \
#   --input=locale/messages.pot \
#   --output-file=locale/ru/LC_MESSAGES/messages.po



## utf8 fix

# iconv -f ISO-8859-5 -t UTF-8 \
#   locale/ru/LC_MESSAGES/messages.po \
#   -o locale/ru/LC_MESSAGES/messages.utf8.po && \
# mv locale/ru/LC_MESSAGES/messages.utf8.po locale/ru/LC_MESSAGES/messages.po



## generate .mo

# msgfmt -o locale/ru/LC_MESSAGES/messages.mo locale/ru/LC_MESSAGES/messages.po
