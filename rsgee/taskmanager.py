import datetime
import os
import sys
import time
from threading import Thread

import ee

from rsgee.settings import SettingsManager as sm
from rsgee.db.models import Task, TaskLog


class TaskManager(Thread):
    def __init__(self, session, settings):
        super().__init__()

        self.__session = session

        self.__max_tasks = settings.EXPORT_MAX_TASKS
        self.__interval = settings.EXPORT_INTERVAL
        self.__max_errors = settings.EXPORT_MAX_ERRORS

        self.__data = {}

        self.__tasks_awaiting = {}
        self.__tasks_running = {}
        self.__tasks_completed = {}
        self.__tasks_error = {}
        self.__tasks_failed = {}

    def run(self):
        def process_tasks(tasks):
            while len(tasks) > 0 or len(self.__tasks_running) > 0:
                try:
                    self.__print()
                    self.__submit_task(tasks)
                    self.update_tasks()
                except Exception as e:
                    print("Exception: {0}".format(e))

                time.sleep(self.__interval)

        process_tasks(self.__tasks_awaiting)
        print("Finished!!!")
        sys.exit(0)

    def add_tasks(self, tasks):
        for task in tasks:
            self.add_task(task)

    def add_task(self, task):
        code = task.config["description"]

        self.__data[code] = task

        task = self.get_task(code)

        if not task:
            # data_json = ee.serializer.toJSON(data)
            task = Task(code=code, state=ee.batch.Task.State.UNSUBMITTED)

            self.__session.add(task)
            self.__session.commit()
            print("Task saved!!!")

            task_log = TaskLog(
                task=task.id,
                state=ee.batch.Task.State.UNSUBMITTED,
                date=datetime.datetime.now(),
            )
            self.__session.add(task_log)
            self.__session.commit()

        if task and task.state not in [
            ee.batch.Task.State.COMPLETED,
            ee.batch.Task.State.CANCELLED,
        ]:
            self.__tasks_awaiting[code] = True
        else:
            print("Task {0} exists!".format(code))

    def update_tasks(self):
        for code, t in self.__tasks_running.copy().items():
            task = self.get_task(code)

            remote_state = t.status()["state"]
            remote_info = None

            if remote_state == ee.batch.Task.State.UNSUBMITTED:
                try:
                    t.start()
                    remote_state = ee.batch.Task.State.READY
                    pass
                except Exception as e:
                    print(e)
                    del self.__tasks_running[code]
                    remote_info = t.status()["error_message"]
                    remote_state = ee.batch.Task.State.FAILED

                    self.__tasks_error[code] = self.__tasks_error.get(code, 0) + 1

                    if self.__tasks_error[code] <= self.__max_errors:
                        self.__tasks_failed[code] = True

            elif (
                remote_state == ee.batch.Task.State.RUNNING
                and task.state == ee.batch.Task.State.READY
            ):
                task.start_date = datetime.datetime.now()

            elif remote_state == ee.batch.Task.State.COMPLETED:
                task.end_date = datetime.datetime.now()
                del self.__tasks_running[task.code]
                self.__tasks_completed[task.code] = True

            elif remote_state in [
                ee.batch.Task.State.CANCELLED,
                ee.batch.Task.State.CANCEL_REQUESTED,
            ]:
                del self.__tasks_running[task.code]

            elif remote_state == ee.batch.Task.State.FAILED:
                remote_info = t.status()["error_message"]

                if (
                    remote_info.find("No valid training data were found") != -1
                    or remote_info.find("Internal error") != -1
                ):
                    remote_state = ee.batch.Task.State.CANCELLED
                    self.__tasks_failed[code] = True
                    del self.__tasks_running[task.code]
                else:
                    self.__tasks_error[code] = self.__tasks_error.get(code, 0) + 1

                    if self.__tasks_error[code] <= self.__max_errors:
                        remote_state = ee.batch.Task.State.UNSUBMITTED
                        self.__tasks_running[code] = self.__generate_task(code)
                    else:
                        self.__tasks_failed[code] = True
                        del self.__tasks_running[code]

            if task.state != remote_state:
                task.state = remote_state
                self.__session.add(
                    TaskLog(
                        task=task.id,
                        state=remote_state,
                        date=datetime.datetime.now(),
                        info=remote_info,
                    )
                )

            self.__session.commit()

    def __print(self):
        os.system("clear")
        print("************************* Tasks *************************")
        print("Awaiting:    {0} tasks".format(len(self.__tasks_awaiting)))
        print("Running:     {0} tasks".format(len(self.__tasks_running)))
        print("Completed:   {0} tasks".format(len(self.__tasks_completed)))
        print("Error:       {0} tasks".format(len(self.__tasks_error)))
        print("Failed:      {0} tasks".format(len(self.__tasks_failed)))
        print("*********************************************************")

        for code, task in self.__tasks_running.items():
            output = self.get_output_path(task)
            print(output, "|", task.status()["state"])

    def get_output_path(self, task):
        if "fileExportOptions" in task.config:
            fileExportOptions = task.config["fileExportOptions"]

            if "gcsDestination" in fileExportOptions:
                return "{bucket}/{filenamePrefix}".format(
                    **fileExportOptions["gcsDestination"]
                )

            if "driveDestination" in fileExportOptions:
                return "{folder}/{filenamePrefix}".format(
                    **fileExportOptions["driveDestination"]
                )

        if "assetExportOptions" in task.config:
            return task.config["assetExportOptions"]["earthEngineDestination"][
                "name"
            ].replace("projects/earthengine-legacy/assets/users/", "")

    def __submit_task(self, tasks):

        for code in sorted(tasks.copy().keys()):
            if code in self.__tasks_failed.keys():
                del tasks[code]
                continue

            max_tasks = self.__max_tasks

            if self.__should_process_additional_tasks():
                max_tasks = self.__max_tasks + 1

            if len(self.__tasks_running) >= max_tasks or len(tasks) == 0:
                break

            task = self.get_task(code)
            if task.state in [
                ee.batch.Task.State.COMPLETED,
                ee.batch.Task.State.CANCELLED,
            ]:
                del tasks[code]
            if task.state in [
                ee.batch.Task.State.UNSUBMITTED,
                ee.batch.Task.State.FAILED,
            ]:
                self.__tasks_running[code] = self.__export_task(code)
                del tasks[code]
            if task.state in [ee.batch.Task.State.READY, ee.batch.Task.State.RUNNING]:
                print("{0} running in other process".format(code))
                # del tasks[code]

    def __export_task(self, code):
        task = self.get_task(code)

        if task:
            data = self.__data[code]
            return data

        raise AttributeError("Task not found")

    def get_task(self, code):
        task = self.__session.query(Task).filter_by(code=code).first()
        return task

    def __generate_task_code(self, year, region_id):
        settings_name = sm.settings.NAME
        return f"{settings_name}_{year}_{region_id}"

    def __should_process_additional_tasks(self):
        time_check = self.__is_current_time_between(
            datetime.time(0, 0), datetime.time(8, 0)
        )
        day_check = self.__is_weekend()

        return time_check or day_check

    def __is_current_time_between(self, begin_time, end_time):
        check_time = datetime.datetime.now().time()
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else:  # crosses midnight
            return check_time >= begin_time or check_time <= end_time

    def __is_weekend(self, check_date=None):
        check_date = check_date or datetime.datetime.now().date()
        return check_date.weekday() >= 5
