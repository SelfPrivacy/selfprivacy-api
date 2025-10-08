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
  selfprivacy_api/graphql/queries/monitoring.py \
