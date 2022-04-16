import gspread
from gspread.utils import rowcol_to_a1

from config import Config
from replay import Replay


class GoogleSpreadsheet:

    no_map_pack_worksheets = ['Season Overview', 'Template']

    # TODO: create Template automatically so that these hardcoded values can be specified there?
    # TODO: pass Template instance to synchronize_replay_times()?
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
        print(f'Hello {self.config("Settings", "uplay_name")}.')

        if map_pack_titles := self.config('Settings', 'map_packs'):
            worksheets = [self.open_worksheet(title) for title in map_pack_titles]
        else:
            worksheets = self.worksheets

        new_records_total = 0
        for worksheet in worksheets:
            track_names = worksheet.col_values(self.track_name_col)[self.header_rows:]
            player_col = worksheet.find(self.config('Settings', 'uplay_name')).col
            times_s = worksheet.col_values(player_col)[self.header_rows:]
            # pad times_s so that it has the same length as track_names
            if (diff := (len(track_names) - len(times_s))) > 0:
                times_s += [''] * diff
            # empty cells get an infinite time
            times_s = [float(time) if time else float('inf') for time in times_s]
            new_records_map_pack = 0
            for i, track_name in enumerate(track_names):
                try:
                    track_time_s = Replay(track_name).time_s
                except FileNotFoundError:
                    continue
                else:
                    if times_s[i] > track_time_s:
                        times_s[i] = track_time_s
                        new_records_map_pack += 1
            # replace inf with empty strings and reformat list
            times_s = [[time] if time != float('inf') else [''] for time in times_s]
            # batch update new times
            start_cell_times = rowcol_to_a1(self.header_rows + 1, player_col)
            stop_cell_times = rowcol_to_a1(self.header_rows + len(track_names), player_col)
            worksheet.update(f'{start_cell_times}:{stop_cell_times}', times_s)
            new_records_total += new_records_map_pack
            print(f'{worksheet.title}: Updated {new_records_map_pack} times.')
        print(f'Updated {new_records_total} times in total. Congratulations!')


if __name__ == '__main__':
    t = GoogleSpreadsheet()
    t.synchronize_replay_times()
