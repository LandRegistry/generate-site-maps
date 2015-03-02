#!/usr/bin/env python

from site_map import SiteMapCreator
from elasticsearch_scan import ElasticsearchClient
import logging
from logging import config
import json
import settings

LOGGER = logging.getLogger(__name__)

class Generator():

    def __init__(self, config):
        self.config = config

    def generate_property_site_map(self):
        LOGGER.info('Started generating site map')
        
        site_map_creator = SiteMapCreator(config)
        site_map_creator.clear_site_map_directory()

        with ElasticsearchClient(self.config) as client:
            self._add_addresses_to_site_map(client, site_map_creator)
            site_map_creator.create_site_map_index_file()

        LOGGER.info('Completed generating site map')

    def _add_addresses_to_site_map(self, client, site_map):
        site_map_entries = client.next_page_of_records()

        while site_map_entries:
            site_map.append_urls_to_site_map(site_map_entries)
            site_map_entries = client.next_page_of_records()

        site_map.flush_site_map()


def setup_logging(logging_config_file_path):
    try:
        with open(logging_config_file_path, 'rt') as file:
            config = json.load(file)
        logging.config.dictConfig(config)
    except IOError as e:
        raise(Exception('Failed to load logging configuration', e))


if __name__ == '__main__':    
    config = settings.parse_command_line_arguments()
    
    try:
        setup_logging(config.logging_config_file_path)
        Generator(config).generate_property_site_map()
    except Exception as e:
        LOGGER.error("An error occurred when running the script", e)
