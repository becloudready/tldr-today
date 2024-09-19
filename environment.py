import configparser
from pathlib import Path
import os

def read_config(file_path):
    # Initialize the configparser
    config = configparser.ConfigParser()
    
    # Read the configuration file
    config.read(file_path)
    
    # Access the variables in the [DEFAULT] section
    consumer_key = config['DEFAULT'].get('consumer_key', '')
    consumer_secret = config['DEFAULT'].get('consumer_secret', '')
    access_token = config['DEFAULT'].get('access_token', '')
    access_token_secret = config['DEFAULT'].get('access_token_secret', '')
    client_id = config['DEFAULT'].get('client_id', '')
    client_secret = config['DEFAULT'].get('client_secret', '')
    tinyurl_token = config['DEFAULT'].get('tinyurl_token', '')
    shorturl_token = config['DEFAULT'].get('shorturl_token', '')
    
    return consumer_key, consumer_secret, access_token, access_token_secret, client_id, client_secret, tinyurl_token, shorturl_token

# Example usage


home_dir = str(Path.home())
config_file_path = os.path.join(home_dir,'tldr_app_config.ini')
consumer_key, consumer_secret, access_token, \
access_token_secret, client_id, client_secret, tinyurl_token, shorturl_token = read_config(config_file_path)


