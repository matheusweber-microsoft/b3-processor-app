class BlobFileDoesntExistsError(Exception):
    def __init__(self):
        super().__init__(f"""Blob file doesnt exists in storage container.""")