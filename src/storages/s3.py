import aioboto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    ConnectionError,
    HTTPClientError,
)

from exceptions import (
    S3ConnectionError,
    S3FileDeleteError,
    S3FileUploadError,
)
from storages.interfaces import S3StorageInterface


class S3StorageClient(S3StorageInterface):
    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
    ) -> None:
        self._endpoint_url = endpoint_url
        self._bucket_name = bucket_name
        self._session = aioboto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
        )

    async def upload_file(
        self,
        file_name: str,
        file_data: bytes,
        content_type: str,
    ) -> None:
        try:
            async with self._session.client(
                service_name="s3",
                endpoint_url=self._endpoint_url,
            ) as client:
                await client.put_object(
                    Bucket=self._bucket_name,
                    Key=file_name,
                    Body=file_data,
                    ContentType=content_type,
                )
        except (ConnectionError, HTTPClientError) as error:
            raise S3ConnectionError() from error
        except (BotoCoreError, ClientError) as error:
            raise S3FileUploadError() from error

    async def get_file_url(self, file_name: str) -> str:
        endpoint = self._endpoint_url.rstrip("/")
        return f"{endpoint}/{self._bucket_name}/{file_name}"

    async def delete_file(self, file_name: str) -> None:
        try:
            async with self._session.client(
                service_name="s3",
                endpoint_url=self._endpoint_url,
            ) as client:
                await client.delete_object(
                    Bucket=self._bucket_name,
                    Key=file_name,
                )
        except (ConnectionError, HTTPClientError) as error:
            raise S3ConnectionError() from error
        except (BotoCoreError, ClientError) as error:
            raise S3FileDeleteError() from error
