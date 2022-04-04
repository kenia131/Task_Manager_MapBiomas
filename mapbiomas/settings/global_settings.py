import os

DATABASE = {
    'ENGINE': 'postgresql',
    'NAME': os.environ.get('DB_NAME', 'mapbiomas'),
    'USER': os.environ.get('DB_USER', 'mapbiomas'),
    'PASSWORD': os.environ.get('DB_PASSWORD', 'mapbiomas'),
    'HOST': os.environ.get('DB_HOST', 'localhost'),
    'PORT': os.environ.get('DB_PORT', 5432),
}

SERVICE_ACCOUNT = {
    'ACCOUNT_NAME':  os.environ.get('SERVICE_ACCOUNT_NAME', ''),
    'ACCOUNT_KEY': os.environ.get('SERVICE_ACCOUNT_KEY', '')
}
