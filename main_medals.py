from bs4 import BeautifulSoup
from requests_html import HTMLSession

import sys
import gspread

LINKS = {
    #'Training': 'https://trackmania.exchange/mappack/view/40/training',
    #'Summer 2020': 'https://trackmania.exchange/mappack/view/42/summer-2020',
    #'Fall 2020': 'https://trackmania.exchange/mappack/view/162/fall-2020',
    #'Winter 2021': 'https://trackmania.exchange/mappack/view/314/winter-2021',
    #'Spring 2021': 'https://trackmania.exchange/mappack/view/467/spring-2021',
    #'Summer 2021': 'https://trackmania.exchange/mappack/view/655/summer-2021',
    #'Fall 2021': 'https://trackmania.exchange/mappack/view/918/fall-2021',
    'Winter 2022': 'https://trackmania.exchange/mappack/view/1179/winter-2022',
}

if len(LINKS.keys()) > 1:
    sys.exit('currently only supports single season')


def to_seconds(time):
    minutes, seconds = time.split(':')
    minutes = int(minutes)
    seconds = float(seconds)
    return round(60 * minutes + seconds, 3)


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 OPR/72.0.3815.487'
session = HTMLSession()

track_info = {}

for season in LINKS:
    track_info[season] = {}
    season_link = LINKS[season]
    rows = []
    response = session.get(season_link, headers={'User-Agent': USER_AGENT})
    response.html.render(sleep=2, timeout=20,
                         script='document.getElementsByClassName("windowv2-buttonbar windowv2-buttonbar-center")[0].getElementsByTagName("a")[1].click()')
    soup = BeautifulSoup(response.html.html, features='lxml')
    rows += soup.findAll('tr', {'class': 'WindowTableCell1v2 with-hover has-image'}) # format until fall 2021
    rows += soup.findAll('tr', {'class': 'WindowTableCell2v2 with-hover has-image'}) # format until fall 2021
    rows += soup.findAll('div', {'class': 'trackgrid-element'})                      # format starting winter 2022 (with picture for each track)
    response.html.render(sleep=2, timeout=20,
                         script='document.getElementsByClassName("windowv2-buttonbar windowv2-buttonbar-center")[0].getElementsByTagName("a")[2].click()')
    soup = BeautifulSoup(response.html.html, features='lxml')
    rows += soup.findAll('tr', {'class': 'WindowTableCell1v2 with-hover has-image'})
    rows += soup.findAll('tr', {'class': 'WindowTableCell2v2 with-hover has-image'})
    rows += soup.findAll('div', {'class': 'trackgrid-element'})

    for row in rows:
        if int(season[-2:]) < 22:
            row = row.findAll('td', {'class': 'cell-ellipsis'})[0]
            track_name = row.findAll('a')[0].getText()
            track_id = row.findAll('td')[0].getText() # old format
        else:
            row = row.findAll('div', {'class': 'trackgrid-title cell-ellipsis'})[0]
            track_name = row.findAll('a')[0].getText()
            track_id = int(track_name[-2:]) # new format starting winter 2022, THIS BREAKS TRACK OF THE DAY FUNCTIONALITY

        print(track_id, track_name)

        track_link = 'https://trackmania.exchange' + row.findAll('a')[0].get('href')
        response = session.get(track_link, headers={'User-Agent': USER_AGENT})
        response.html.render(sleep=.2, timeout=20)
        soup = BeautifulSoup(response.html.html, features='lxml')
        time_data = soup.findAll('abbr', {'class': 'tipsy-n-html dark-grey'})[0].get('original-title')
        time_data = time_data.split('<br/>')[1:]
        time_data = [to_seconds(time.split(' ')[1]) for time in time_data]

        author = time_data[0]
        gold = time_data[1]
        silver = time_data[2]
        bronze = time_data[3]

        track_info[season][track_name] = {}
        track_info[season][track_name]['id'] = track_id
        track_info[season][track_name]['times'] = [bronze, silver, gold, author]

print(track_info)

gc = gspread.service_account(filename='credentials.json')
spreadsheet = gc.open('TrackMania 2020')


for season in track_info.keys():
    try:
        worksheet = spreadsheet.worksheet(season)
    except gspread.exceptions.WorksheetNotFound:
        sys.exit(f'Season {season} does not have a worksheet.')

    max_id = max([int(track_info[season][track]['id']) for track in track_info[season].keys()])
    formatted_track_info = [[0, 0, 0, 0, 'Error']]*max_id

    for track in track_info[season].keys():
        track_name = track
        track_id = int(track_info[season][track]['id'])
        bronze, silver, gold, author = track_info[season][track]['times']

        header_rows = 2
        track_row = track_id + header_rows

        bronze_column = 1
        silver_column = 2
        gold_column = 3
        author_column = 4
        track_name_column = 5

        formatted_track_info[track_id-1] = [bronze, silver, gold, author, track_name]

    top_left_cell = gspread.utils.rowcol_to_a1(header_rows + 1, 1)
    bottom_right_cell = gspread.utils.rowcol_to_a1(header_rows + max_id, track_name_column)
    worksheet.batch_update([{'range': f'{top_left_cell}:{bottom_right_cell}', 'values': formatted_track_info}])
