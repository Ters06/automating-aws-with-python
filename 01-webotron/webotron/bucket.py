# -*- coding: utf-8 -*-
"""Classes for s3 Buckets."""

from pathlib import Path
import mimetypes

import boto3
from botocore.exceptions import ClientError

from functools import reduce
from hashlib import md5
import util


class BucketManager:
    """Manage an s3 Bucket."""

    CHUNCK_SIZE = 8388608

    def __init__(self, session):
        """Create a BucketManager object."""
        self.session = session
        self.s3 = self.session.resource('s3')
        self.transfer_config = boto3.s3.transfer.TransferConfig(
            multipart_chunksize=self.CHUNCK_SIZE,
            multipart_threshold=self.CHUNCK_SIZE
        )
        self.manifest = {}

    def get_region_name(self, bucket):
        """Get the bucket's region name."""
        bucket_location = self.s3.meta.client.\
            get_bucket_location(Bucket=bucket.name)

        return bucket_location["LocationConstraint"] or 'us-east-1'

    def get_bucket(self, bucket_name):
        """Get a bucket by name."""
        return self.s3.Bucket(bucket_name)

    def get_bucket_url(self, bucket):
        """Get the website URL for this bucket."""
        return "http://{}.{}".\
            format(bucket.name,
                   util.get_endpoint(self.get_region_name(bucket)).host)

    def all_buckets(self):
        """Get an iterator for all buckets."""
        return self.s3.buckets.all()

    def all_objects(self, bucket_name):
        """Get all objects in a bucket."""
        return self.s3.Bucket(bucket_name).objects.all()

    def init_bucket(self, bucket_name):
        """Create new bucket, or return existing one by name."""
        try:
            s3_bucket = self.s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': self.session.region_name
                }
            )
        except ClientError as error:
            if error.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                s3_bucket = self.s3.Bucket(bucket_name)
            else:
                raise error

        return s3_bucket

    @staticmethod
    def set_policy(bucket):
        """Set bucket policy to be readable by everyone."""
        policy = """
        {
            "Version":"2012-10-17",
            "Statement":[{
                "Sid":"PublicReadGetObject",
                "Effect":"Allow",
                "Principal": "*",
                    "Action":["s3:GetObject"],
                    "Resource":["arn:aws:s3:::%s/*"]
                }]
        }
        """ % bucket.name

        bucket.Policy().put(Policy=policy.strip())

    @staticmethod
    def configure_website(bucket):
        """Configure s3 website hosting for bucket."""
        bucket.Website().put(WebsiteConfiguration={
            'ErrorDocument': {
                'Key': 'error.html'
            },
            'IndexDocument': {
                'Suffix': 'index.html'
            }
        })

    def load_manifest(self, bucket):
        """Load manifest for caching purposes."""
        paginator = self.s3.meta.client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket.name):
            for obj in page.get('Contents', []):
                self.manifest[obj['Key']] = obj['ETag']

    @staticmethod
    def has_data(data):
        """Generate md5 hash for data."""
        hash = md5()
        hash.update(data)

        return hash

    def gen_etag(self, path):
        """Generate ETag for file."""
        hashes = []

        with open(path, 'rb') as f:
            while True:
                data = f.read(self.CHUNCK_SIZE)

                if not data:
                    break

                hashes.append(self.has_data(data))

        if not hashes:
            return
        elif len(hashes) == 1:
            return '"{}"'.format(hashes[0].hexdigest())
        else:
            hash = self.has_data(
                reduce(lambda x, y: x + y, (h.digest() for h in hashes))
            )
            return '"{}-{}"'.format(hash.hexdigest(), len(hashes))

    def upload_file(self, bucket, path, key):
        """Upload path to s3_bucket at key."""
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'

        etag = self.gen_etag(path)
        if self.manifest.get(key, '') == etag:
            print("Skipping {}, etags match".format(key))
            return
        return bucket.upload_file(
            path,
            key,
            ExtraArgs={
                'ContentType': content_type
            },
            Config=self.transfer_config
        )

    @staticmethod
    def remove_keys(bucket, keys):
        """Remove objects by key."""
        to_delete = {'Objects': []}
        for key in keys:
            to_delete['Objects'].append({
                'Key': key
            })

        return bucket.delete_objects(Delete=to_delete)

    def sync(self, pathname, bucket_name):
        """Sync contents of the website to the bucket."""
        bucket = self.s3.Bucket(bucket_name)
        self.load_manifest(bucket)

        root = Path(pathname).expanduser().resolve()

        keys_to_remove = list(self.manifest.keys())

        def handle_directory(target):
            for p in target.iterdir():
                if p.is_dir():
                    handle_directory(p)
                if p.is_file():
                    if p.relative_to(root).as_posix() in keys_to_remove:
                        keys_to_remove.remove(p.relative_to(root).as_posix())
                    self.upload_file(
                        bucket,
                        str(p),
                        str(p.relative_to(root).as_posix())
                    )

        handle_directory(root)

        if keys_to_remove:
            self.remove_keys(bucket, keys_to_remove)
