import os
import sys
import threading
import logging
import re

from time import sleep
from peewee import *
from globus_cli.commands.ls import _get_ls_res as get_ls

from models import DataFile
from jobs.Transfer import Transfer
from jobs.JobStatus import JobStatus
from lib.YearSet import SetStatus
from lib.util import print_debug

filestatus = {
    'EXISTS': 0,
    'NOT_EXIST': 1,
    'IN_TRANSIT': 2
}


class FileManager(object):
    """
    Manage all files required by jobs
    """
    def __init__(self, database, types, sta=False, **kwargs):
        self.mutex = kwargs['mutex']
        self.sta = sta
        self.types = types
        self.active_transfers = 0
        self.db_path = database
        self.mutex.acquire()
        self.db = SqliteDatabase(database, threadlocals=True)
        self.db.connect()
        if DataFile.table_exists():
            DataFile.drop_table()
        DataFile.create_table()
        self.mutex.release()
        self.remote_endpoint = kwargs.get('remote_endpoint')
        self.local_path = kwargs.get('local_path')
        self.local_endpoint = kwargs.get('local_endpoint')
        self.search_paths = kwargs.get('search_paths')
        self.start_year = kwargs.get('start_year')
        self.alt_names = []
        self.alt_types = []

        # remove the trailing 'run' if its there
        head, tail = os.path.split(kwargs.get('remote_path'))
        if tail == 'run':
            self.remote_path = head
        else:
            self.remote_path = kwargs.get('remote_path')
        print 'remote_path ' + self.remote_path

    def __str__(self):
        return str({
            'short term archive': self.sta,
            'active_transfers': self.active_transfers,
            'remote_path': self.remote_path,
            'remote_endpoint': self.remote_endpoint,
            'local_path': self.local_path,
            'local_endpoint': self.local_endpoint,
            'db_path': self.db_path
        })

    def populate_file_list(self, simstart, simend, experiment):
        """
        Populate the database with the required DataFile entries

        Parameters:
            simstart (int): the start year of the simulation,
            simend (int): the end year of the simulation,
            types (list(str)): the list of file types to add, must be members of file_type_map,
            experiment (str): the name of the experiment 
                ex: 20170915.beta2.A_WCYCL1850S.ne30_oECv3_ICG.edison
        """
        print 'Creating file table'
        newfiles = []
        with self.db.atomic():
            for _type, _template in self.types.items():
                if _type == 'rest':
                    continue
                    # name = self.render_file_template(_template=_template, EXPERIMENT=experiment, YEAR=simstart+1)
                    # local_path = os.path.join(self.local_path, 'input', 'rest', name)
                    # if self.sta:
                    #     start_name = '{start:04d}-01-01-00000'.format(
                    #         start=simstart + 1)
                    # newfiles = self._add_file(
                    #     newfiles=newfiles,
                    #     name=name,
                    #     local_path=local_path,
                    #     _type=_type)
                elif _type == 'streams.ocean' or _type == 'streams.cice':
                    name = _type
                    local_path = local_path = os.path.join(
                        self.local_path,
                        'input',
                        'streams',
                        name)
                    newfiles = self._add_file(
                        newfiles=newfiles,
                        name=name,
                        local_path=local_path,
                        _type=_type)
                elif _type in ['atm', 'ice', 'ocn']:
                    for year in xrange(simstart, simend + 1):
                        for month in xrange(1, 13):
                            name = self.render_file_template(_template=_template, EXPERIMENT=experiment, YEAR=year, MONTH=month)
                            local_path = os.path.join(self.local_path, _type, name)
                            newfiles = self._add_file(
                                newfiles=newfiles,
                                name=name,
                                local_path=local_path,
                                _type=_type,
                                year=year,
                                month=month)
                else:
                    for year in xrange(simstart, simend + 1):
                        name = self.render_file_template(_template=_template, EXPERIMENT=experiment, YEAR=year, MONTH=month)
                        self.alt_names.append(name)
                        self.alt_types.append(_type)

            print 'Inserting file data into the table'
            self.mutex.acquire()
            try:
                step = 50
                for idx in range(0, len(newfiles), step):
                    DataFile.insert_many(newfiles[idx: idx + step]).execute()
            except Exception as e:
                print_debug(e)
            finally:
                self.mutex.release()
            print 'Database update complete'
    
    def render_file_template(self, _template, **kwargs):
        """
        Renders a file_type name template with the allowed keywords
        """
        keywords = ['EXPERIMENT', 'YEAR', 'MONTH']
        name = _template
        for key in keywords:
            if key == 'YEAR':
                keystr = '{key:04d}'.format(key=kwargs.get(key, 0))
            elif key == 'MONTH':
                keystr = '{key:02d}'.format(key=kwargs.get(key, 0))
            else:
                keystr = kwargs.get(key, '')
            name = name.replace(key, keystr)
        return name

    def _add_file(self, newfiles, **kwargs):
        local_status = filestatus['EXISTS'] \
            if os.path.exists(kwargs['local_path']) \
            else filestatus['NOT_EXIST']
        local_size = os.path.getsize(kwargs['local_path']) \
            if local_status == filestatus['EXISTS'] \
            else 0
        newfiles.append({
            'name': kwargs['name'],
            'local_path': kwargs['local_path'],
            'local_status': local_status,
            'remote_path': '',
            'remote_status': filestatus['NOT_EXIST'],
            'year': kwargs.get('year', 0),
            'month': kwargs.get('month', 0),
            'datatype': kwargs['_type'],
            'local_size': local_size,
            'remote_size': 0
        })
        return newfiles

    def update_remote_status(self, client):
        """
        Check remote location for existance of the files on our list
        If they exist, update their status in the DB

        Parameters:
            client (globus_sdk.client): the globus client to use for remote query
        """
        result = client.endpoint_autoactivate(self.remote_endpoint, if_expires_in=2880)
        if result['code'] == "AutoActivationFailed":
            return False
        names = [x.name for x in DataFile.select()]
        for path in self.search_paths:
            # if 'rest' in path:
            #     remote_path = path
            # elif path == 'run':
            #     remote_path = os.path.join(self.remote_path, path)
            # else:
            remote_path = os.path.join(self.remote_path, path)
            print 'Querying globus for {}'.format(remote_path)
            res = self._get_ls(
                client=client,
                path=remote_path)
            res = [x for x in res]
            resnames = [x['name'] for x in res]
            
            print 'got a response'
            try:
                new_name = []
                new_size = []
                new_path = []
                new_type = []
                for alt_index, alt_name in enumerate(self.alt_names):
                    for index, name in enumerate(resnames):
                        if re.search(pattern=alt_name, string=name):
                            new_name.append(name)
                            new_size.append(res[index]['size'])
                            new_path.append(os.path.join(remote_path, name))
                            new_type.append(self.alt_types[alt_index])

                if new_name:
                    print 'starting alt update'
                    newfiles = []
                    for index, item in enumerate(new_name):
                        local_path = os.path.join(self.local_path, new_type[index], new_name[index])
                        local_status = filestatus['EXISTS'] if os.path.exists(local_path) else filestatus['NOT_EXIST']
                        local_size = os.path.getsize(local_path) if os.path.exists(local_path) else 0
                        newfiles.append({
                            'name': item,
                            'local_path': local_path,
                            'local_status': local_status,
                            'remote_path': new_path[index],
                            'remote_status': filestatus['EXISTS'],
                            'year': 0,
                            'month': 0,
                            'datatype': new_type[index],
                            'local_size': local_size,
                            'remote_size': new_size[index]
                        })

                    self.mutex.acquire()
                    try:
                        step = 50
                        for idx in range(0, len(newfiles), step):
                            DataFile.insert_many(newfiles[idx: idx + step]).execute()
                    except Exception as e:
                        print_debug(e)
                    finally:
                        if self.mutex.locked():
                            self.mutex.release()

                if 'rest' in path:
                    to_update_name = [x for x in resnames if 'mpaso.rst' in x]
                    to_update_size = [x['size'] for x in res if 'mpaso.rst' in x['name']]
                    to_update_path = [os.path.join(remote_path, x) for x in to_update_name]
                    newfiles = []
                    for index, item in enumerate(to_update_name):
                        local_path = os.path.join(self.local_path, 'rest', to_update_name[index])
                        local_status = filestatus['EXISTS'] if os.path.exists(local_path) else filestatus['NOT_EXIST']
                        local_size = os.path.getsize(local_path) if os.path.exists(local_path) else 0
                        newfiles.append({
                            'name': item,
                            'local_path': local_path,
                            'local_status': local_status,
                            'remote_path': to_update_path[index],
                            'remote_status': filestatus['EXISTS'],
                            'year': 0,
                            'month': 0,
                            'datatype': 'rest',
                            'local_size': local_size,
                            'remote_size': to_update_size[index]
                        })

                    self.mutex.acquire()
                    try:
                        step = 50
                        for idx in range(0, len(newfiles), step):
                            DataFile.insert_many(newfiles[idx: idx + step]).execute()
                    except Exception as e:
                        print_debug(e)
                    finally:
                        if self.mutex.locked():
                            self.mutex.release()
                else:
                    to_update_name = [x for x in resnames if x in names]
                    to_update_size = [x['size'] for x in res if x['name'] in names]
                    to_update_path = [os.path.join(remote_path, x) for x in resnames if x in names]

                    self.mutex.acquire()
                    q = DataFile.update(
                        remote_status=filestatus['EXISTS'],
                        remote_path=to_update_path[to_update_name.index(DataFile.name)],
                        remote_size=to_update_size[to_update_name.index(DataFile.name)]
                    ).where(
                        (DataFile.name << to_update_name) &
                        (DataFile.name.not_in(new_name))
                    )
                    n = q.execute()
                    print '{} updated'.format(n)
            except Exception as e:
                print_debug(e)
                print "Do you have the correct start and end dates?"
            finally:
                print 'done with {} update'.format(path)
                if self.mutex.locked():
                    self.mutex.release()

    def _get_ls(self, client, path):
        for fail_count in xrange(10):
            try:
                res = get_ls(
                    client,
                    path,
                    self.remote_endpoint,
                    False, 0, False)
            except Exception as e:
                sleep(fail_count)
                if fail_count >= 9:
                    from lib.util import print_debug
                    print_debug(e)
                    sys.exit()
            else:
                return res

    def update_local_status(self):
        """
        Update the database with the local status of the expected files

        Parameters:
            types (list(str)): the list of files types to expect, must be members of file_type_map
        """

        self.mutex.acquire()
        try:
            datafiles = DataFile.select().where(
                DataFile.local_status == filestatus['NOT_EXIST'])
            for datafile in datafiles:
                if os.path.exists(datafile.local_path):
                    local_size = os.path.getsize(datafile.local_path)
                    if local_size == datafile.remote_size:
                        datafile.local_status = filestatus['EXISTS']
                        datafile.local_size = local_size
                        datafile.save()
        except Exception as e:
            print_debug(e)
        finally:
            self.mutex.release()

    def all_data_local(self):
        self.mutex.acquire()
        try:
            for data in DataFile.select():
                if data.local_status != filestatus['EXISTS']:
                    return False
        except Exception as e:
            print_debug(e)
        finally:
            self.mutex.release()
        return True

    def transfer_needed(self, event_list, event, remote_endpoint, ui, display_event, emailaddr, thread_list):
        """
        Start a transfer job for any files that arent local, but do exist remotely

        Globus user must already be logged in

        Parameters:
            event_list (EventList): the list to push information into
            event (threadding.event): the thread event to trigger a cancel
        """
        if self.active_transfers >= 2:
            return False
        # required files dont exist locally, do exist remotely
        # or if they do exist locally have a different local and remote size
        self.mutex.acquire()
        try:
            required_files = [x for x in DataFile.select().where(
                (DataFile.remote_status == filestatus['EXISTS']) &
                (DataFile.local_status != filestatus['IN_TRANSIT']) &
                ((DataFile.local_status == filestatus['NOT_EXIST']) |
                 (DataFile.local_size != DataFile.remote_size))
            )]
            target_files = []
            target_size = 1e11 # 100 GB
            total_size = 0
            for file in required_files:
                if total_size + file.remote_size < target_size:
                    target_files.append({
                        'name': file.name,
                        'local_size': file.local_size,
                        'local_path': file.local_path,
                        'local_status': file.local_status,
                        'remote_size': file.remote_size,
                        'remote_path': file.remote_path,
                        'remote_status': file.remote_status
                    })
                    total_size += file.remote_size
                else:
                    break
        except Exception as e:
            print_debug(e)
        finally:
            self.mutex.release()

        logging.info('Transfering required files')
        print 'total transfer size {size} for {nfiles} files'.format(
            size=total_size,
            nfiles=len(target_files))
        transfer_config = {
            'file_list': target_files,
            'source_endpoint': self.remote_endpoint,
            'destination_endpoint': self.local_endpoint,
            'source_path': self.remote_path,
            'destination_path': self.local_path,
            'src_email': emailaddr,
            'display_event': display_event,
            'ui': ui,
        }
        transfer = Transfer(
            config=transfer_config,
            event_list=event_list)
        print 'staring transfer for:'
        transfer_names = [x['name'] for x in transfer.file_list]
        for file in transfer.file_list:
            print file['name']
            logging.info(file['name'])
        self.mutex.acquire()
        try:
            print 'should be updating local status'
            DataFile.update(
                local_status=filestatus['IN_TRANSIT']
            ).where(
                DataFile.name << transfer_names
            ).execute()
            print 'following files are in transit'
            for df in DataFile.select():
                if df.local_status == filestatus['IN_TRANSIT']:
                    print df.name
        except Exception as e:
            print_debug(e)
        finally:
            self.mutex.release()
        args = (transfer, event, event_list)
        thread = threading.Thread(
            target=self._handle_transfer,
            name='filemanager_transfer',
            args=args)
        thread_list.append(thread)
        thread.start()
        return True

    def _handle_transfer(self, transfer, event, event_list):
        self.active_transfers += 1
        event_list.push(message='Starting file transfer')
        transfer.execute(event)
        print 'Transfer complete'
        self.active_transfers -= 1

        if transfer.status == JobStatus.FAILED:
            message = "Transfer has failed"
            logging.error(message)
            event_list.push(message='Tranfer failed')
            return

        print 'Updating table with new files info'
        self.mutex.acquire()
        names = [x['name'] for x in transfer.file_list]
        for datafile in DataFile.select().where(DataFile.name << names):
            if os.path.exists(datafile.local_path) \
            and os.path.getsize(datafile.local_path) == datafile.remote_size:
                datafile.local_status = filestatus['EXISTS']
                datafile.local_size = os.path.getsize(datafile.local_path)
            else:
                datafile.local_status = filestatus['NOT_EXIST']
                datafile.local_size = 0
            datafile.save()
        try:
            self.mutex.release()
        except:
            pass
        print 'table update complete'


    def years_ready(self, start_year, end_year):
        """
        Checks if atm files exist from start year to end of endyear

        Parameters:
            start_year (int): the first year to start checking
            end_year (int): the last year to check for
        Returns:
            -1 if no data present
            0 if partial data present
            1 if all data present
        """
        data_ready = True
        non_zero_data = False

        self.mutex.acquire()
        try:
            datafiles = DataFile.select().where(
                (DataFile.datatype == 'atm') &
                (DataFile.year >= start_year) &
                (DataFile.year <= end_year))
            for datafile in datafiles:
                if datafile.local_status in [filestatus['NOT_EXIST'], filestatus['IN_TRANSIT']]:
                    data_ready = False
                else:
                    non_zero_data = True
        except Exception as e:
            print_debug(e)
        finally:
            self.mutex.release()

        if data_ready:
            return 1
        elif not data_ready and non_zero_data:
            return 0
        elif not data_ready and not non_zero_data:
            return -1

    def get_file_paths_by_year(self, start_year, end_year, _type):
        self.mutex.acquire()
        try:
            if _type in ['rest', 'streams.ocean', 'streams.cice']:
                datafiles = Datafile.select().where(DataFile.datatype == _type)
            else:
                datafiles = DataFile.select().where(
                    (DataFile.datatype == _type) &
                    (DataFile.year >= start_year) &
                    (DataFile.year <= end_year))
            files = [x.local_path for x in datafiles]
        except Exception as e:
            print_debug(e)
        finally:
            self.mutex.release()
        return files


    def check_year_sets(self, job_sets):
        """
        Checks the file_list, and sets the year_set status to ready if all the files are in place,
        otherwise, checks if there is partial data, or zero data
        """
        incomplete_job_sets = [s for s in job_sets
                            if s.status != SetStatus.COMPLETED
                            and s.status != SetStatus.RUNNING
                            and s.status != SetStatus.FAILED]

        for job_set in incomplete_job_sets:
            data_ready = self.years_ready(
                start_year=job_set.set_start_year,
                end_year=job_set.set_end_year)

            if data_ready == 1:
                if job_set.status != SetStatus.DATA_READY:
                    job_set.status = SetStatus.DATA_READY
                    print "{start:04d}-{end:04d} is ready".format(
                        start=job_set.set_start_year,
                        end=job_set.set_end_year)
            elif data_ready == 0:
                if job_set.status != SetStatus.PARTIAL_DATA:
                    job_set.status = SetStatus.PARTIAL_DATA
                    print "{start:04d}-{end:04d} has partial data".format(
                        start=job_set.set_start_year,
                        end=job_set.set_end_year)
            elif data_ready == -1:
                if job_set.status != SetStatus.NO_DATA:
                    job_set.status = SetStatus.NO_DATA
                    print "{start:04d}-{end:04d} has no data".format(
                        start=job_set.set_start_year,
                        end=job_set.set_end_year)

    def print_db(self):
        self.mutex.acquire()
        for df in DataFile.select():
            print {
                'name': df.name,
                'local_path': df.local_path,
                'remote_path': df.remote_path
            }
        self.mutex.release()
