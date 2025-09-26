#!/bin/bash

xgettext \
  --from-code=UTF-8 \
  --language=Python \
  -k_ \
  -kngettext:1,2 \
  -o selfprivacy_api/locale/messages.pot \
  selfprivacy_api/repositories/users/exceptions.py \
  selfprivacy_api/repositories/users/exceptions_kanidm.py \
  selfprivacy_api/actions/ssh.py \
  selfprivacy_api/actions/users.py \
