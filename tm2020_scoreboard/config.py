import configparser
import os


class Config:

    """
    This class stores all the values from the specified config_file and validates them. Values are retrieved
    with a function call on an instance.
    """

    config_file = 'config.ini'

    def __init__(self):

        self._data = {}
        config_dir = os.path.dirname(os.path.realpath(__file__))

        try:
            assert os.path.exists(os.path.join(config_dir, self.config_file))
        except AssertionError:
            raise FileNotFoundError(f'{self.config_file} was not found in '
                                    f'{os.path.dirname(os.path.realpath(__file__))}.')
        else:
            config = configparser.ConfigParser()
            config.read(os.path.join(config_dir, self.config_file))

        for section in config.sections():
            self._data[section] = {}
            for key, val in config.items(section):
                self._data[section][key] = val

        # validate some important values
        try:
            assert self._data['Settings']['uplay_name']
        except AssertionError:
            raise ValueError('uplay_name is empty.')

        if self._data['Settings']['replay_path']:
            try:
                assert os.path.exists(self._data['Settings']['replay_path'])
            except AssertionError:
                raise ValueError('replay_path does not exist.')
        else:
            self._data['Settings']['replay_path'] = os.path.expanduser(r'~/Documents/Trackmania2020/Replays/Autosaves')

        self._data['Settings']['map_packs'] = [map_pack.strip() for map_pack in
                                               self._data['Settings']['map_packs'].split(',') if map_pack]

    def __call__(self, section, key):
        return self._data[section][key]
