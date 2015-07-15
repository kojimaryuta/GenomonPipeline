#  Copyright Human Genome Center, Institute of Medical Science, the University of Tokyo
#  @since 2015
import sys
import os
import yaml
from __main__ import *
from resource.genomon_rc import job_config_default as default_values
import job_check


"""
    Genomon job configuration file parse
    How to use it:
        ge_job = genomonjob( 'path to the job configuration file' )
        ge_job.get( 'bwa' )

"""
class genomon_job:
    #
    # Interface
    #
    def __init__( self, job_file = None, param_file = None, log = None ):

        self.__log = log
        if job_file != None:
            self.open_job( job_file )
            self.open_param( param_file )

        self.__default = default_values

    def open_param( self, param_file = None ):
        if param_file != None:
            self.__param_file = param_file

        try:
            if self.__param_file == None:
                self.__log.error( "genomon_job.get: param file is not loaded properly." )
                raise

            f = open( self.__param_file )
            self.__param = yaml.load( f )
            f.close()

        except IOError as (errno, stderror ):
            self.__log.error( "genomon_job.open_job: IOError: error number: {num}, std_error: {stderr}".format(
                        num = errno, stderr = stderror ) )
            raise

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.__log.error( "genomon_job.open_job: unexpected error:", sys.exc_info()[0] )
            self.__log.error("{0}: {1}:{2}".format( exc_type, fname, exc_tb.tb_lineno) )
            raise

    def open_job( self, job_file = None ):
        if job_file != None:
            self.__job_file = job_file

        try:
            if self.__job_file == None:
                self.__log.error( "genomon_job.get: job file is not loaded properly." )
                raise

            f = open( self.__job_file )
            self.__job = yaml.load( f )
            f.close()

        except IOError as (errno, stderror ):
            self.__log.error( "genomon_job.open_job: IOError: error number: {num}, std_error: {stderr}".format(
                        num = errno, stderr = stderror ) )
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.__log.error( "genomon_job.open_job: unexpected error:", sys.exc_info()[0] )
            self.__log.error("{0}: {1}:{2}".format( exc_type, fname, exc_tb.tb_lineno) )

    def get_param( self, task, item ):
        param_dict = self.__param.get( task )
        return_value = None
        if param_dict:
            if item in param_dict:
                return_value = param_dict[ item ]

        if None == return_value:
            if item in self.__default[ task ]:
                return_value = self.__default[ task ][ item ]
            else:
                return_value = None

        return return_value


    def get_job( self, item ):
        if self.__job != None:
            return_item = self.__job.get( item )
            if return_item == None:
                if item in self.__default:
                    return_item = self.__default[ item ]
                else:
                    pass
                    #self.__log.error( "genomon_job.get: specified item \"{item}\" has not been found in yaml.".format(
                    #                item = item ) )
            return return_item
        else:
            self.__log.error( "genomon_job.get: job file is not loaded properly." )
            return None

    def check_file( self, keyword_file ):
        try:
            f = open( keyword_file )
            f_yaml = yaml.load( f )
            if ( job_check.Job_file_check( self.__job, f_yaml ) and
                 job_check.Param_file_check( self.__job, self.__param, f_yaml ) ):
                return_value = True
            else:
                return_value = False

            f.close()

            return return_value

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.__log.error( "genomon_job.open_job: unexpected error:", sys.exc_info()[0] )
            self.__log.error("{0}: {1}:{2}".format( exc_type, fname, exc_tb.tb_lineno) )
            raise

