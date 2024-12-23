import subprocess


class PostgresDumper:
    """--dbname=postgresql://postgres@%2Frun%2Fpostgresql/pleroma"""

    def __init__(self, db_name: str):
        self.db_name = db_name
        self.user = "postgres"
        self.socket_dir = r"%2Frun%2Fpostgresql"

    def backup_database(self, backup_file: str):
        # Create the database dump and pipe it to gzip
        dump_command = [
            "pg_dump",
            f"--dbname=postgresql://{self.user}@{self.socket_dir}/{self.db_name}",
        ]
        gzip_command = ["gzip", "--rsyncable"]

        with open(backup_file, "wb") as f_out:
            dump_process = subprocess.Popen(dump_command, stdout=subprocess.PIPE)
            gzip_process = subprocess.Popen(
                gzip_command, stdin=dump_process.stdout, stdout=f_out
            )
            dump_process.stdout.close()  # Allow dump_process to receive a SIGPIPE if gzip_process exits
            gzip_process.communicate()

        return backup_file

    def restore_database(self, backup_file: str):
        # Decompress the backup file
        gunzip_command = ["gunzip", backup_file]
        subprocess.run(gunzip_command, check=True)

        # Restore the database from the decompressed file
        dump_file = backup_file.replace(".gz", "")
        restore_command = [
            "pg_restore",
            "--dbname=postgresql://{}@{}/{}".format(
                self.user, self.socket_dir, self.db_name
            ),
            "--clean",
            "--create",
            dump_file,
        ]
        subprocess.run(restore_command, check=True)
