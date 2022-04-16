import argparse

from .google_spreadsheet import GoogleSpreadsheet


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Provides command line functionality for tm2020_scoreboard.')
    action_arg = parser.add_argument('action', type=str, help='Choose between "synchronize" and "create_worksheets".')
    args = parser.parse_args()
    if args.action.lower() == 'synchronize':
        GoogleSpreadsheet().synchronize_replay_times()
    elif args.action.lower() == 'create_worksheets':
        # TODO: add command line functionality for creating worksheets
        raise NotImplementedError
    else:
        parser.error(f'{args.action} is an invalid argument. {action_arg.help}')
