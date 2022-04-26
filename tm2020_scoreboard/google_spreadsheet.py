import os

import gspread
from gspread.utils import rowcol_to_a1

from tm2020_scoreboard.config import Config
from tm2020_scoreboard.replay import Replay
from tm2020_scoreboard.webscraping import collect_map_packs


class GoogleSpreadsheet:

    no_map_pack_worksheets = ['Season Overview', 'Template']

    # TODO: create Template automatically so that these hardcoded values can be specified there?
    # TODO: pass Template instance to synchronize_replay_times()?
    track_name_col = 5
    header_rows = 2

    def __init__(self):
        self.config = Config()
        credentials_dir = os.path.dirname(os.path.realpath(__file__))
        try:
            service_acc = gspread.service_account(os.path.join(credentials_dir,
                                                               self.config('Settings', 'service_account_json')))
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
            start_cell = rowcol_to_a1(self.header_rows + 1, player_col)
            stop_cell = rowcol_to_a1(self.header_rows + len(track_names), player_col)
            worksheet.update(f'{start_cell}:{stop_cell}', times_s)
            new_records_total += new_records_map_pack
            print(f'{worksheet.title}: Updated {new_records_map_pack} times.')
        print(f'Updated {new_records_total} times in total. Congratulations!')

    def create_worksheets_for_map_packs(self, map_packs_urls):
        """
        Creates a worksheet for every map pack in map_packs_urls and fills in the map names and the
        corresponding medal times.
        """
        map_packs_info = collect_map_packs(map_packs_urls)
        for map_pack_title, maps in map_packs_info.items():
            try:
                worksheet = self.open_worksheet(map_pack_title)
            except gspread.exceptions.WorksheetNotFound:
                # TODO: create a worksheet with a given template
                raise gspread.exceptions.WorksheetNotFound(f'Worksheet {map_pack_title} does not exist.')
            else:
                while True:
                    user_input = input(f'Worksheet {map_pack_title} already exists. Would you like to '
                                       'overwrite it? [y/n]\n').lower()
                    if user_input in ['y', 'n']:
                        break
                if user_input == 'n':
                    continue
                elif user_input == 'y':
                    # TODO: delete existing worksheet and create a new one with a given template
                    pass
                else:
                    raise ValueError(f'Unexpected user input "{user_input}" occurred.')

            data_to_update = []
            for map_ in maps:
                data_to_update.append([
                    map_.medal_times['bronze'], map_.medal_times['silver'], map_.medal_times['gold'],
                    map_.medal_times['author'], map_.title
                ])
            start_cell = rowcol_to_a1(self.header_rows + 1, 1)
            stop_cell = rowcol_to_a1(self.header_rows + len(maps), self.track_name_col)
            worksheet.update(f'{start_cell}:{stop_cell}', data_to_update)
            print(f'Created new worksheet for map pack {map_pack_title}.')
