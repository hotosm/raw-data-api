"""
s3.py

This module provides an asynchronous S3 file transfer class, `AsyncS3FileTransfer`, which can be used to list S3 buckets, get bucket locations, and upload files to S3 asynchronously.

Usage:

1. Import the `AsyncS3FileTransfer` class:
    from s3 import AsyncS3FileTransfer

2. Create an instance of the `AsyncS3FileTransfer` class:
    s3_transfer = AsyncS3FileTransfer()

3. List S3 buckets:
    buckets = await s3_transfer.list_buckets()
    print(buckets)

4. Get bucket location:
    bucket_location = await s3_transfer.get_bucket_location('my-bucket')
    print(bucket_location)

5. Upload a file to S3:
    file_url = await s3_transfer.upload("path/to/local/file.csv", "remote_file_name", file_suffix="csv")
    print(file_url)

Example:

import asyncio

async def main():
    s3_transfer = AsyncS3FileTransfer()

    # List buckets
    buckets = await s3_transfer.list_buckets()
    print(buckets)

    # Upload a file
    file_url = await s3_transfer.upload("path/to/local/file.csv", "remote_file_name", file_suffix="csv")
    print(file_url)

asyncio.run(main())
"""

# Standard library imports
import logging
import time

# Third party imports
import aioboto3

# Reader imports
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, BUCKET_NAME


class AsyncS3FileTransfer:
    """Responsible for the asynchronous file transfer to S3 from the API machine."""

    def __init__(self):
        # Responsible for the connection
        try:
            if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
                self.aws_session = aioboto3.Session(
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                )
            else:  # If it is not passed on config, then the API will assume it is configured within the machine using the credentials file
                self.aws_session = aioboto3.Session()
            self.s3 = self.aws_session.client("s3")
            logging.debug("Connection has been successful to S3")
        except Exception as ex:
            logging.error(ex)
            raise ex

    async def list_buckets(self):
        """Used to list all the buckets available on S3."""
        async with self.s3 as s3:
            buckets = await s3.list_buckets()
            return buckets

    async def get_bucket_location(self, bucket_name):
        """Provides the bucket location on AWS, takes bucket_name as a string -- name of the repo on S3."""
        try:
            async with self.s3 as s3:
                bucket_location = await s3.get_bucket_location(Bucket=bucket_name)
                return bucket_location.get("LocationConstraint", "us-east-1")
        except Exception as ex:
            logging.error("Can't access bucket location")
            raise ex

    async def upload(self, file_path, file_name, file_suffix=None):
        """Used for transferring a file to S3 after reading the path from the user. It will wait for the upload to complete.

        Parameters:
            file_path (str): Your local file path to upload.
            file_name (str): The filename to be stored on S3.
            file_suffix (str, optional): The file extension to be added to the filename.

        Returns:
            str: The URL of the uploaded file on S3.

        Example:
            url = await s3_transfer.upload("exports", "upload_test", file_suffix="csv")
        """
        if file_suffix:
            file_name = f"{file_name}.{file_suffix}"

        logging.debug("Started Uploading %s from %s", file_name, file_path)

        # Instantiate upload
        start_time = time.time()
        try:
            async with self.s3 as s3:
                await s3.upload_file(str(file_path), BUCKET_NAME, str(file_name))
        except Exception as ex:
            logging.error(ex)
            raise ex

        logging.debug("Uploaded %s in %s sec", file_name, time.time() - start_time)

        # Generate the download URL
        bucket_location = await self.get_bucket_location(bucket_name=BUCKET_NAME)
        object_url = (
            f"https://s3.{bucket_location}.amazonaws.com/{BUCKET_NAME}/{file_name}"
        )

        return object_url
