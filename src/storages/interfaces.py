from abc import ABC, abstractmethod


class S3StorageInterface(ABC):
    @abstractmethod
    async def upload_file(
        self,
        file_name: str,
        file_data: bytes,
        content_type: str,
    ) -> None:
        """Upload file contents using the specified storage key."""
        pass

    @abstractmethod
    async def get_file_url(self, file_name: str) -> str:
        """Return a URL for accessing the stored file."""
        pass

    @abstractmethod
    async def delete_file(self, file_name: str) -> None:
        """Delete an object using its storage key."""
        pass
