import unittest
from mock import patch
from mock import call
import elasticsearch_scan
from generate import Generator
from models import SiteMapUrl
import site_map
from test import FakeConfig

CONFIG = FakeConfig(
    base_page_url='n/a',
    elasticsearch_url='n/a',
    site_map_directory_path='n/a',
    site_map_directory_url='n/a',
    page_size='n/a',
    url_change_frequency='n/a',
    scroll_expiry='n/a',
    request_timeout='n/a',
    base_site_map_filename='n/a',
    site_map_index_filename='n/a',
    max_urls_per_file='n/a',
    file_encoding='n/a',
    es_doc_type='n/a',
    es_index='n/a',
)

class GeneratorTestCase(unittest.TestCase):

    @patch.object(elasticsearch_scan.ElasticsearchClient, 'next_page_of_records')
    @patch.object(elasticsearch_scan.ElasticsearchClient, '__exit__')
    @patch.object(site_map.SiteMapCreator, 'clear_site_map_directory')
    @patch.object(site_map.SiteMapCreator, 'append_urls_to_site_map')
    @patch.object(site_map.SiteMapCreator, 'flush_site_map')
    @patch.object(site_map.SiteMapCreator, 'create_site_map_index_file')
    def test_generate_property_site_map_passes_each_es_data_page_to_site_map_creator(
            self,
            mock_create_site_map_index_file,
            mock_flush_site_map,
            mock_append_urls_to_site_map,
            mock_clear_site_map_directory,
            mock_client_exit,
            mock_next_page_of_records):

        url_list_1 = [SiteMapUrl(location='loc1', last_modified='2015-03-01', change_frequency='weekly')]
        url_list_2 = [SiteMapUrl(location='loc2', last_modified='2015-03-02', change_frequency='daily')]

        mock_next_page_of_records.side_effect = [url_list_1, url_list_2, []]

        Generator(CONFIG).generate_property_site_map()

        mock_clear_site_map_directory.assert_called_once()
        self.assertEqual(len(mock_next_page_of_records.mock_calls), 3)
        self.assertListEqual(mock_append_urls_to_site_map.mock_calls, [call(url_list_1), call(url_list_2)])
        mock_flush_site_map.assert_called_once_with()
        mock_create_site_map_index_file.assert_called_once_with()
        self.assertEqual(len(mock_client_exit.mock_calls), 1)
