from abc import ABC, abstractmethod

from selfprivacy_api.models.email_password_metadata import EmailPasswordData


class AbstractEmailPasswordManager(ABC):
    @staticmethod
    @abstractmethod
    def get_all_email_passwords_matadata(
        username: str,
        with_passwords_hashes: bool = False,
    ) -> list[EmailPasswordData]:
        """
        Retrieve metadata of all stored email passwords for a given user.

        Args:
            username (str)

        Returns:
            List[EmailPasswordMetadata]:
                A list of metadata objects containing details
                about stored passwords. Without hashed password.
        """

    @staticmethod
    @abstractmethod
    def add_email_password_hash(
        username: str, password_hash: str, credential_metadata: EmailPasswordData
    ) -> None:
        """
        Store a new email password along with its metadata for a given user.

        Args:
            username (str)
            password_hash (str): The hashed password value.
            credential_metadata (EmailPasswordMetadata):
                Metadata associated with the password,
                including display name and timestamps.
        """

    @staticmethod
    @abstractmethod
    def delete_email_password_hash(username: str, uuid: str) -> None:
        """
        Remove a stored email password with its metadata
        for a given user by its unique identifier.

        Args:
            username (str)
            uuid (str): The unique identifier of the password entry to be removed.
        """

    @staticmethod
    def delete_all_email_passwords_hashes(username: str) -> None:
        """
        Remove all stored email passwords along with their metadata
        for a specified user.

        Args:
            username (str): The username whose email passwords should be deleted.
        """
