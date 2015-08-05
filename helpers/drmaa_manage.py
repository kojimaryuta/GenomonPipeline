#! /usr/bin/python
"""

This is a Python parser module for annotation database


"""
import os
import sys
import drmaa
import time
import inspect
import threading

################################################################################
#
# Annotation database parser
#
################################################################################
class JobManage:

    def whoami( self ):
        return inspect.stack()[1][3]

    def whosdaddy( self ):
        return inspect.stack()[2][3]

    def __init__( self, native_param = None, log_dir = None, work_dir = None):
        """
        JobManage constructor

        """
        try:
            self.decodestatus = {
                drmaa.JobState.UNDETERMINED: 'process status cannot be determined',
                drmaa.JobState.QUEUED_ACTIVE: 'job is queued and active',
                drmaa.JobState.SYSTEM_ON_HOLD: 'job is queued and in system hold',
                drmaa.JobState.USER_ON_HOLD: 'job is queued and in user hold',
                drmaa.JobState.USER_SYSTEM_ON_HOLD: 'job is queued and in user and system hold',
                drmaa.JobState.USER_SYSTEM_SUSPENDED: 'job is suspended and in user and system hold',
                drmaa.JobState.RUNNING: 'job is running',
                drmaa.JobState.SYSTEM_SUSPENDED: 'job is system suspended',
                drmaa.JobState.USER_SUSPENDED: 'job is user suspended',
                drmaa.JobState.DONE: 'job finished normally',
                drmaa.JobState.FAILED: 'job finished, but failed',
                }

            if native_param:
                self.native_param = native_param
            if log_dir:
                self.log_dir = log_dir
            if work_dir:
                self.work_dir = work_dir

            self.lock = threading.Lock()

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print( "{function}: Unexpected error: {error}".format( function = self.whoami(), error = sys.exc_info()[0] ) )
            print("{0}: {1}:{2}".format( exc_type, fname, exc_tb.tb_lineno) )
            raise Exception( 'drmaa_manage.constructor failed' )

    def set_native_param( self, native_param ):
        """
            Set native parameter for job submittion
        """
        self.native_param = native_param

    def __del__( self ):
        """
            Destructor

        """
        self.lock.acquire()
        self.delete_job_template( )
        self.lock.release()
        self.session.exit()

    def init_job_template( self, command, args = [],  log_dir = None, cmd_options = '' ):
        """
            DRMAA job template initialization
        """

        if log_dir:
            self.log_dir = log_dir

        self.job_template = {}
        self.jobids = []

        try:
            if not hasattr( self, 'session' ):
                self.session = drmaa.Session()
                self.session.initialize()

            jt = self.session.createJobTemplate()
            jt.remoteCommand = '/bin/bash ' + command
            jt.args = args
            jt.nativeSpecification = self.native_param.format( cmd_options = cmd_options )
            jt.workingDirectory = self.work_dir
            jt.outputPath = ':' + self.log_dir
            jt.errorPath = ':' + self.log_dir
            jt.joinFiles = False
            jt.jobEnvironment = os.environ

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print( "{function}: Unexpected error: {error}".format( function = self.whoami(), error = sys.exc_info()[0] ) )
            print("{0}: {1}:{2}".format( exc_type, fname, exc_tb.tb_lineno) )
            raise Exception( 'drmaa_manage.init_job_template failed' )

        return jt

    def run_array_job( self,
                       command,
                       id_start = 1,
                       id_end = 1,
                       id_step = 1,
                       args = [],
                       log_dir = None,
                       cmd_options = '' ):
        try:
            if not log_dir:
                log_dir = self.log_dir

            self.lock.acquire()
            jt = self.init_job_template( 
                                    command,
                                    args = [],
                                    log_dir = log_dir,
                                    cmd_options = cmd_options )

            jobids = self.session.runBulkJobs( jt, id_start, id_end, id_step )
            jobid = jobids[ 0 ][:jobids[ 0 ].find( '.' )]
            self.lock.release()
            self.session.synchronize( jobids )
            self.job_template[ jobid ] = jt

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print( "{function}: Unexpected error: {error}".format( function = self.whoami(), error = sys.exc_info()[0] ) )
            print("{0}: {1}:{2}".format( exc_type, fname, exc_tb.tb_lineno) )
            raise Exception( 'drmaa_manage.run_array_job failed' )

    def run_job( self, command, array_param = None, args = [],  log_dir = None, cmd_options = '' ):
        try:
            if not log_dir:
                log_dir = self.log_dir

            self.lock.acquire()
            jt = self.init_job_template(
                                    command,
                                    args = [],
                                    log_dir = log_dir,
                                    cmd_options = cmd_options )
            jobid = self.session.runJob( jt )
            self.lock.release()
            self.job_template[ jobid ] = jt

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print( "{function}: Unexpected error: {error}".format( function = self.whoami(), error = sys.exc_info()[0] ) )
            print("{0}: {1}:{2}".format( exc_type, fname, exc_tb.tb_lineno) )
            raise Exception( 'drmaa_manage.run_job failed' )

    def delete_job_template( self, jobid = None ):
        try:
            if jobid:
                if jobid in self.job_template:
                    self.session.deleteJobTemplate( self.job_template[ jobid ] )
                    del self.job_template[ jobid ]
            else:
                for jobid in self.job_template.keys():
                    self.session.deleteJobTemplate( jt = self.job_template[ jobid ] )
                    del self.job_template[ jobid ]

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print( "{function}: Unexpected error: {error}".format( function = self.whoami(), error = sys.exc_info()[0] ) )
            print("{0}: {1}:{2}".format( exc_type, fname, exc_tb.tb_lineno) )
            raise Exception( 'drmaa_manage.delete_job_template failed' )

    def wait_jobs( self ):

        return_code = None
        try:
            for jobid in self.job_template.keys():
                exited = False
                while not exited:
                    retval = self.session.wait( jobid, drmaa.Session.TIMEOUT_WAIT_FOREVER )
                    exited = retval.hasExited

                else:
                    return_code = retval.exitStatus
                    self.delete_job_template( jobid = jobid )
                    if return_code != 0:
                        raise Exception( 'Job {jobid} exitted with {code}.'.format( jobid = jobid, code = str( return_code ) ) )

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print( "{function}: Unexpected error: {error}, exit_status = {ret}".format( function = self.whoami(), error = sys.exc_info()[0], ret = return_code ) )
            print( e )
            print( "{0}: {1}:{2}".format( exc_type, fname, exc_tb.tb_lineno) )
            raise Exception( 'Job {jobid} exitted with {code}.'.format( jobid = jobid, code = str( return_code ) ) )

        return return_code

