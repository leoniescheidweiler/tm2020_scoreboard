import gspread

from config import Config
from replay import Replay


class GoogleSpreadsheet:

    no_map_pack_worksheets = ['Season Overview', 'Template']

    # TODO: create Template automatically so that these hardcoded values can be specified there?
    track_name_col = 5
    header_rows = 2

    def __init__(self):
        self.config = Config()
        try:
            service_acc = gspread.service_account(self.config('Settings', 'service_account_json'))
        except FileNotFoundError:
            raise FileNotFoundError(f'{self.config("Settings", "service_account_json")} does not exist. '
                                    'Specify a valid .json file.')
        spreadsheet_title = self.config('Settings', 'spreadsheet_title')
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
        if map_pack_titles := self.config('Settings', 'map_packs'):
            worksheets = [self.open_worksheet(title) for title in map_pack_titles]
        else:
            worksheets = self.worksheets

        for worksheet in worksheets:
            track_names = worksheet.col_values(self.track_name_col)[self.header_rows:]
            player_col = worksheet.find(self.config('Settings', 'uplay_name')).col
            old_times_s = worksheet.col_values(player_col)[self.header_rows:]
            if (diff := (len(track_names) - len(old_times_s))) > 0:
                old_times_s += [''] * diff
            old_times_s = [float(time) if time else float('inf') for time in old_times_s]
            for i, track_name in enumerate(track_names):
                try:
                    track_time_s = Replay(track_name).time_s
                except FileNotFoundError:
                    continue
                else:
                    old_time_s = old_times_s[i]
                    if old_time_s > track_time_s:
                        # TODO: update cell values with batch update
                        pass


if __name__ == '__main__':
    t = GoogleSpreadsheet()
    t.synchronize_replay_times()
