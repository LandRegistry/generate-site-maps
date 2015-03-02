from io import StringIO
import unittest
from mock import call, patch
from site_map import SiteMapCreator
from models import SiteMapUrl
import xml
import os
from asq.initiators import query
from datetime import datetime
from test import FakeConfig

CONFIG = FakeConfig(
    base_page_url='n/a',
    elasticsearch_url='n/a',
    site_map_directory_path='sitemap/directory/path',
    site_map_directory_url='http://localhost/sitemap/directory/url',
    page_size=0,
    url_change_frequency='n/a',
    scroll_expiry='n/a',
    request_timeout='n/a',
    base_site_map_filename='sitemap',
    site_map_index_filename='sitemap_index.xml',
    max_urls_per_file=10,
    file_encoding='UTF-8',
    es_doc_type='n/a',
    es_index='n/a',
)

def create_site_map_url(index):
    return SiteMapUrl(
        location='http://localhost:1234/property/SW11_2DR/TEST_PROPERTY_{}'.format(index),
        last_modified='2015-03-02',
        change_frequency='daily',
    )

def get_locations_from_site_map(site_map):
    site_map_elements = site_map.getroot().getchildren()

    return (
        query(site_map_elements)
            .select(lambda e: query(e.getchildren()).single(lambda e: e.tag == 'loc'))
            .select(lambda e: e.text)
            .to_list()
    )


