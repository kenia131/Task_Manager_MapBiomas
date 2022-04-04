# -*- coding: utf-8 -*-
from functools import reduce

import ee

from rsgee.settings import SettingsManager as sm
from rsgee.db import DatabaseManager
from rsgee.taskmanager import TaskManager
from rsgee.processors.processing_mediator import ProcessingMediator


class Manager(object):
    def __init__(self, db_settings, service_account={}):
        self.db_settings = db_settings
        self.service_account = service_account

    def execute_command(self, command, settings_name=None):
        if command in ["-r", "run"]:
            self.run(settings_name)
        if command in ["-s", "script"]:
            self.run_script(settings_name)
        elif command in ["-m", "migrate"]:
            self.migrate()
        elif command in ["-h", "help"]:
            self.help()
        elif command in ["-w", "watch"]:
            self.watch()
        else:
            self.help()

    def ee_initialize(self):
        account_name = self.service_account.get("ACCOUNT_NAME")
        account_key = self.service_account.get("ACCOUNT_KEY")

        if account_name and account_key:
            credentials = ee.ServiceAccountCredentials(account_name, account_key)
            ee.Initialize(credentials)
        else:
            ee.Initialize()

    def run(self, settings_name):
        self.ee_initialize()

        sm.set_running_settings(settings_name)

        session = DatabaseManager(self.db_settings).get_session()
        task_manager = TaskManager(session, sm.settings)
        mediator = ProcessingMediator()

        tasks = mediator.process()

        task_manager.add_tasks(tasks)
        task_manager.start()
        task_manager.join()

        session.close()

    def run_script(self, script):
        import importlib

        importlib.import_module(script)

    def migrate(self):
        db = DatabaseManager(self.db_settings)
        db.migrate()

    def watch(self):
        pass

    def help(self):
        print(
            """Usage: manage.py [COMMAND]...
        -r, run                 COMMAND start the processing of tasks.
        -m, migrate             COMMAND create tables in database.
        -w, watch               COMMAND watch tasks processing.
        -h, help                COMMAND show the help
        """
        )
