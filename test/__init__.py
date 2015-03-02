from collections import namedtuple

FakeConfig = namedtuple(
    'FakeConfig',
    [
        'base_page_url', 
        'elasticsearch_url', 
        'site_map_directory_path', 
        'site_map_directory_url', 
        'page_size',
        'url_change_frequency', 
        'scroll_expiry', 
        'request_timeout', 
        'base_site_map_filename',
        'site_map_index_filename', 
        'max_urls_per_file', 
        'file_encoding', 
        'es_index', 
        'es_doc_type',
     ]
)
