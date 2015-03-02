import unittest
import elasticsearch
from mock import patch
from elasticsearch_scan import ElasticsearchClient
from models import SiteMapUrl
from test import FakeConfig

CONFIG = FakeConfig(
    base_page_url='http://localhost:1234',
    elasticsearch_url='http://localhost:4321/es',
    site_map_directory_path='n/a',
    site_map_directory_url='n/a',
    page_size=10,
    url_change_frequency='daily',
    scroll_expiry='5m',
    request_timeout=123,
    base_site_map_filename='n/a',
    site_map_index_filename='n/a',
    max_urls_per_file='n/a',
    file_encoding='n/a',
    es_doc_type='property',
    es_index='landregistry',
)

SCROLL_ID = 'cXVlcnlUaGVuRmV0Y2g7NTs3Nzp3eC1HUHBzSlJicXJxcDFJVU53V1NBOzc4Ond4LUdQcHNKUmJxcnFwMUlVTndXU0E7NzY6d3gtR1Bwc0pSYnFycXAxSVVOd1dTQTs4MDp3eC1HUHBzSlJicXJxcDFJVU53V1NBOzc5Ond4LUdQcHNKUmJxcnFwMUlVTndXU0E7MDs='

SEARCH_RESULT = {
    '_shards': {
        'successful': 5, 
        'total': 5, 
        'failed': 0
    }, 
    '_scroll_id': SCROLL_ID,
    'timed_out': False, 
    'hits': {
        'total': 3, 
        'max_score': 1.0, 
        'hits': [{
                     '_score': 1.0, 
                     '_id': '10025938201',
                     '_type': 'property', 
                     '_index': 'landregistry', 
                     '_source': {
                         'entryDatetime': '2014-06-07T09:01:38+00', 
                         'thoroughfareName': 'RIVERST ROAD',
                         'buildingName': '', 
                         'uprn': '10025938201',
                         'postTown': 'EXETER', 
                         'dependentThoroughfareName': '', 
                         'subBuildingName': '', 
                         'organisationName': '', 
                         'doubleDependentLocality': '', 
                         'departmentName': '', 
                         'postcode': 'EX2 4RQ',
                         'dependentLocality': '', 
                         'position': {
                             'y': 93203.52,
                             'x': 293918.15
                         }, 
                         'addressKey': '18_RIVERSTH_ROAD_EXETER_EX2_4RQ',
                         'buildingNumber': '78'
                     }
                 }
        ]
    }, 
    'took': 3
}

class ElasticsearchClientTestCase(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None

    @patch.object(elasticsearch.Elasticsearch, 'search')
    @patch.object(elasticsearch.Elasticsearch, 'scroll')
    def test_next_page_of_records_calls_search_on_first_call(self, mock_scroll, mock_search):
        ElasticsearchClient(CONFIG).next_page_of_records()
        self.assertEqual(mock_scroll.mock_calls, [])
        mock_search.assert_called_once_with(CONFIG.es_index, CONFIG.es_doc_type, params={'timeout': CONFIG.request_timeout, 'scroll': CONFIG.scroll_expiry, 'size': CONFIG.page_size }, body=None)

    @patch.object(elasticsearch.Elasticsearch, 'search', return_value=SEARCH_RESULT)
    @patch.object(elasticsearch.Elasticsearch, 'scroll', return_value=SEARCH_RESULT)
    def test_next_page_of_records_calls_scroll_on_second_and_later_calls(self, mock_scroll, mock_search):
        client = ElasticsearchClient(CONFIG)
        client.next_page_of_records()
        client.next_page_of_records()

        mock_search.assert_called_once_with(
            CONFIG.es_index, 
            CONFIG.es_doc_type, 
            params={
                'timeout': CONFIG.request_timeout, 
                'scroll': CONFIG.scroll_expiry, 
                'size': CONFIG.page_size 
            }, 
            body=None)
        
        mock_scroll.assert_called_once_with(
            scroll_id=SCROLL_ID, 
            params={
                'scroll': CONFIG.scroll_expiry, 
                'search_type': 'scan', 
                'timeout': CONFIG.request_timeout, 
                'size': CONFIG.page_size 
            })

    @patch.object(elasticsearch.Elasticsearch, 'search', return_value=SEARCH_RESULT)
    @patch.object(elasticsearch.Elasticsearch, 'scroll', return_value=SEARCH_RESULT)
    def test_next_page_of_records_transform_result_to_right_format(self, mock_scroll, mock_search):
        client = ElasticsearchClient(CONFIG)
        search_result = client.next_page_of_records()
        scroll_result = client.next_page_of_records()

        expected_site_map_url = SiteMapUrl(
            location='http://localhost:1234/EX2_4RQ/18_RIVERSTH_ROAD_EXETER',
            last_modified='2014-06-07T09:01+00:00',
            change_frequency='daily',
        )
        
        self.assertSequenceEqual(search_result, [expected_site_map_url])
        self.assertEqual(scroll_result, [expected_site_map_url])

    @patch.object(elasticsearch.Elasticsearch, 'search', return_value=SEARCH_RESULT)
    @patch.object(elasticsearch.Elasticsearch, 'clear_scroll')
    def test_exit_clears_the_scroll(self, mock_clear_scroll, mock_search):
        client = ElasticsearchClient(CONFIG)
        
        with client:
            client.next_page_of_records()
        
        mock_clear_scroll.assert_called_once_with(SCROLL_ID)
