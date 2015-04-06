#!/usr/bin/python
"""

Genome Analysis Pipeline


"""

import sys
import os
import shutil
from datetime import datetime
import argparse
from glob import glob
from ruffus import *
import yaml

################################################################################
#
# Globals
#
global log
log = None
global Geno
class Geno(object):
    now     = None
    options = None
    conf    = None
    job     = None
    dir     = {}
    RT      = None


################################################################################
#
# Private modules
#
import genomon_rc as res
from genomon_cfg import genomon_config as ge_cfg
from genomon_job import genomon_job as ge_job
from runtask import RunTask
from utils import *

################################################################################
#
# Subroutines
#
def construct_arguments( ):
    """
    Call argparse and create argument object
    
    """

    parser = cmdline.get_argparse( description='Genome Analysis Pipeline' )

    ge_arg = parser.add_argument_group( 'genomon', 'Genomon options' );

    ge_arg.add_argument( '-s', "--config_file",  help = "Genomon pipeline configuration file",    type = str )
    ge_arg.add_argument( '-f', "--job_file",     help = "Genomon pipeline job file",              type = str )
    ge_arg.add_argument( '-m', "--mpi",          help = "Enable MPI",   action ='store_true',     default = False )
    ge_arg.add_argument( '-l', "--abpath",       help = "Use absolute path in scripts", action ='store_true', default = False )

    return parser

########################################
def printheader( myself, options ):
    """
    Print infomration about this run

    """
    Geno.now = datetime.now()

    log.info( "Generated by {my}".format(my = myself ) )
    log.info( "Input config file = {input}".format( input = options.config_file  ) )
    log.info( "Input job file    = {input}".format( input = options.job_file  ) )


########################################
def replace_reserved_string( dir_tmp, cwd ):
    """
    Reserved names to replace strings defined in job configuration file
        project_directory   -> defined as project in job configuration file
        sample_date         -> defined sample_date in job configuration file
        sample_name         -> defined sample_name in job configuration file
        analysis_date       -> date of the pipeline to run
    """
    #
    # Replace reserved strings
    #
    dir_replace = None
    if dir_tmp == 'project_directory':
        dir_replace = Geno.job.get( 'project' )
    elif dir_tmp == 'sample_date':
        dir_replace = str( Geno.job.get( 'sample_date' ) )
    elif dir_tmp == 'sample_name':
        dir_replace = Geno.job.get( 'sample_name' )
    elif dir_tmp == 'sample_date_sample_name':
        dir_replace = str( Geno.job.get( 'sample_date' ) ) + '_' + Geno.job.get( 'sample_name' )
    elif dir_tmp == 'analysis_date':
        dir_replace = str( Geno.job.get( 'analysis_date' ) )
        if dir_replace == 'today' :
            dir_replace = res.date_format.format( 
                        year = Geno.now.year, 
                        month = Geno.now.month, 
                        day = Geno.now.day ) 
    else:
        dir_replace = dir_tmp
    
    return dir_replace

def make_dir( dir ):
    if not os.path.exists( dir ):
        os.makedirs( dir )
    return dir

def get_dir ( dir_tree, cwd, dir_name ):
    """
    return the path to the specified directory by dir_tree

    """
    if isinstance( dir_tree, dict ):
        for dir_tmp in dir_tree.keys():
            dir_replace = replace_reserved_string( dir_tmp, cwd )
            cwd_tmp = cwd + '/' + dir_replace
            if isinstance( dir_tmp, str) and dir_tmp  == dir_name:
                return cwd_tmp
            if ( isinstance( dir_tree[ dir_tmp ], dict ) or
                 isinstance( dir_tree[ dir_tmp ], list ) ):
                dir_returned =  get_dir( dir_tree[ dir_tmp ], cwd_tmp, dir_name  )

                if None != dir_returned:
                    return dir_returned
            
    elif isinstance( dir_tree, list ):
        n = 0
        for dir_tmp in dir_tree:
            if isinstance( dir_tmp, str):
                dir_replace = replace_reserved_string( dir_tmp , cwd )
                cwd_tmp = cwd + '/' + dir_replace
            elif isinstance( dir_tmp, dict):
                dir_replace = replace_reserved_string( dir_tmp.keys()[ 0 ] , cwd )
                cwd_tmp = cwd + '/' + dir_replace

            if ( ( isinstance( dir_tmp, str) and dir_tmp == dir_name ) or
                 ( isinstance( dir_tmp, dict) and dir_tmp.keys()[0] == dir_name ) ):
                return cwd_tmp
            else:
                if ( isinstance( dir_tree[ n ], dict ) or
                     isinstance( dir_tree[ n ], list ) ):
                    dir_returned =  get_dir( dir_tree[ n ], cwd, dir_name )
                    if None != dir_returned:
                        return dir_returned
            n = n + 1
    else:
        if isinstance( dir_tmp, str) and dir_tmp  == dir_name:
            dir_replace = replace_reserved_string( dir_tmp, cwd )
            cwd_tmp = cwd + '/' + dir_replace
            return cwd_tmp

    return None


