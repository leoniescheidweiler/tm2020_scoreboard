import argparse

from tm2020_scoreboard.google_spreadsheet import GoogleSpreadsheet


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Provides command line functionality for tm2020_scoreboard.')
    parser.add_argument('-s', '--synchronize', action='store_true', help='Synchronizes your replay times.')
    parser.add_argument('-cw', '--create_worksheets', nargs='+', help='Creates worksheets for the given map pack urls.')
    args = parser.parse_args()
    gs = GoogleSpreadsheet()
    if args.synchronize:
        gs.synchronize_replay_times()
    if args.create_worksheets:
        gs.create_worksheets_for_map_packs(args.create_worksheets)
