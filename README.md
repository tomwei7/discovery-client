# discovery-client

python client for discovery https://github.com/bilibili/discovery only support python3.

### Install

```bash
pip install python-discovery-client
```

### Usage

```python
from discovery import config_from_env, Client


# register instance
client = Client(config_from_env('127.0.0.1:7771')) # use you discovery domain
client.register('your app name', ['http://127.0.0.1:8000'])

# watch instance
def watch_callback(instances):
    print('instance change: %s', instances)

client.watch('your app name', watch_callback)

client.stop()
```
