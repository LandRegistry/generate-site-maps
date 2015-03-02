import argparse

def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='Creates site map files based on Elasticsearch data')

    _add_base_page_url_arg(parser)
    _add_elasticsearch_url_arg(parser)
    _add_site_map_directory_path_arg(parser)
    _add_site_map_directory_url_arg(parser)
    _add_page_size_arg(parser)
    _add_url_change_frequency_arg(parser)
    _add_scroll_expiry_arg(parser)
    _add_request_timeout_arg(parser)
    _add_base_filename_arg(parser)
    _add_index_filename_arg(parser)
    _add_max_records_per_file_arg(parser)
    _add_file_encoding_arg(parser)
    _add_logging_config_file(parser)
    _add_es_index_name(parser)
    _add_es_doc_type(parser)

    return parser.parse_args()

def _add_base_page_url_arg(parser):
    parser.add_argument(
        '--basePageUrl',
        help='Base URL for property pages',
        dest='base_page_url',
        required=True,
    )

def _add_elasticsearch_url_arg(parser):
    parser.add_argument(
        '--elasticsearchUrl',
        help='URL of the Elasticsearch instance',
        dest='elasticsearch_url',
        required=True,
    )

def _add_site_map_directory_path_arg(parser):
    parser.add_argument(
        '--siteMapDirectoryPath',
        help='Path to the directory where site map files should be stored',
        dest='site_map_directory_path',
        required=True,
    )

def _add_site_map_directory_url_arg(parser):
    parser.add_argument(
        '--siteMapDirectoryUrl',
        help='URL of the directory where site map files will be available',
        dest='site_map_directory_url',
        required=True,
    )

def _add_page_size_arg(parser):
    parser.add_argument(
        '--pageSize',
        help='Size of data pages to read from Elasticsearch',
        type=int,
        dest='page_size',
        default=1000,
    )

def _add_url_change_frequency_arg(parser):
    parser.add_argument(
        '--urlChangeFrequency',
        help='Change frequency of property URLs',
        choices=['always', 'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'never'],
        dest='url_change_frequency',
        default='weekly',
    )

def _add_scroll_expiry_arg(parser):
    parser.add_argument(
        '--scrollExpiry',
        help='Elasticsearch scroll expiry (e.g. "2m" - 2 minutes)',
        dest='scroll_expiry',
        default='2m',
    )

def _add_request_timeout_arg(parser):
    parser.add_argument(
        '--requestTimeout',
        help='Timeout, in seconds, for requests to Elasticsearch',
        type=int,
        dest='request_timeout',
        default=120,
    )

def _add_base_filename_arg(parser):
    parser.add_argument(
        '--baseFilename',
        help='Base name of a site map file. Site map file names in basename_X.xml format, '
             'where X is the number of the file (0-based)',
        dest='base_site_map_filename',
        default='site_map',
    )

def _add_index_filename_arg(parser):
    parser.add_argument(
        '--indexFilename',
        help='Name of site map index file',
        dest='site_map_index_filename',
        default='site_map_index.xml',
    )

def _add_max_records_per_file_arg(parser):
    parser.add_argument(
        '--maxRecordsPerFile',
        help='Maximum number of URLs per site map file',
        type=int,
        dest='max_urls_per_file',
        default=50000,
    )

def _add_file_encoding_arg(parser):
    parser.add_argument(
        '--fileEncoding',
        help='Site map file encoding',
        dest='file_encoding',
        default='UTF-8',
    )

def _add_logging_config_file(parser):
    parser.add_argument(
        '--loggingConfig',
        help='Logging configuration file path',
        dest='logging_config_file_path',
        default='logging_config.json',
    )

def _add_es_index_name(parser):
    parser.add_argument(
        '--index',
        help='Elasticsearch index name',
        dest='es_index',
        default='landregistry',
    )

def _add_es_doc_type(parser):
    parser.add_argument(
        '--docType',
        help='Elasticsearch document type',
        dest='es_doc_type',
        default='property',
    )
