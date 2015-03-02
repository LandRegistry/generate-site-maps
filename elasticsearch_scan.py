from elasticsearch import Elasticsearch, Transport
from models import SiteMapUrl
import logging
from datetime import datetime

LOGGER = logging.getLogger(__name__)

class ElasticsearchClient():

    def __init__(self, config):
        self.config = config
        self.client = Elasticsearch(config.elasticsearch_url)
        self.scroll_id = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._try_clear_scroll()

    def next_page_of_records(self):
        result = self._retrieve_page_of_data()
        self.scroll_id = self._get_scroll_id(result)
        site_map_entries = self._get_site_map_entries(result)
        LOGGER.info('Retrieved {} records from elasticsearch'.format(len(site_map_entries)))
        return site_map_entries

    def _retrieve_page_of_data(self):
        try:
            if self.scroll_id:
                result = self._scroll(self.scroll_id)
            else:
                result = self._search()

            return result
        except Exception as e:
            raise Exception('Failed to retrieve a page of data from elasticsearch', e)

    def _get_site_map_entries(self, result):
        try:
            address_page = self._get_addresses(result)
            site_map_entries = self._convert_to_site_map_entries(address_page)
            return site_map_entries
        except Exception as e:
            raise Exception('Failed to convert elasticsearch result to a list of site map entries', e)

    def _scroll(self, scroll_id):
        return self.client.scroll(
            scroll_id=scroll_id,
            params={
                'scroll': self.config.scroll_expiry,
                'search_type': 'scan',
                'size': self.config.page_size,
                'timeout': self.config.request_timeout,
            }
        )


    def _search(self):
        return self.client.search(
            self.config.es_index,
            self.config.es_doc_type,
            body=None,
            params={
                'size': self.config.page_size,
                'scroll': self.config.scroll_expiry,
                'timeout': self.config.request_timeout,
            }
        )

    def _try_clear_scroll(self):
        try:
            self.client.clear_scroll(self.scroll_id)
            LOGGER.info('Cleared elasticsearch scroll')
        except Exception as e:
            LOGGER.warn('Failed to clear scroll in elasticsearch', e)

    def _get_scroll_id(self, search_result):
        try:
            return search_result['_scroll_id']
        except Exception as e:
            raise Exception('Failed to extract scroll ID from the elasticsearch result', e)

    def _get_addresses(self, search_result):
        return search_result['hits']['hits']

    def _convert_to_site_map_entries(self, address_page):
        return [self._get_site_map_entry(address) for address in address_page]

    def _get_page_url(self, address):
        data = address['_source']
        postcode = data['postcode']
        address_key = data['addressKey']
        address_url_segment = address_key[:len(address_key) - len(postcode) - 1]

        return '{}/{}/{}'.format(self.config.base_page_url, postcode.replace(' ', '_'), address_url_segment)

    def _get_site_map_entry(self, address):
        entry_datetime = datetime.strptime(address['_source']['entryDatetime'], '%Y-%m-%dT%H:%M:%S+00')
        
        return SiteMapUrl(
            location=self._get_page_url(address),
            last_modified=entry_datetime.strftime('%Y-%m-%dT%H:%M+00:00'),
            change_frequency=self.config.url_change_frequency,
        )
