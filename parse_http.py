from urllib.parse import urlparse, urlunparse

def convert_http_to_https(url):
    parsed_url = urlparse(url)
    
    if parsed_url.scheme == 'http':
        https_url = parsed_url._replace(scheme='https')
        return urlunparse(https_url)
    else:
        # The URL is already using HTTPS, so return it as is.
        return url