class SiteMapCreatorTestCase(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None

    def test_flush_site_map_creates_new_file_when_current_site_map_has_urls(self):
        fake_file = FakeFile()

        with patch('xml.etree.ElementTree.open', create=True) as mock_open:
            mock_open.return_value = fake_file

            site_map_creator = SiteMapCreator(CONFIG)
            url = SiteMapUrl(location='http://localhost:1234', last_modified='2015-03-02', change_frequency='daily')
            site_map_creator.append_urls_to_site_map([url])
            site_map_creator.flush_site_map()

            expected_file_path = '{}/{}_0.xml'.format(CONFIG.site_map_directory_path, CONFIG.base_site_map_filename)
            mock_open.assert_called_once_with(
                expected_file_path, 'w', encoding=CONFIG.file_encoding.lower(), errors='xmlcharrefreplace')
            
            with open('data/sitemap_1_url.xml') as expected_file:
                self.assertMultiLineEqual(fake_file.saved_content, expected_file.read())

    @patch.object(xml.etree.ElementTree.ElementTree, 'write')
    def test_flush_site_map_does_not_create_file_when_current_site_map_is_empty(self, mock_write):
        mock_write.return_value = lambda self, filename, **kwargs : None
        SiteMapCreator(CONFIG).flush_site_map()
        self.assertListEqual(mock_write.mock_calls, [])

    @patch.object(os, 'listdir')
    @patch.object(os.path, 'isfile')
    @patch.object(os, 'unlink')
    def test_clear_site_map_directory_deletes_all_site_map_files(self, mock_unlink, mock_isfile, mock_listdir):
        filename1 = '{}_123.xml'.format(CONFIG.base_site_map_filename)
        filename2 = '{}_0.xml'.format(CONFIG.base_site_map_filename)

        mock_listdir.return_value = [filename1, filename2]
        mock_isfile.return_value = lambda path: True

        SiteMapCreator(CONFIG).clear_site_map_directory()

        expected_file1_path = '{}/{}'.format(CONFIG.site_map_directory_path, filename1)
        expected_file2_path = '{}/{}'.format(CONFIG.site_map_directory_path, filename2)

        self.assertIn(call(expected_file1_path), mock_unlink.mock_calls)
        self.assertIn(call(expected_file2_path), mock_unlink.mock_calls)
        self.assertEquals(len(mock_unlink.mock_calls), 2)

    @patch.object(os, 'listdir')
    @patch.object(os.path, 'isfile')
    @patch.object(os, 'unlink')
    def test_clear_site_map_directory_deletes_site_map_index_file(self, mock_unlink, mock_isfile, mock_listdir):
        mock_listdir.return_value = [CONFIG.site_map_index_filename]
        mock_isfile.return_value = lambda path: True

        SiteMapCreator(CONFIG).clear_site_map_directory()
        
        expected_sitemap_index_path = '{}/{}'.format(CONFIG.site_map_directory_path, CONFIG.site_map_index_filename)
        mock_unlink.assert_called_once_with(expected_sitemap_index_path)

    @patch.object(os, 'listdir')
    @patch.object(os.path, 'isfile')
    @patch.object(os, 'unlink')
    def test_clear_site_map_directory_does_not_delete_unknown_files(self, mock_unlink, mock_isfile, mock_listdir):
        filename1 = '_site_map_123.xml'.format(CONFIG.base_site_map_filename)
        filename2 = 'other.txt'.format(CONFIG.base_site_map_filename)

        mock_listdir.return_value = [filename1, filename2]
        mock_isfile.return_value = lambda path: True

        SiteMapCreator(CONFIG).clear_site_map_directory()
        self.assertListEqual(mock_unlink.mock_calls, [])

    def test_append_urls_to_site_map_adds_urls_to_current_site_map_when_enough_space(self):
        max_records_per_file = 10
        urls_to_append = [create_site_map_url(i) for i in range(0, max_records_per_file - 1)]

        site_map_creator = SiteMapCreator(CONFIG._replace(max_urls_per_file=max_records_per_file))
        site_map_creator.append_urls_to_site_map(urls_to_append)

        expected_locations = [url.location for url in urls_to_append]
        actual_locations_in_site_map = get_locations_from_site_map(site_map_creator.current_site_map)

        self.assertListEqual(actual_locations_in_site_map, expected_locations)
                    
    def test_append_urls_to_site_map_saves_site_map_to_file_when_full(self):
        fake_file = FakeFile()

        with patch('xml.etree.ElementTree.open', create=True) as mock_open:
            mock_open.return_value = fake_file
            
            max_records_per_file = 3
            urls_to_append = [create_site_map_url(i) for i in range(0, max_records_per_file)]

            config = CONFIG._replace(max_urls_per_file=max_records_per_file)
            site_map_creator = SiteMapCreator(config)
            first_site_map = site_map_creator.current_site_map

            site_map_creator.append_urls_to_site_map(urls_to_append)

            expected_locations_in_site_map = [url.location for url in urls_to_append]
            expected_saved_file_path = '{}/{}_0.xml'.format(
                config.site_map_directory_path, config.base_site_map_filename)

            mock_open.assert_called_once_with(
                expected_saved_file_path, 'w', encoding=config.file_encoding.lower(), errors='xmlcharrefreplace')

            with open('data/sitemap_3_urls.xml') as expected_file:
                self.assertEqual(fake_file.saved_content, expected_file.read())

            self.assertListEqual(get_locations_from_site_map(first_site_map), expected_locations_in_site_map)
            self.assertListEqual(get_locations_from_site_map(site_map_creator.current_site_map), [])

    def test_append_urls_to_site_map_adds_urls_to_non_empty_site_map(self):
        urls_to_append = [create_site_map_url(i) for i in range(0, 4)]

        site_map_creator = SiteMapCreator(CONFIG)
        site_map_creator.append_urls_to_site_map(urls_to_append[0:1])
        site_map_creator.append_urls_to_site_map(urls_to_append[1:3])
        site_map_creator.append_urls_to_site_map(urls_to_append[3:4])

        expected_locations = [url.location for url in urls_to_append]
        actual_locations_in_site_map = get_locations_from_site_map(site_map_creator.current_site_map)

        self.assertListEqual(actual_locations_in_site_map, expected_locations)

    def test_append_urls_to_site_map_saves_current_site_map_and_uses_new_one_when_not_enough_space(self):
        fake_file = FakeFile()

        with patch('xml.etree.ElementTree.open', create=True) as mock_open:
            mock_open.return_value = fake_file

            max_records_per_file = 2
            urls_to_append = [create_site_map_url(i) for i in range(0, max_records_per_file + 1)]
            config = CONFIG._replace(max_urls_per_file=max_records_per_file)
            site_map_creator = SiteMapCreator(config)
            first_site_map = site_map_creator.current_site_map

            site_map_creator.append_urls_to_site_map(urls_to_append)

            expected_locations_in_first_site_map = [url.location for url in urls_to_append][:max_records_per_file]
            expected_locations_in_second_site_map = [urls_to_append[max_records_per_file].location]
            expected_saved_file_path = '{}/{}_0.xml'.format(
                config.site_map_directory_path, config.base_site_map_filename)

            mock_open.assert_called_once_with(
                expected_saved_file_path, 'w', encoding=config.file_encoding.lower(), errors='xmlcharrefreplace')

            self.assertListEqual(get_locations_from_site_map(first_site_map), expected_locations_in_first_site_map)
            self.assertListEqual(
                get_locations_from_site_map(site_map_creator.current_site_map), 
                expected_locations_in_second_site_map
            )

    def test_create_site_map_index_file_creates_index_file_referencing_all_site_map_files(self):
        fake_site_map_file_1 = FakeFile()
        fake_site_map_file_2 = FakeFile()
        fake_site_map_index_file = FakeFile()

        with patch('xml.etree.ElementTree.open', create=True) as mock_open:
            mock_open.side_effect = [fake_site_map_file_1, fake_site_map_file_2, fake_site_map_index_file]

            max_records_per_file = 2
            urls_to_append = [create_site_map_url(i) for i in range(0, max_records_per_file + 1)]
            config = CONFIG._replace(max_urls_per_file=max_records_per_file)
            site_map_creator = SiteMapCreator(config)

            site_map_creator.append_urls_to_site_map(urls_to_append)
            site_map_creator.flush_site_map()
            site_map_creator.create_site_map_index_file()

            site_map_file_paths = ['{}/{}_{}.xml'.format(
                config.site_map_directory_path, config.base_site_map_filename, i) for i in range(0, 2)]
            site_map_index_file_path = '{}/{}'.format(config.site_map_directory_path, config.site_map_index_filename)

            standard_args = { 'encoding': config.file_encoding.lower(), 'errors': 'xmlcharrefreplace'}

            expected_file_open_calls = [
                call(site_map_file_paths[0], 'w', **standard_args),
                call(site_map_file_paths[1], 'w', **standard_args),
                call(site_map_index_file_path, 'w', **standard_args),
            ]

            mock_open.assert_has_calls(expected_file_open_calls, any_order=False)
            
            with (open('data/sitemap_index_for_2_sitemaps.xml')) as expected_index:
                expected_content = expected_index.read().replace(
                    '<lastmod>2015-03-05</lastmod>', '<lastmod>{0:%Y-%m-%d}</lastmod>'.format(datetime.now()))
                self.assertSequenceEqual(fake_site_map_index_file.saved_content, expected_content)


class FakeFile(StringIO):
    def close(self, *args, **kwargs):
        self.saved_content = self.getvalue()
        super(FakeFile, self).close(*args, **kwargs)
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args, **kwargs):
        self.saved_content = self.getvalue()
        super(FakeFile, self).__exit__(*args, **kwargs)
