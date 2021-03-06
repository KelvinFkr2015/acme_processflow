import sys
import os
import logging
import json
import time
import stat
import argparse

from pprint import pformat
from shutil import rmtree, copy

from configobj import ConfigObj
from YearSet import YearSet, SetStatus
from shutil import copyfile
from lib.filemanager import FileManager
from lib.runmanager import RunManager
from lib.mailer import Mailer
from jobs.JobStatus import JobStatus
from util import (setup_globus,
                  check_globus,
                  print_message,
                  print_debug)


def parse_args(argv=None, print_help=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='Path to configuration file.')
    parser.add_argument(
        '-n', '--no-ui', help='Turn off the GUI.', action='store_true')
    parser.add_argument('-l', '--log', help='Path to logging output file.')
    parser.add_argument(
        '-u', '--no-cleanup', help='Don\'t perform pre or post run cleanup. This will leave all run scripts in place.', action='store_true')
    parser.add_argument(
        '-m', '--no-monitor', help='Don\'t run the remote monitor or move any files over globus.', action='store_true')
    parser.add_argument(
        '-f', '--file-list', help='Turn on debug output of the internal file_list so you can see what the current state of the model files are', action='store_true')
    parser.add_argument('-r', '--resource-dir',
                        help='Path to custom resource directory')
    if print_help:
        parser.print_help()
        return
    return parser.parse_args(argv)


