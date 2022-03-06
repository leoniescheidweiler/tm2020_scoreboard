import configparser
import sys
import os
import gspread
import re

config = configparser.ConfigParser()
config.read('config.ini')

UPLAY_NAME = config['SETTINGS']['uplay_name']
REPLAY_PATH = config['SETTINGS']['replay_path']
SEASONS = [season.strip() for season in config['SETTINGS']['seasons'].split(', ')]

print(f'Hello {UPLAY_NAME}.')
gc = gspread.service_account(filename=config['SETTINGS']['service_account_json'])
spreadsheet = gc.open('TrackMania 2020')

updated_times = 0
for season in SEASONS:
    try:
        worksheet = spreadsheet.worksheet(season)
    except gspread.exceptions.WorksheetNotFound:
        sys.exit(f'Season {season} does not have a worksheet.')

    try:
        uplay_name_cell = worksheet.find(UPLAY_NAME)
    except gspread.exceptions.CellNotFound:
        sys.exit(f'User {UPLAY_NAME} does not have a column.')

    header_rows = 2
    track_name_column = 5
    user_column = uplay_name_cell.col

    # get column containing track names.
    track_name_list = worksheet.col_values(track_name_column)[header_rows:]

    # get column of already written best times for this player
    # if the last tracks haven't been driven yet the current_times_list is shorter than the track_names_list
    # therefore append empty elements
    scoreboard_time_list = worksheet.col_values(user_column)[header_rows:]
    while len(scoreboard_time_list) < len(track_name_list):
        scoreboard_time_list.append('')
    # use a godly list comprehension to replace all '' by float('inf'). this makes it easier to compare scoreboard
    # times and replay times
    scoreboard_time_list = [float(scoreboard_time) if scoreboard_time != '' else float('inf')
                            for scoreboard_time in scoreboard_time_list]

    # prepare replay_time_list as list of infinities. replays that are found will replace the infinity
    replay_time_list = [float('inf')]*len(track_name_list)

    for track_index, track_name in enumerate(track_name_list):
        # open replay file and read the time. it is written in clear text inside this file.
        replay = os.path.join(REPLAY_PATH, f'{UPLAY_NAME}_{track_name}_PersonalBest_TimeAttack.Replay.Gbx')
        if os.path.exists(replay):
            with open(replay, 'r', encoding='utf8', errors='ignore') as file:
                data = file.readlines()
            for line in data:
                if 'times best' in line:
                    replay_time_in_ms = re.search(r'<times best="[0-9]+"', line).group(0).split('"')[1]
                    replay_time_list[track_index] = float(replay_time_in_ms)/1000
                    break

    # use a godly list comprehension to find the smaller time, be it in the scoreboard_time_list or in the
    # replay time list
    updated_time_list = [min(track_time_tuple) for track_time_tuple in zip(scoreboard_time_list, replay_time_list)]

    # count how many times have been updated
    updated_times_this_season = 0
    for index in range(len(track_name_list)):
        if updated_time_list[index] != scoreboard_time_list[index]:
            updated_times_this_season += 1

    # use a godly list comprehension to convert float('inf') back to '' for writing to the worksheet
    updated_time_list = [float(updated_time) if updated_time != float('inf') else ''
                         for updated_time in updated_time_list]

    # write updated_time_list back to worksheet. therefore get start and stop cell for this array
    start_cell_for_times = gspread.utils.rowcol_to_a1(header_rows + 1, user_column)
    stop_cell_for_times = gspread.utils.rowcol_to_a1(header_rows + len(scoreboard_time_list), user_column)

    # upload times
    if updated_times_this_season > 0:
        updated_time_list_formatted = [[time] for time in updated_time_list]
        worksheet.update(f'{start_cell_for_times}:{stop_cell_for_times}', updated_time_list_formatted)
        updated_times += updated_times_this_season
    print(f'    {season}: Updated {updated_times_this_season} times.')

print(f'Updated {updated_times} times in total. congratulations.')
