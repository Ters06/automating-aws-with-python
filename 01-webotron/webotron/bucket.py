# -*- coding: utf-8 -*-

"""Classes for s3 Buckets."""

class BucketManager:
    """Manage an s3 Bucket."""

    def __init__(self, session):
        """Create a BucketManager object."""
        self.s3 = session.resource('s3')

    def all_buckets(self):
        """Get an iterator for all buckets."""
        return self.s3.buckets.all()

    def all_objects(self, bucket):
        """Get all objects in a bucket."""
        return self.s3.Bucket(bucket).objects.all()
