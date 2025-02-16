from abc import ABC, abstractmethod

from selfprivacy_api.models.email_password_metadata import EmailPasswordMetadata


class AbstractEmailPasswordManager(ABC):
    @staticmethod
    @abstractmethod
    def get_all_email_passwords_matadata(username: str) -> list[EmailPasswordMetadata]:
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
    def add_new_email_password(
        username: str, password_hash: str, credential_metadata: EmailPasswordMetadata
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
    def delete_email_password(username: str, uuid: str) -> None:
        """
        Remove a stored email password with its metadata
        for a given user by its unique identifier.

        Args:
            username (str)
            uuid (str): The unique identifier of the password entry to be removed.
        """
