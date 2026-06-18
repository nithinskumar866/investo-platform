from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MinioStorage(S3Boto3Storage):
    """MinIO S3-compatible storage backend.

    Maps MINIO_* settings from Django settings to S3Boto3Storage
    configuration. All FileFields and ImageFields use this backend
    by default via DEFAULT_FILE_STORAGE.
    """

    endpoint_url = settings.MINIO_ENDPOINT
    access_key = settings.MINIO_ACCESS_KEY
    secret_key = settings.MINIO_SECRET_KEY
    bucket_name = settings.MINIO_BUCKET_NAME
    use_ssl = settings.MINIO_USE_SSL
    default_acl = "private"
    file_overwrite = False
    querystring_auth = True
    querystring_expire = 600  # 10 minutes

    # Map MINIO settings to S3Boto3Storage's internal config
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bucket = None

    def url(self, name, parameters=None, expire=None):
        """Generate a signed URL for private file access.

        Uses MINIO_URL_EXPIRY from settings (default 3600s).
        Pass expire=None to use querystring_expire.
        """
        expire = expire or getattr(
            settings, "MINIO_URL_EXPIRY", self.querystring_expire,
        )
        return super().url(name, parameters=parameters, expire=expire)