def make_directories( ):
    """
    Make Directory Tree Structure
       Read directory structure from resource file
       Make sure that input data exists.
       Create results directory if necesesary

    """

    #
    # Make sure the input data is availalbe.
    #
    

    error_message = ''
    try:
        if not os.path.exists( Geno.job.get( 'project_root' )):
            log.error( "Dir: {dir} not found.".format( dir = Geno.job.get( 'project_root' ) ) )
            raise


        #
        # make directories
        #
        dir_tree  = Geno.job.get( 'project_dir_tree' )
        if not dir_tree:
            dir_tree  = yaml.load( res.dir_tree_resource  )

        #
        # get directory locations
        #
        cwd = Geno.job.get( 'project_root' )
        if not Geno.options.abpath:
            os.chdir( cwd )
            cwd = '.'

        subdir = Geno.job.get( 'sample_subdir' )
        if subdir:
            subdir_list = glob( "{dir}/{subdir}".format(
                                    dir = Geno.job.get( 'input_file_dir' ),
                                    subdir = subdir ) )

        for target_dir in res.end_dir_list:
            Geno.dir[ target_dir ] = get_dir( dir_tree, cwd, target_dir )
            make_dir( Geno.dir[ target_dir ] )
            if subdir and target_dir in res.subdir_list:
                for subdir_tmp in subdir_list:
                    make_dir( "{dir}/{subdir}".format(
                                    dir = Geno.dir[ target_dir ],
                                    subdir = os.path.basename( subdir_tmp ) ) )

        #
        # data diretory
        # make symbolic link from the original input_file_dir
        #   if input_file_dir is not the same as data dir
        #
        make_dir( "{data}/{sample_date}".format(
                                data = get_dir( dir_tree, cwd, 'data' ),
                                sample_date = Geno.job.get( 'sample_date' ) ) )
        Geno.dir[ 'data' ] = "{data}/{sample_date}/{sample_name}". format(
                                data = get_dir( dir_tree, cwd, 'data' ),
                                sample_date = Geno.job.get( 'sample_date' ),
                                sample_name = Geno.job.get( 'sample_name' ) )
        if ( not os.path.exists( Geno.dir[ 'data' ] ) and
             Geno.job.get( 'input_file_dir' ) != Geno.dir[ 'data' ] ):
                os.symlink( Geno.job.get( 'input_file_dir' ), Geno.dir[ 'data' ] )

    except IOError as (errno, strerror):
        log.error( "make_directories failed." )
        log.error( "IOError {0}]{1}".format( errno, strerror ) )


    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        log.error( "make_directories failed." )
        log.error( "Unexpected error: {1}".format( error_message ) )
        log.error("{0}: {1}:{2}".format( exc_type, fname, exc_tb.tb_lineno) )

########################################
def copy_config_files():
    """
    Copy genomon system configuration file and job configuration file
    to results directory

    """
    global Geno

    config_dir = Geno.dir[ 'config' ]

    src = Geno.options.config_file
    basename = os.path.splitext( os.path.basename( src ) )[ 0 ]
    ext = os.path.splitext( os.path.basename( src ) )[ 1 ]
    config_backup = res.file_timestamp_format.format(
                                        name=basename,
                                        year=Geno.now.year,
                                        month=Geno.now.month,
                                        day=Geno.now.day,
                                        hour=Geno.now.hour,
                                        min=Geno.now.minute,
                                        msecond=Geno.now.microsecond )
    dest = "{dir}/{basename}{ext}".format( dir = config_dir,
                                            basename = config_backup,
                                            ext = ext )
    shutil.copyfile( src, dest )

    src = Geno.options.job_file
    basename = os.path.splitext( os.path.basename( src ) )[ 0 ]
    ext = os.path.splitext( os.path.basename( src ) )[ 1 ]
    dest = "{dir}/{basename}{ext}".format( dir = config_dir,
                                            basename = config_backup,
                                            ext = ext )
    shutil.copyfile( src, dest )

########################################
def copy_script_files():
    """
    Copy genomon script files to script directory

    """
    global Geno

    for script_file in res.script_files:
        src = "{dir}/{file}".format(
                    dir = Geno.dir[ 'genomon' ],
                    file = script_file )
        dest = "{dir}/{file}".format(
                    dir = Geno.dir[ 'script' ],
                    file = os.path.basename( script_file )
                )
        shutil.copy( src, dest )

    
