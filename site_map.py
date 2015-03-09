import os
import datetime
from xml.etree.ElementTree import ElementTree, Element, SubElement
import re
import logging

LOGGER = logging.getLogger(__name__)

class SiteMapCreator():

    def __init__(self, config):
        self.config = config
        self.records_in_current_file = 0
        self.current_file_number = 0
        self.current_site_map = self._create_empty_site_map_document()
        self.site_map_file_names = []

    def create_site_map_index_file(self):
        try:
            site_map_index = self._create_site_map_index_document()
            self._save_site_map_index_to_file(site_map_index)
        except Exception as e:
            raise Exception('Failed to create site map index file', e)

    def append_urls_to_site_map(self, urls):
        remaining_space_in_current_doc = self.config.max_urls_per_file - self._nof_urls_in_current_site_map()
        nof_urls_to_add_to_existing_doc = min(remaining_space_in_current_doc, len(urls))

        self._append_urls(urls[0:nof_urls_to_add_to_existing_doc], self.current_site_map)
                
        if self._nof_urls_in_current_site_map() == self.config.max_urls_per_file:
            self._save_current_site_map()
            self.current_file_number += 1
            self.current_site_map = self._create_empty_site_map_document()

        if len(urls) > nof_urls_to_add_to_existing_doc:
            self.append_urls_to_site_map(urls[nof_urls_to_add_to_existing_doc:])

    def clear_site_map_directory(self):
        LOGGER.info('Clearing site map directory...')
        
        try:
            for filename in os.listdir(self.config.site_map_directory_path):
                file_path = os.path.join(self.config.site_map_directory_path, filename)
                if self._is_site_map_file(filename, file_path) or filename == self.config.site_map_index_filename:
                    os.unlink(file_path)
                    LOGGER.info('Deleted file {}'.format(file_path))
        except Exception as e:
            raise Exception('Failed to clear site map directory', e)

    def flush_site_map(self):
        if self._nof_urls_in_current_site_map() > 0:
            self._save_current_site_map()

    def _nof_urls_in_current_site_map(self):
        return len(self.current_site_map.getroot().getchildren())

    def _is_site_map_file(self, filename, file_path):
        site_map_filename_pattern = '{}_\\d+\\.xml'.format(self.config.base_site_map_filename)
        return os.path.isfile(file_path) and re.fullmatch(site_map_filename_pattern, filename)

    def _create_empty_site_map_document(self):
        url_set_element = Element('urlset')
        url_set_element.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        document = ElementTree(url_set_element)
        return document

    def _create_site_map_index_document(self):
        site_map_index_element = Element('sitemapindex')
        site_map_index_element.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')

        last_modified = datetime.datetime.now()

        for file_name in self.site_map_file_names:
            site_map_element = self._create_site_map_element(file_name, last_modified)
            site_map_index_element.append(site_map_element)

        return ElementTree(site_map_index_element)

    def _append_urls(self, urls, site_map):
        url_set_element = site_map.getroot()
        
        for url in urls:
            url_element = self._add_sub_element(url_set_element, 'url')
            self._add_sub_element(url_element, 'loc', url.location)
            self._add_sub_element(url_element, 'lastmod', url.last_modified)
            self._add_sub_element(url_element, 'changefreq', url.change_frequency)

    def _create_site_map_element(self, file_name, last_modified):
        site_map_element = Element('sitemap')
        self._add_sub_element(site_map_element, 'loc', self._get_site_map_url(file_name))
        self._add_sub_element(site_map_element, 'lastmod', last_modified.strftime('%Y-%m-%d'))
        return site_map_element

    def _get_site_map_url(self, file_name):
        return '{}/{}'.format(self.config.site_map_directory_url, file_name)

    def _add_sub_element(self, parent, tag, text=None):
        sub_element = SubElement(parent, tag)

        if text:
            sub_element.text = text

        return sub_element

    def _save_current_site_map(self):
        filename = self._get_file_name(self.current_file_number)
        self._save_site_map_to_file(self.current_site_map, filename)

    def _save_site_map_to_file(self, site_map, file_name):                
        try:
            file_path = self._get_file_path(file_name)
            self._save_xml_doc_to_file(site_map, file_path)            
        except Exception as e:
            raise Exception('Failed to create site map file: {}'.format(file_path), e)
        else:
            self.site_map_file_names += [file_name]
            LOGGER.info('Created site map file: {}'.format(file_path))

    def _save_site_map_index_to_file(self, site_map_index):
        try:
            file_path = self._get_file_path(self.config.site_map_index_filename)
            self._save_xml_doc_to_file(site_map_index, file_path)
        except Exception as e:
            raise Exception('Failed to create site map index file: {}'.format(file_path), e)
        else:
            LOGGER.info('Created site map index file: {}'.format(file_path))

    def _save_xml_doc_to_file(self, xml, file_path):
        xml.write(file_path, xml_declaration=True, encoding=self.config.file_encoding)

    def _get_file_path(self, file_name):
        return '{}/{}'.format(self.config.site_map_directory_path, file_name)

    def _get_file_name(self, file_number):
        return "{}_{}.xml".format(self.config.base_site_map_filename, file_number)
