# coding: utf-8
import csv
import os
import re
import sys
import time

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.files.storage import get_storage_class, FileSystemStorage
from django.db.models import Value as V
from django.db.models.functions import Concat

from onadata.apps.logger.models import Attachment
from onadata.apps.viewer.models import Export


class Command(BaseCommand):
    help = 'Removes orphan files on storage'
    args = '[username]'

    def __init__(
        self, stdout=None, stderr=None, no_color=False, force_color=False
    ):
        super().__init__(stdout, stderr, no_color, force_color)
        self._orphans = 0
        self._size_to_reclaim = 0
        self._csv_filepath = '/srv/logs/orphan_files-{}.csv'.format(
            int(time.time())
        )

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)

        parser.add_argument('username', nargs='?', default=None)

        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Do not delete files',
        )

        parser.add_argument(
            '--save-as-csv',
            action='store_true',
            default=False,
            help='Save deleted files to a CSV file',
        )

        parser.add_argument(
            '--calculate-size',
            action='store_true',
            default=False,
            help=(
                'Calculate total size reclaimed on storage.\n'
                'Warning, it produces lots of `HEAD` (billed) requests to AWS S3'
            )
        )

    def handle(self, *args, **options):

        dry_run = options['dry_run']
        save_as_csv = options['save_as_csv']
        calculate_size = options['calculate_size']
        username = options['username']

        self._storage_manager = StorageManager(username, calculate_size)
        all_files = self._storage_manager.get_files()

        if dry_run:
            self.stdout.write('Dry run mode activated')

        if save_as_csv:
            with open(self._csv_filepath, 'w', newline='') as csvfile:
                writer = csv.DictWriter(
                    csvfile, fieldnames=['type', 'filepath', 'filesize']
                )
                writer.writeheader()

        for absolute_filepath in all_files:
            try:
                if not absolute_filepath.endswith('/'):
                    filepath = self._storage_manager.get_path_from_storage(
                        absolute_filepath
                    )
                    if re.match(r'[^\/]*\/attachments\/[^\/]*\/[^\/]*\/.+', filepath):
                        clean_filepath = filepath
                        for auto_suffix in ['-large', '-medium', '-small']:
                            filename, extension = os.path.splitext(
                                os.path.basename(filepath)
                            )
                            # Find real name saved in DB
                            if filename[-len(auto_suffix):] == auto_suffix:
                                clean_filepath = (
                                    filepath[:-(len(auto_suffix) + len(extension))]
                                    + extension
                                )
                                break

                        if not Attachment.objects.filter(
                            media_file=clean_filepath
                        ).exists():
                            self.delete('attachment', absolute_filepath, options)

                    elif re.match(r'[^\/]*\/exports\/[^\/]*\/[^\/]*\/.+', filepath):
                        # KoBoCAT exports
                        if (
                            not Export.objects.annotate(
                                fullpath=Concat('filedir', V('/'), 'filename')
                            )
                            .filter(fullpath=filepath)
                            .exists()
                        ):
                            self.delete('export', absolute_filepath, options)

            except Exception as e:
                self.stderr.write(f'ERROR - {str(e)}')
                sys.exit(1)

        self.stdout.write(f'Orphans: {self._orphans}')
        if calculate_size:
            self.stdout.write(f'Free up space: {self.sizeof_fmt(self._size_to_reclaim)}')
        if save_as_csv:
            self.stdout.write(f'CSV saved at {self._csv_filepath}')

    def delete(self, orphan_type: str, absolute_filepath: str, options: dict):

        # Get size of the file
        filesize = self._storage_manager.get_filesize(absolute_filepath)
        filepath = self._storage_manager.get_path_from_storage(absolute_filepath)
        self._orphans += 1
        self._size_to_reclaim += filesize

        if options['save_as_csv']:
            with open(self._csv_filepath, 'a') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([orphan_type, filepath, filesize])

        if options['verbosity'] > 1:
            self.stdout.write(
                f'Found {orphan_type}: {filepath} - {self.sizeof_fmt(filesize)}'
            )

        if options['dry_run']:
            return

        try:
            self._storage_manager.delete(absolute_filepath)
            if options['verbosity'] > 1:
                self.stdout.write('\tDeleted!')

        except Exception as e:
            self.stderr.write(
                f'ERROR - Could not delete file {filepath} - Reason {str(e)}'
            )

    @staticmethod
    def sizeof_fmt(num, suffix='B'):
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)


class StorageManager:

    def __init__(self, username: str, calculate_size: bool):
        self._calculate_size = calculate_size
        self._username = username
        self._storage = get_storage_class()()
        self._is_local = isinstance(self._storage, FileSystemStorage)
        if not self._is_local:
            self._s3_client = boto3.client('s3')

    def delete(self, absolute_filepath: str):
        if self._is_local:
            os.remove(absolute_filepath)
        else:
            # Be aware, it does not delete all versions of the file.
            # It relies on S3 LifeCyle rules to delete old versions.
            self._s3_client.Object(
                settings.AWS_STORAGE_BUCKET_NAME, absolute_filepath
            ).delete()

    def get_files(self):
        if self._is_local:
            dest = (
                f'{settings.MEDIA_ROOT}/{self._username}'
                if self._username
                else settings.MEDIA_ROOT
            )
            for root, dirs, files in os.walk(dest):
                for name in files:
                    yield os.path.join(root, name)
        else:
            s3_paginator = self._s3_client.get_paginator('list_objects_v2')
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            prefix = self._username if self._username else ''
            for page in s3_paginator.paginate(
                Bucket=bucket_name, Prefix=prefix, StartAfter=''
            ):
                for content in page.get('Contents', ()):
                    yield content['Key']

    def get_filesize(self, absolute_filepath: str):
        if not self._calculate_size:
            return 0

        if self._is_local:
            return os.path.getsize(absolute_filepath)
        else:
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            response = self._s3_client.head_object(
                Bucket=bucket_name, Key=absolute_filepath
            )
            return response['ContentLength']

    def get_path_from_storage(self, absolute_filepath: str) -> str:
        if self._is_local:
            return absolute_filepath.replace(settings.MEDIA_ROOT, '')
        else:
            return absolute_filepath

    @property
    def storage(self):
        return self._storage