########################################
def set_env_variables():
    """
    Set environment variables for some tools

    """
    global Geno

    for tool_env in res.env_list.keys():
        env_value = Geno.conf.get( 'ENV', tool_env )
        for env_name in res.env_list[ tool_env ]:
            tmp = os.environ[ env_name ]
            os.environ[ env_name ] = tmp + ':' + env_value


###############################################################################
#
# main
#
def main():
    global log
    global Geno

    try:
        #
        # Argument parse
        #
        argvs = sys.argv
        arg_parser = construct_arguments()

        #
        # parse arguments
        #
        if len(argvs) < 3:
            arg_parser.print_help()
            sys.exit( 0 )

        Geno.options = arg_parser.parse_args()
        Geno.dir[ 'genomon' ] = os.path.dirname( os.path.realpath(__file__) )

        #
        # Logging setup
        #
        #  logger which can be passed to multiprocessing ruffus tasks
        if Geno.options.verbose:
            verbose_level = Geno.options.verbose
        else:
            verbose_level = 0

        log, log_mutex = cmdline.setup_logging( __name__,
                                                Geno.options.log_file,
                                                verbose_level)
        #
        # Print header in log
        #
        printheader( argvs[ 0 ], Geno.options )

        #
        # Parse system and job config file
        #
        Geno.conf = ge_cfg( config_file = Geno.options.config_file, log = log )
        Geno.job = ge_job( Geno.options.job_file, log = log )

        #
        # Prepare directory tree for pipeline to run.
        # Copy the input configuration files to results directory
        # Link input_data to project's data directory
        #
        make_directories()
        copy_config_files()
        copy_script_files()
        set_env_variables()

        #
        # Initalize RunTask object
        #
        Geno.RT = RunTask( enable_mpi = Geno.options.mpi,
                           log = log,
                           ncpus = Geno.options.jobs,
                           qsub_cmd = Geno.job.get( 'qsub_cmd' ) )

        #
        # Print information
        #
#        log.info( '# main: process={num}'.format( num = Geno.options.jobs ) )

        #######################################################################
        #
        # Run the defined pipeline
        # Figure out what analysis to run from job configuration file
        #
        job_tasks = Geno.job.get( 'tasks' )

        if job_tasks[ 'WGS' ]:
            import wgs_pipeline as pipeline

        elif job_tasks[ 'WES' ]:
            import wes_pipeline as pipeline

        elif job_tasks[ 'Capture' ]:
            import capture_pipeline as pipeline

#
#       multiprocess
#
#       Optional. The number of processes which should be dedicated to running in parallel independent tasks
#            and jobs within each task. If multiprocess is set to 1, the pipeline will execute in the main process.
#
#       multithread
#
#       Optional. The number of threads which should be dedicated to running in parallel independent tasks
#            and jobs within each task. Should be used only with drmaa.
#            Otherwise the CPython global interpreter lock (GIL) will slow down your pipeline
#
#       verbose            
#
#       Optional parameter indicating the verbosity of the messages sent to logger: (Defaults to level 1 if unspecified)
#
#           level 0 : nothing
#           level 1 : Out-of-date Task names
#           level 2 : All Tasks (including any task function docstrings)
#           level 3 : Out-of-date Jobs in Out-of-date Tasks, no explanation
#           level 4 : Out-of-date Jobs in Out-of-date Tasks, with explanations and warnings
#           level 5 : All Jobs in Out-of-date Tasks, (include only list of up-to-date tasks)
#           level 6 : All jobs in All Tasks whether out of date or not
#           level 10: logs messages useful only for debugging ruffus pipeline code
        pipeline_run(   target_tasks = [ pipeline.last_function ],
                        multiprocess = Geno.options.jobs,
                        logger = log,
                        verbose = 50)
#        pipeline_cleanup()

#        pipeline_printout_graph( "flow_{job_type}".format( job_type = job_tasks.keys()[ 0 ] ),
#                                 "jpg",
#                                 [ pipeline.last_function ]
#                )
#        cmdline.run( Geno.options )
        #
        #######################################################################

    except IOError as (errno, strerror):
        log.error( "{0}: I/O error({1}): {2}".format( whoami(), errno, strerror) )

    except ValueError:
        log.error( "{0}: ValueError".format( whoami() ) )

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        log.error( "{0}: Unexpected error".format( whoami() ) )
        log.error("{0}: {1}:{2}".format( exc_type, fname, exc_tb.tb_lineno) )

    sys.exit( 0 )


################################################################################
if __name__ == "__main__":
    main()

