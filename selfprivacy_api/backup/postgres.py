import subprocess


class PostgresDumper:
    """--dbname=postgresql://postgres@%2Frun%2Fpostgresql/pleroma"""

    def __init__(self, db_name: str):
        self.db_name = db_name
        self.user = "postgres"
        self.socket_dir = r"%2Frun%2Fpostgresql"

    def backup_database(self, backup_file: str):
        # Create the database dump in custom format
        dump_command = [
            "pg_dump",
            f"--dbname=postgresql://{self.user}@{self.socket_dir}/{self.db_name}",
            "--format=custom",
            f"--file={backup_file}",
        ]

        subprocess.run(dump_command, check=True)

        return backup_file

    def restore_database(self, backup_file: str):
        restore_command = [
            "pg_restore",
            f"--dbname=postgresql://{self.user}@{self.socket_dir}",
            "--clean",
            "--create",
            "--exit-on-error",
            backup_file,
        ]
        subprocess.run(restore_command, check=True)
