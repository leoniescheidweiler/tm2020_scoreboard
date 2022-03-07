from bs4 import BeautifulSoup
from requests_html import HTMLSession


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

    def get_map_pack_info(self, map_pack_url):
        pass


class Map:
    """
    Container to store information about a map.
    """

    medal_order = ['author', 'gold', 'silver', 'bronze']

    def __init__(self, url=None, title=None):
        self.url = url
        self.title = title
        self._medal_times = dict()

    @property
    def medal_times(self):
        return self._medal_times

    @medal_times.setter
    def medal_times(self, times_list):
        for i, medal in enumerate(self.medal_order):
            self.medal_times[medal] = times_list[i]


if __name__ == '__main__':
    t = MapPackWebScraper()
    urll = 'https://trackmania.exchange/maps/43850/fujiyama'
    print(t.get_map_medals(urll))