def setup(argv, display_event, **kwargs):
    """
    Parse the commandline arguments, and setup the master config dict

    Parameters:
        parser (argparse.ArgumentParser): The parser object
        display_event (Threadding_event): The event to turn the display on and off
    """
    print "entering setup"
    # Setup the parser
    args = parse_args(argv=argv)
    if not args.config:
        parse_args(print_help=True)
        return False, False, False

    event_list = kwargs['event_list']
    thread_list = kwargs['thread_list']
    mutex = kwargs['mutex']

    # check if globus config is valid, else remove it
    globus_config = os.path.join(os.path.expanduser('~'), '.globus.cfg')
    if os.path.exists(globus_config):
        try:
            conf = ConfigObj(globus_config)
        except:
            os.remove(globus_config)

    if not os.path.exists(args.config):
        print "Invalid config, {} does not exist".format(args.config)
        return False, False, False

    # Check that there are no white space errors in the config file
    line_index = check_config_white_space(args.config)
    if line_index != 0:
        print '''
ERROR: line {num} does not have a space after the \'=\', white space is required.
Please add a space and run again.'''.format(num=line_index)
        return False, False, False

    # read the config file and setup the config dict
    try:
        config = ConfigObj(args.config)
    except Exception as e:
        print "Error parsing config file {}".format(args.config)
        parse_args(print_help=True)
        return False, False, False

    # run validator for config file
    if config.get('global'):
        if args.resource_dir:
            config['global']['resource_dir'] = args.resource_dir
        else:
            config['global']['resource_dir'] = os.path.join(
                sys.prefix,
                'share',
                'processflow',
                'resources')
    else:
        return False, False, False

    template_path = os.path.join(
        config['global']['resource_dir'],
        'config_template.json')

    with open(template_path, 'r') as template_file:
        template = json.load(template_file)

    valid, messages = verify_config(config, template)
    if not valid:
        for message in messages:
            print message
        return False, False, False

    config['global']['input_path'] = os.path.join(
        config['global']['project_path'], 'input')
    config['global']['output_path'] = os.path.join(
        config['global']['project_path'], 'output')

    # setup output and cache directories
    if not os.path.exists(config['global']['input_path']):
        os.makedirs(config['global']['input_path'])
    if not os.path.exists(config['global']['output_path']):
        os.makedirs(config['global']['output_path'])

    # Copy the config into the input directory for safe keeping
    input_config_path = os.path.join(config['global']['input_path'], 'run.cfg')
    try:
        copy(args.config, input_config_path)
    except:
        pass

    # setup logging
    if args.log:
        log_path = args.log
    else:
        log_path = os.path.join(
            config.get('global').get('output_path'),
            'workflow.log')
    config['global']['log_path'] = log_path
    logging.basicConfig(
        format='%(asctime)s:%(levelname)s: %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        filename=log_path,
        filemode='w',
        level=logging.INFO)
    logging.getLogger('globus_sdk').setLevel(logging.WARNING)

    # Make sure the set_frequency is a list of ints
    set_frequency = config['global']['set_frequency']
    if not isinstance(set_frequency, list):
        set_frequency = [int(set_frequency)]
    else:
        # These are sometimes strings which break things later
        new_freqs = []
        for freq in set_frequency:
            new_freqs.append(int(freq))
        set_frequency = new_freqs
    config['global']['set_frequency'] = set_frequency

    # setup config for file type directories
    if not isinstance(config['global']['file_types'], list):
        config['global']['file_types'] = [config['global']['file_types']]

    # setup run_scipts_path
    run_script_path = os.path.join(
        config['global']['output_path'],
        'run_scripts')
    config['global']['run_scripts_path'] = run_script_path
    if not os.path.exists(run_script_path):
        os.makedirs(run_script_path)

    # setup tmp_path
    tmp_path = os.path.join(
        config['global']['output_path'],
        'tmp')
    config['global']['tmp_path'] = tmp_path
    if os.path.exists(tmp_path):
        rmtree(tmp_path)
    os.makedirs(tmp_path)

    # setup the year_set list
    config['global']['simulation_start_year'] = int(
        config['global']['simulation_start_year'])
    config['global']['simulation_end_year'] = int(
        config['global']['simulation_end_year'])
    sim_start_year = int(config['global']['simulation_start_year'])
    sim_end_year = int(config['global']['simulation_end_year'])

    config['global']['short_term_archive'] = int(
        config['global']['short_term_archive'])

    # initialize the filemanager
    event_list.push(message='Initializing file manager')
    head, tail = os.path.split(config['global']['source_path'])
    if tail == 'run':
        config['global']['source_path'] = head

    filemanager = FileManager(
        database=os.path.join(
            config['global']['project_path'], 'input', 'workflow.db'),
        types=config['global']['file_types'],
        sta=config['global']['short_term_archive'],
        remote_path=config['global']['source_path'],
        remote_endpoint=config['transfer']['source_endpoint'],
        local_path=os.path.join(config['global']['project_path'], 'input'),
        local_endpoint=config['transfer']['destination_endpoint'],
        mutex=mutex)
    filemanager.populate_file_list(
        simstart=config['global']['simulation_start_year'],
        simend=config['global']['simulation_end_year'],
        experiment=config['global']['experiment'])
    print 'Updating local status'
    filemanager.update_local_status()
    print 'Local status update complete'
    all_data = filemanager.all_data_local()
    if all_data:
        print 'All data is local'
    else:
        print 'Additional data needed'

    logging.info("FileManager setup complete")
    logging.info(str(filemanager))

    if all_data or args.no_monitor:
        print "skipping globus setup"
    else:
        endpoints = [endpoint for endpoint in config['transfer'].values()]
        if args.no_ui:
            print 'Running in no-ui mode'
            addr = config.get('global').get('email')
            if not addr:
                print 'When running in no-ui mode, you must enter an email address.'
                return False, False, False
            setup_success = setup_globus(
                endpoints=endpoints,
                no_ui=True,
                src=config.get('global').get('email'),
                dst=config.get('global').get('email'),
                event_list=event_list)
        else:
            output_path = config.get('global').get('output_path')
            error_output = os.path.join(
                output_path,
                'workflow.error')
            config['global']['error_path'] = error_output
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            sys.stderr = open(error_output, 'w')
            msg = 'Activating endpoints {}'.format(' '.join(endpoints))
            logging.info(msg)
            setup_success = setup_globus(
                endpoints=endpoints,
                display_event=display_event,
                no_ui=False)
        if not setup_success:
            print "Globus setup error"
            return False, False, False
        else:
            print 'Globus authentication complete'
        print 'Checking file access on globus transfer nodes'
        setup_success, endpoint = check_globus(
            source_endpoint=config['transfer']['source_endpoint'],
            source_path=config['global']['source_path'],
            destination_endpoint=config['transfer']['destination_endpoint'],
            destination_path=config['global']['input_path'])
        if not setup_success:
            print 'ERROR! Unable to access {} globus node'.format(endpoint['type'])
            print 'The node may be down, or you may not have access to the requested directory'
            return False, False, False

    # setup the runmanager
    runmanager = RunManager(
        event_list=event_list,
        output_path=config['global']['output_path'],
        caseID=config['global']['experiment'],
        scripts_path=run_script_path,
        thread_list=kwargs['thread_list'],
        event=kwargs['kill_event'])
    runmanager.setup_job_sets(
        set_frequency=config['global']['set_frequency'],
        sim_start_year=sim_start_year,
        sim_end_year=sim_end_year,
        config=config,
        filemanager=filemanager)

    # Turning off the GUI for the time being
    # config['global']['ui'] = False if args.no_ui else True
    config['global']['ui'] = False
    config['global']['no_cleanup'] = True if args.no_cleanup else False
    config['global']['no_monitor'] = True if args.no_monitor else False
    config['global']['print_file_list'] = True if args.file_list else False

    logging.info('Starting run with config')
    logging.info(pformat(config))
    return config, filemanager, runmanager


