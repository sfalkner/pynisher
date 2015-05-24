#! /bin/python
import time
import numpy as np
import multiprocessing
import unittest
import os
import signal
import logging

import pynisher

all_tests=True


# TODO: get rid of numpy just to create some data of fixed size!
# 		add tests for cpu usage
#		add test for num_processes
#		add test with crash_unexpectedly to see what happens if the function call dies!

def simulate_work(size_in_mb, wall_time_in_s, num_processes):
    # allocate memory (size_in_mb) with an array
    # note the actual size in memory of this process is a little bit larger 
    s = np.float64().itemsize    
    A = np.ones(int((size_in_mb*1024*1024)/s),dtype=np.float64);

    # try to spawn new processes
    if (num_processes > 0):
        # data parallelism
        multiprocessing.Pool(num_processes)

    # sleep for specified duration
    time.sleep(wall_time_in_s)
    return((size_in_mb, wall_time_in_s, num_processes));


def crash_unexpectedly(signum):
    pid = os.getpid()
    time.sleep(1)
    os.kill(pid, signum)
    time.sleep(1)
    
def cpu_usage(wall_time_in_s,cpu_time_in_s ):
    cpu_percentage = (100/wall_time_in_s)*cpu_time_in_s
    return(cpu_percentage)

class test_limit_resources_module(unittest.TestCase):

    @unittest.skipIf(not all_tests, "skipping successful tests")
    def test_success(self):
        
        local_mem_in_mb = 256
        local_time_in_s = 2
        local_grace_period = 0
        
        wrapped_function = pynisher.enforce_limits(mem_in_mb = local_mem_in_mb, wall_time_in_s=local_time_in_s, grace_period_in_s = local_grace_period)(simulate_work)
        
        for mem in [1,2,4,8,16]:
            print("\nmem: {}\n".format(mem))
            self.assertEqual((mem,0,0),wrapped_function(mem,0,0))

    @unittest.skipIf(not all_tests, "skipping out_of_memory test")
    def test_out_of_memory(self):

        local_mem_in_mb = 64
        local_wall_time_in_s = 2
        local_cpu_time_in_s = None
        local_grace_period = 0
        
        wrapped_function = pynisher.enforce_limits(mem_in_mb = local_mem_in_mb, wall_time_in_s=local_wall_time_in_s, cpu_time_in_s = local_cpu_time_in_s, grace_period_in_s = local_grace_period)(simulate_work)
    
        for mem in [256,512,1024]:
            print("\nmem: {}\n".format(mem))
            self.assertIsNone(wrapped_function(mem,0,0))
    
    @unittest.skipIf(not all_tests, "skipping time_out test")
    def test_time_out(self):

        local_mem_in_mb = -1
        local_time_in_s = 1
        local_grace_period = 2
        
        wrapped_function = pynisher.enforce_limits(mem_in_mb = local_mem_in_mb, wall_time_in_s=local_time_in_s, grace_period_in_s = local_grace_period)(simulate_work)
    
        for mem in [64,128,256,512]:
            print("\nmem: {}\n".format(mem))
            self.assertIsNone(wrapped_function(mem,2,0))

    @unittest.skipIf(not all_tests, "skipping term signal test")
    def test_term_signal(self):

        local_mem_in_mb = -1
        local_time_in_s = 1
        local_grace_period = 1
        
        wrapped_function = pynisher.enforce_limits(mem_in_mb = local_mem_in_mb, wall_time_in_s=local_time_in_s, grace_period_in_s = local_grace_period)(simulate_work)
    
        for mem in [1,2,3,4]:
            print("\nmem: {}\n".format(mem))
            self.assertIsNone(wrapped_function(mem,3,0))
    

    def test_num_processes(self):
        local_mem_in_mb = 350
        local_num_processes = 3
        local_wall_time_in_s = 20
        local_grace_period = 20
        
        wrapped_function = pynisher.enforce_limits(mem_in_mb = local_mem_in_mb, wall_time_in_s=local_wall_time_in_s,num_processes = local_num_processes, grace_period_in_s = local_grace_period)(simulate_work)
        
        for processes in [1,15,50,100,250,350,500,1000]:
            print("\nprocesses: {}\n".format(processes))
            self.assertIsNone(wrapped_function(0,0, processes))
    # system crash when cpu_time in s and wall time in s = 0
    def test_crash_unexpectedly(self):
        local_mem_in_mb = 289
        local_wall_time_in_s = 1
        local_cpu_time_in_s = 1
        local_grace_period = 0
        
        wrapped_function = pynisher.enforce_limits(mem_in_mb = local_mem_in_mb, wall_time_in_s=local_wall_time_in_s, cpu_time_in_s = local_cpu_time_in_s, grace_period_in_s = local_grace_period)(crash_unexpectedly)
        self.assertIsNone(wrapped_function(signal.SIGTERM))
        
class test_cpu_usage(unittest.TestCase):
    def test_high_cpu_percentage(self):
        mem_in_mb = 35
        wall_time_in_s = 10
        cpu_time_in_s = 10
        grace_period = 1
        wrapped_function = pynisher.enforce_limits(mem_in_mb = mem_in_mb, wall_time_in_s=wall_time_in_s, cpu_time_in_s = cpu_time_in_s, grace_period_in_s = grace_period)(cpu_usage)
        self.assertEqual(75,wrapped_function(20,15))
        
#logger = multiprocessing.log_to_stderr()
#logger.setLevel(logging.DEBUG)

unittest.main()
