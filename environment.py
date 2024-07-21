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
    
    return consumer_key, consumer_secret, access_token, access_token_secret, client_id, client_secret, tinyurl_token

# Example usage


home_dir = str(Path.home())
config_file_path = os.path.join(home_dir,'tldr_app_config.ini')
consumer_key, consumer_secret, access_token, \
access_token_secret, client_id, client_secret, tinyurl_token = read_config(config_file_path)

# Print the variables to verify (remove or comment out in production)
print(f"Consumer Key: {consumer_key}")
print(f"Consumer Secret: {consumer_secret}")
print(f"Access Token: {access_token}")
print(f"Access Token Secret: {access_token_secret}")
print(f"Client ID: {client_id}")
print(f"Client Secret: {client_secret}")
