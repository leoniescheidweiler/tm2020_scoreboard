import gspread

from config import Config


class GoogleSheetsConnection:

    no_map_pack_worksheets = ['Season Overview', 'Template']

    def __init__(self):
        config = Config()
        service_acc = gspread.service_account(config('Settings', 'service_account_json'))
        spreadsheet_title = config('Settings', 'spreadsheet_title')
        try:
            self.spreadsheet = service_acc.open(spreadsheet_title)
        except gspread.exceptions.SpreadsheetNotFound:
            raise gspread.exceptions.SpreadsheetNotFound(f'Spreadsheet "{spreadsheet_title}" does not exist.')

    @property
    def worksheets(self):
        """
        WARNING: Worksheets in "no_map_pack_worksheets" are left out.
        """
        return [sheet for sheet in self.spreadsheet.worksheets() if sheet.title not in self.no_map_pack_worksheets]

    def open_worksheet(self, title):
        """
        Returns a worksheet instance which matches the given title.
        """
        return self.spreadsheet.worksheet(title)

    def synchronize_replay_times(self):
        """
        Synchronizes all the replay times for all map packs listed in config.ini. If there are not any map packs
        listed, then all map packs with an existing worksheet in the spreadsheet will be updated.
        """
        pass


if __name__ == '__main__':
    t = GoogleSheetsConnection()
    t.open_worksheet('adsf')
