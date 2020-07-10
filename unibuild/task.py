# Copyright (C) 2015 Sebastian Herbord.  All rights reserved.
# Copyright (C) 2016 - 2019 Mod Organizer contributors.
#
# This file is part of Mod Organizer.
#
# Mod Organizer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mod Organizer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mod Organizer.  If not, see <http://www.gnu.org/licenses/>.
import os
import os.path
import time

from unibuild.manager import TaskManager


class Task(object):
    """
    base class of all elements in the dependency graph
    """

    class FailBehaviour:
        FAIL = 1
        CONTINUE = 2
        SKIP_PROJECT = 3

    def __init__(self):
        self.__dependencies = []
        self._context = None
        self.__fail_behaviour = Task.FailBehaviour.FAIL
        self.__dummy = False

    @property
    def name(self):
        return

    @property
    def settings(self):
        return {}

    @property
    def dependencies(self):
        return self.__dependencies

    def depends_on(self, name):
        for d in self.__dependencies:
            if d.name == name:
                return True

            if d.depends_on(name):
                return True

        return False

    @property
    def enabled(self):
        return True

    @enabled.setter
    def enabled(self, value):
        pass

    @property
    def fail_behaviour(self):
        return self.__fail_behaviour

    def set_fail_behaviour(self, behaviour):
        self.__fail_behaviour = behaviour
        return self

    @staticmethod
    def _expiration():
        return None

    def __success_path(self):
        from config import config
        task_name = self.name.replace("/", "_").replace("\\", "_").replace(" ", "_")
        ctx_name = self._context.name if self._context else task_name
        if (config['progress_method'] == 'folders'):
            return os.path.join(config["paths"]["progress"], ctx_name,
                                "{}_complete.txt".format(task_name))
        else:
            return os.path.join(config["paths"]["progress"],
                                "{}_complete_{}.txt".format(ctx_name, task_name))

    def already_processed(self):
        if not os.path.exists(self.__success_path()):
            return False

        expiration_duration = self._expiration()
        if expiration_duration:
            return os.path.getmtime(self.__success_path()) + expiration_duration > time.time()
        return True

    def mark_success(self):
        if not self.__dummy:
          dir_path = os.path.split(self.__success_path())[0]
          if not os.path.exists(dir_path):
            os.makedirs(dir_path)
          with open(self.__success_path(), "w"):
            pass

    def dummy(self):
        self.__dummy = True
        return self

    def depend(self, task):
        """
        add a task as a dependency of this one. This means that the dependent task has to be fulfilled
        before this one will be processed.
        The order in which dependencies are fulfilled is arbitrary however, you can not control which
        of two sibling Tasks is processed first. This is because independent tasks could be processed
        asynchronously and they may be also be dependencies for a third task.
        """
        if isinstance(task, str):
            task_obj = TaskManager().get_task(task)
            if task_obj is None:
                raise KeyError("unknown project \"{}\"".format(task))
            else:
                task = task_obj
        else:
            if self._context:
                task.set_context(self._context)

        self.__dependencies.append(task)
        return self

    def set_context(self, context):
        if self._context is None:
            self._context = context
            for dep in self.__dependencies:
                dep.set_context(context)

    def applies(self, parameters):
        return

    def fulfilled(self):
        for dep in self.__dependencies:
            if not dep.fulfilled():
                return False
        return True

    def prepare(self):
        """
        initialize this task. At this point you can rely on required tasks to have run. This should be quick to
        complete but needs to initialize everything required by dependent tasks (globals, config, context).
        unlike progress, this is called if the task ran successfully already
        """
        pass

    def process(self, progress):
        pass
