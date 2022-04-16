from calendar import monthrange
from datetime import datetime

from bs4 import BeautifulSoup
from requests_html import HTMLSession


class MapsMissing(Exception):
    pass


def to_seconds(time_str):
    """
    Helper function to convert times like XX:XX.XXX to seconds.
    """
    minutes, seconds = time_str.split(':')
    minutes, seconds = int(minutes), float(seconds)
    return round(60 * minutes + seconds, 3)


class MapPackWebScraper:
    """
    This class is used to get medal times and other track info for every track in a map pack.
    """

    # General
    base_url = 'https://trackmania.exchange'
    user_agent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                  'Chrome/86.0.4240.198 Safari/537.36 OPR/72.0.3815.487')
    campaign_map_pack_len = 25

    # Map pack websites
    pagination_bar_class = 'windowv2-buttonbar windowv2-buttonbar-center'
    map_pack_container_id = 'mappacktracks-container'
    map_a_tag_attr_len = 2

    # Map websites
    medals_time_class = 'tipsy-n-html dark-grey'

    def __init__(self):
        self.session = HTMLSession()

    def get_html(self, url, js_script=None):
        """
        Returns a souped HTML representation of a url which is rendered with js_script.
        """
        r = self.session.get(url, headers={'User-Agent': self.user_agent})
        r.html.render(sleep=2, timeout=20)
        if js_script:
            r.html.render(sleep=2, timeout=20, script=js_script)
        return BeautifulSoup(r.html.html, features='lxml')

    def get_map_pack_title(self, map_pack_url):
        """
        Returns title of a map pack.
        """
        html = self.get_html(map_pack_url)
        return html.find('h1').get_text().strip()

    def count_pagination_pages(self, map_pack_url):
        """
        Counts the pagination pages. Subtract 2 because of forwards/backwards buttons.
        """
        html = self.get_html(map_pack_url)
        return len(html.find('div', {'class': self.pagination_bar_class}).find_all('a')) - 2

    def get_map_urls_and_titles(self, map_pack_url):
        """
        Yields (map_url, map_title) for every map in the given map pack.
        """
        pages_count = self.count_pagination_pages(map_pack_url)
        for page in range(1, pages_count + 1):
            js = (f'document.getElementsByClassName("{self.pagination_bar_class}")[0]' +
                  f'.getElementsByTagName("a")[{page}].click()')
            html = self.get_html(map_pack_url, js_script=js)
            map_pack_container = html.find('div', {'id': self.map_pack_container_id})
            for a_tag in map_pack_container.find_all('a'):
                if 'title' in a_tag.attrs and len(a_tag.attrs) == self.map_a_tag_attr_len:
                    yield self.base_url + a_tag.attrs['href'], a_tag.attrs['title']

    def get_map_medals(self, map_url):
        """
        Returns all medal times of a given map in the following order: author, gold, silver, bronze.
        """
        html = self.get_html(map_url)
        time_data = html.find('abbr', {'class': self.medals_time_class}).attrs['original-title']
        return [to_seconds(time.split(' ')[1]) for time in time_data.split('<br/>')[1:]]

    def map_pack_len(self, map_pack_url):
        """
        Determine the type (Campaign, TOTD, none of those) of the map pack and return the expected amount
        of maps in this pack.
        """
        tokens = map_pack_url.split('/')[-1].split('-')
        if tokens[0] in ['summer', 'fall', 'winter', 'spring']:
            return self.campaign_map_pack_len
        elif tokens[0] == 'totd':
            month, year = tokens[-2], int(tokens[-1])
            try:
                month = datetime.strptime(month, '%B').month
            except ValueError:
                print('WARNING: TOTD map pack detected. Failed to detect the expected amount of maps.')
                return None
            else:
                return monthrange(year, month)[1]
        else:
            return None

    def get_map_pack_info(self, map_pack_url):
        """
        Yields a map instance for every map in the given map pack.
        """
        print(f'\nStart scraping {map_pack_url} ...')
        map_count = 0
        for map_url, map_title in self.get_map_urls_and_titles(map_pack_url):
            map_medals = self.get_map_medals(map_url)
            print(f'Collected medal times for map {map_title} ({map_url}).')
            map_count += 1
            yield Map(url=map_url, title=map_title, medal_times=map_medals)
        print(f'{map_count} maps collected from {map_pack_url}.')
        expected_count = self.map_pack_len(map_pack_url)
        if expected_count is None:
            print('Could not calculate expected amount of maps because this map pack is not a campaign '
                  'or totd map pack.')
        else:
            if map_count != expected_count:
                raise MapsMissing(f'{map_count} were collected but {expected_count} maps are expected '
                                  f'for map pack {map_pack_url}.')


class Map:
    """
    Container to store information about a map.
    """

    medal_order = ['author', 'gold', 'silver', 'bronze']

    def __init__(self, url, title, medal_times):
        self.url = url
        self.title = title
        assert len(medal_times) == 4
        self.medal_times = dict()
        for i, medal in enumerate(self.medal_order):
            self.medal_times[medal] = medal_times[i]


def collect_map_packs(*map_packs_urls):
    """
    Collects every map for every map pack url and stores them in a dictionary (keys: map pack titles,
    values: list of map instances).
    """
    scraper = MapPackWebScraper()
    map_packs_info = dict()
    for url in map_packs_urls:
        map_pack_title = scraper.get_map_pack_title(url)
        map_packs_info[map_pack_title] = list(scraper.get_map_pack_info(url))
    return map_packs_info
