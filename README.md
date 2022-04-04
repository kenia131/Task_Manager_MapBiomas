## Install Google Cloud SDK

https://cloud.google.com/sdk/docs/#deb

```
$ export CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)"
$ echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
$ curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
$ sudo apt-get update && sudo apt-get install google-cloud-sdk
$ gcloud init 
$ gcloud auth application-default login
```

## Create a virtual environment
```
$ pip install virtualenv
$ virtualenv env -p python3
$ source env/bin/activate
```

## Install requirements
```
$ pip3 install -r requirements.txt
```

## Earth Engine Authenticate
```
$ earthengine authenticate
```

## Install postgres:
```
$ sudo apt-get install postgresql
$ sudo -u postgres psql
$ \password postgres
# \q 
```

## Create a database
```
$ psql -U postgres -W -h localhost
$ create database mapbiomas;
#\q
```


## Initialize database:
```
>> python3 manage.py migrate
```

## To use client API, install ImageTk

```
sudo apt-get install python-imaging-tk
```

## Create your settings or use an existing

change "mapbiomas/settings/__init__.py" to choose the settings.

## Execute

```
>> python3 manager.py run
```