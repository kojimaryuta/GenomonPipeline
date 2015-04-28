"""
wes_pipeline.py

"""

import sys
import os
import shutil
from datetime import datetime
from ruffus import *
from runtask import RunTask

#####################################################################
#
# Private modules
#
from __main__ import *
from resource import genomon_rc as res
from utils import *
from sample import Sample

def check_file_exists(input_file, output_file):
    if not os.path.exists(output_file):
        return True, "Missing file %s" % output_file
    else:
        return False, "File %s exists" % output_file

#####################################################################
#
#   STAGE 0 data preparation
#
Sample = Sample()
Sample.make_param( 'tophat2', '.bam', 'bam', 1, 1 )
starting_file_list = []
for infile1, infile2, outfile1, outfil2 in Sample.param( 'tophat2' ):
    starting_file_list.append( ( infile1, outfile1 ) )


#####################################################################
#
#   STAGE 1 fastq to bam by topha2
#
@parallel( starting_file_list )
@check_if_uptodate( check_file_exists )
def stage_1(
        input_file,
        output_file,
        ):
    """
        Stage 1

    """
    return_code = True

    try:
        function_name = whoami()
        log.info( "#{function}".format( function = function_name ) )

        #
        # Make shell script
        #
        shell_script_full_path = make_script_file_name( function_name, Geno )
        shell_script_file = open( shell_script_full_path, 'w' )
        shell_script_file.write( wgs_res.fisher_mutation_call.format(
                                        log = Geno.dir[ 'log' ],
                                        ref_fa = Geno.conf.get( 'REFERENCE', 'ref_fasta' ),
                                        input_fastq = input_file,
                                        output_bam = output_file,
                                        ref_gtf = Geno.conf.get( 'REFERENCE', 'gtf' ),
                                        bowtie2_db = Geno.conf.get( 'REFERENCE', 'bowtie2' ),
                                        tophat2 = Geno.conf.get( 'SOFTWARE', 'tophat2' ),
                                        script_dir = Geno.dir[ 'script' ]
                                    )
                                )
        shell_script_file.close()

        #
        # Run
        #
        return_code = Geno.RT.run_arrayjob(
                            shell_script_full_path,
                            Geno.job.get( 'cmd_options' )[ function_name ],
                            id_start = 1,
                            id_end = wgs_res.interval_num )
        Geno.status.save_status( function_name, input_file1, return_code )
        if return_code != 0:
            log.error( "{function}: runtask failed".format( function = function_name ) )
            raise

    except IOError as (errno, strerror):
        log.error( "{function}: I/O error({num}): {error}".format(
                        function = whoami(),
                        num = errno,
                        error = strerror)
                )
        return_code = False

    except ValueError:
        log.error( "{function}: ValueError".format(
                        function = whoami()
                    )
                )
        return_code = False

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        log.error( "{function}: Unexpected error: {error} ".format(
                    function = whoami()))
        log.error("{0}: {1}:{2}".format( exc_type, fname, exc_tb.tb_lineno) )
        return_code = False


    return return_code

#####################################################################
#
#   STAGE 2
#
@transform( stage_1, suffix( "2.txt" ), "3.txt" )
@follows( stage_1 )
@check_if_uptodate( check_file_exists )
def stage_2(
        input_file,
        output_file
        ):
    """
        Stage 2

    """
    return_code = True

    try:
        function_name = whoami()
        log.info( "#{function}".format( function = function_name ) )

        #
        # Make shell script
        #
        shell_script_full_path = make_script_file_name( function_name, Geno )
        shell_script_file = open( shell_script_full_path, 'w' )
        shell_script_file.write( wgs_res.fisher_mutation_call.format(
                                        log = Geno.dir[ 'log' ],
                                        ref_fa = Geno.conf.get( 'REFERENCE', 'ref_fasta' ),
                                        input_fastq = input_file,
                                        output_bam = output_file,
                                        ref_gtf = Geno.conf.get( 'REFERENCE', 'gtf' ),
                                        bowtie2_db = Geno.conf.get( 'REFERENCE', 'bowtie2' ),
                                        tophat2 = Geno.conf.get( 'SOFTWARE', 'tophat2' ),
                                        script_dir = Geno.dir[ 'script' ]
                                    )
                                )
        shell_script_file.close()

        #
        # Run
        #
        return_code = Geno.RT.run_arrayjob(
                            shell_script_full_path,
                            Geno.job.get( 'cmd_options' )[ function_name ],
                            id_start = 1,
                            id_end = wgs_res.interval_num )
        Geno.status.save_status( function_name, input_file1, return_code )
        if return_code != 0:
            log.error( "{function}: runtask failed".format( function = function_name ) )
            raise

    except IOError as (errno, strerror):
        log.error( "{function}: I/O error({num}): {error}".format(
                        function = whoami(),
                        num = errno,
                        error = strerror)
                )
        return_code = False

    except ValueError:
        log.error( "{function}: ValueError".format(
                        function = whoami()
                    )
                )
        return_code = False

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        log.error( "{function}: Unexpected error: {error} ".format(
                    function = whoami()))
        return_code = False


    return return_code

#####################################################################
#
#   STAGE 3
#
@transform( stage_2, suffix( "3.txt" ), "4.txt" )
@follows( stage_2 )
@check_if_uptodate( check_file_exists )
def stage_3(
        input_file,
        output_file
        ):
    """
        Stage 3

    """
    return_code = True

    try:
        function_name = whoami()
        log.info( "#{function}".format( function = function_name ) )

        #
        # Make shell script
        #
        shell_script_full_path = make_script_file_name( function_name, Geno )
        shell_script_file = open( shell_script_full_path, 'w' )
        shell_script_file.write( wgs_res.fisher_mutation_call.format(
                                        log = Geno.dir[ 'log' ],
                                        ref_fa = Geno.conf.get( 'REFERENCE', 'ref_fasta' ),
                                        input_fastq = input_file,
                                        output_bam = output_file,
                                        ref_gtf = Geno.conf.get( 'REFERENCE', 'gtf' ),
                                        bowtie2_db = Geno.conf.get( 'REFERENCE', 'bowtie2' ),
                                        tophat2 = Geno.conf.get( 'SOFTWARE', 'tophat2' ),
                                        script_dir = Geno.dir[ 'script' ]
                                    )
                                )
        shell_script_file.close()

        #
        # Run
        #
        return_code = Geno.RT.run_arrayjob(
                            shell_script_full_path,
                            Geno.job.get( 'cmd_options' )[ function_name ],
                            id_start = 1,
                            id_end = wgs_res.interval_num )
        Geno.status.save_status( function_name, input_file1, return_code )
        if return_code != 0:
            log.error( "{function}: runtask failed".format( function = function_name ) )
            raise


    except IOError as (errno, strerror):
        log.error( "{function}: I/O error({num}): {error}".format(
                        function = whoami(),
                        num = errno,
                        error = strerror)
                )
        return_code = False

    except ValueError:
        log.error( "{function}: ValueError".format(
                        function = whoami()
                    )
                )
        return_code = False

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        log.error( "{function}: Unexpected error: {error} ".format(
                    function = whoami()))
        return_code = False


    return return_code


#####################################################################
#
#   LAST STAGE 
#

@follows( stage_3 )
def last_function():
    log.info( "Genomon pipline has finished successflly!" )
    return True