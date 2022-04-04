#!/usr/bin/env python
import sys
from rsgee.manager import Manager
import mapbiomas.settings as settings

sys.dont_write_bytecode = True


def main(command, settings_name=None):
    db_settings = settings.global_settings.DATABASE
    service_account = settings.global_settings.SERVICE_ACCOUNT

    Manager(db_settings, service_account).execute_command(command, settings_name)


if __name__ == "__main__":
    main(*sys.argv[1:3])
