"""
    File name: MPFProcess.py
    Author: Matthew Allen

    Description:
        This is the parent class for a process object. It executes the process loop and handles i/o with the main process.
        Note that process termination happens regardless of what any child objects are in the middle of, so it is
        important to implement the cleanup function properly as it is the only notification of termination that child
        objects will get.
"""

from multiprocessing import Process
import traceback
class MPFProcess(Process):
    def __init__(self, process_name = "unnamed_process", loop_wait_period=None):
        Process.__init__(self)
        self._out = None
        self._inp = None
        self._loop_wait_period = loop_wait_period
        self.name = process_name
        self.shared_memory = None
        self.task_checker = None
        self.results_publisher = None
        self._MPFLog = None

    def run(self):
        """
        The function to be called when a process is started.
        :return: None
        """

        try:
            #We import everything important here to ensure that the libraries we need will be imported into the new
            #process memory instead of the main process memory.
            from MPFramework import MPFResultPublisher
            from MPFramework import MPFTaskChecker
            import logging
            import time

            #This are our i/o objects for interfacing with the main process.
            self.task_checker = MPFTaskChecker(self._inp, self.name)
            self.results_publisher = MPFResultPublisher(self._out, self.name)

            self._MPFLog = logging.getLogger("MPFLogger")
            self._MPFLog.debug("MPFProcess initializing...")

            #Initialize.
            self.init()
            self._MPFLog.debug("MPFProcess {} has successfully initialized".format(self.name))

            while True:
                #Here is the simple loop to be executed by this process until termination.

                #Check for new inputs from the main process.
                if self.task_checker.check_for_update():

                    #If we are told to stop running, do so.
                    if self.task_checker.header == "STOP PROCESS":
                        self._MPFLog.debug("PROCESS {} RECEIVED STOP SIGNAL!".format(self.name))
                        break

                    #Otherwise, update with the latest main process message.
                    self.update(self.task_checker.header, self.task_checker.latest_data)

                #Take a step.
                self.step()

                #Publish any output we might have.
                self.publish()

                #Wait if requested.
                if self._loop_wait_period is not None:
                    time.sleep(self._loop_wait_period)

        except:
            #Catch-all because I'm lazy.
            error = traceback.format_exc()
            self._MPFLog.critical("MPFPROCESS {} HAS CRASHED!\n"
                               "EXCEPTION TRACEBACK:\n"
                               "{}".format(self.name, error))

        finally:
            #Clean everything up and terminate.
            if self.task_checker is not None:
                self._MPFLog.debug("MPFProcess {} Cleaning task checker...".format(self.name))
                self.task_checker.cleanup()
                del self.task_checker
                self._MPFLog.debug("MPFProcess {} has cleaned its task checker!".format(self.name))

            if self.results_publisher is not None:
                del self.results_publisher

            self._MPFLog.debug("MPFProcess {} Cleaning up...".format(self.name))
            self.cleanup()

            self._MPFLog.debug("MPFProcess {} Exiting!".format(self.name))
            return

    def set_shared_memory(self, memory):
        self.shared_memory = memory

    def init(self):
        raise NotImplementedError

    def update(self, header, data):
        raise NotImplementedError

    def step(self):
        raise NotImplementedError

    def publish(self):
        raise NotImplementedError

    def cleanup(self):
        raise NotImplementedError