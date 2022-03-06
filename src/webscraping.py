from bs4 import BeautifulSoup
from requests_html import HTMLSession


class MapPackWebScraper:
    """
    This class is used to get medal times and other track info for every track in a map pack.
    """

    user_agent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                  'Chrome/86.0.4240.198 Safari/537.36 OPR/72.0.3815.487')
    pagination_bar_class = 'windowv2-buttonbar windowv2-buttonbar-center'

    def __init__(self):
        self.session = HTMLSession()

    def get_html(self, url, js_script=None):
        """
        Returns a souped HTML representation of a url which is rendered with js_script.
        """
        r = self.session.get(url, headers={'User-Agent': self.user_agent})
        r.html.render(sleep=2, wait=2, timeout=20, script=js_script)
        return BeautifulSoup(r.html.html, features='lxml')

    def count_pagination_pages(self, map_pack_url):
        """
        Counts the pagination pages. Subtract 2 because of forwards/backwards buttons.
        """
        html = self.get_html(map_pack_url)
        return len(html.find('div', {'class': self.pagination_bar_class}).find_all('a')) - 2

    def get_track_urls(self, map_pack_url):
        pages_count = self.count_pagination_pages(map_pack_url)
        for page in range(1, pages_count + 1):
            js = (f'document.getElementsByClassName("{self.pagination_bar_class}")[0]' +
                  f'.getElementsByTagName("a")[{page}].click()')
            html = self.get_html(map_pack_url, js_script=js)
            for a_tag in html.find_all('a'):
                if 'title' in a_tag.attrs:
                    print('ds')


if __name__ == '__main__':
    t = MapPackWebScraper()
    urll = 'https://trackmania.exchange/mappack/view/42/summer-2020'
    t.get_track_urls(urll)