def verify_config(config, template):
    messages = []
    valid = True
    for key, val in config.items():
        if key not in template:
            msg = '{key} is not a valid config option, is it misspelled?'.format(
                key=key)
            messages.append(msg)
            valid = False
    for key, val in template.items():
        if key not in config:
            msg = '{key} is missing from your config'.format(key=key)
            messages.append(msg)
            valid = False
        for item in val:
            if not config.get(key):
                msg = '{key} requires {val} but it is missing from your config'.format(
                    key=key, val=item)
                messages.append(msg)
                valid = False
                continue
            if item not in config[key]:
                msg = '{key} requires {val} but it is missing from your config'.format(
                    key=key, val=item)
                messages.append(msg)
                valid = False
    return valid, messages


def finishup(config, job_sets, state_path, event_list, status, display_event, thread_list, kill_event):
    message = 'Performing post run cleanup'
    event_list.push(message=message)
    if not config.get('global').get('no_cleanup', False):
        print 'Not cleaning up temp directories'
    else:
        tmp = os.path.join(config['global']['output_path'], 'tmp')
        if os.path.exists(tmp):
            rmtree(tmp)

    message = 'All processing complete' if status == 1 else "One or more job failed"
    emailaddr = config.get('global').get('email')
    if emailaddr:
        event_list.push(
            message='Sending notification email to {}'.format(emailaddr))
        try:
            if status == 1:
                msg = 'Post processing for {exp} has completed successfully\n'.format(
                    exp=config['global']['experiment'])
            else:
                msg = 'One or more job(s) for {exp} failed\n\n'.format(
                    exp=config['global']['experiment'])

            for job_set in job_sets:
                msg += '\nYearSet {start}-{end}: {status}\n'.format(
                    start=job_set.set_start_year,
                    end=job_set.set_end_year,
                    status=job_set.status)
                for job in job_set.jobs:
                    if job.status == JobStatus.COMPLETED:
                        if job.config.get('host_url'):
                            msg += '    > {job} - COMPLETED  :: output hosted :: {url}\n'.format(
                                url=job.config['host_url'],
                                job=job.type)
                        else:
                            msg += '    > {job} - COMPLETED  :: output located :: {output}\n'.format(
                                output=job.output_path,
                                job=job.type)
                    elif job.status in [JobStatus.FAILED, JobStatus.CANCELLED]:
                        output_path = os.path.join(
                            job.config['run_scripts_path'],
                            '{job}_{start:04d}_{end:04d}.out'.format(
                                job=job.type,
                                start=job.start_year,
                                end=job.end_year))
                        msg += '    > {job} - {status} :: console output :: {output}\n'.format(
                            output=output_path,
                            job=job.type,
                            status=job.status)
                    else:
                        msg += '    > {job} - {state}\n'.format(
                            job=job.type,
                            state=job.status)
                msg += '\n\n'

            m = Mailer(src='processflowbot@llnl.gov', dst=emailaddr)
            m.send(
                status=message,
                msg=msg)
        except Exception as e:
            print_debug(e)
    event_list.push(message=message)
    display_event.set()
    print_type = 'ok' if status == 1 else 'error'
    print_message(message, print_type)
    logging.info("All processes complete")
    for t in thread_list:
        kill_event.set()
        t.join(timeout=1.0)
    time.sleep(2)


def check_config_white_space(filepath):
    line_index = 0
    found = False
    with open(filepath, 'r') as infile:
        for line in infile.readlines():
            line_index += 1
            index = line.find('=')
            if index == -1:
                found = False
                continue
            if line[index + 1] != ' ':
                found = True
                break
    if found:
        return line_index
    else:
        return 0
