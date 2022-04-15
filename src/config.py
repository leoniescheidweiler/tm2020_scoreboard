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

        try:
            assert os.path.exists(self.config_file)
        except AssertionError:
            raise FileNotFoundError(f'{self.config_file} was not found in '
                                    f'{os.path.dirname(os.path.realpath(__file__))}.')
        else:
            config = configparser.ConfigParser()
            config.read(self.config_file)

        for section in config.sections():
            self._data[section] = {}
            for key, val in config.items(section):
                self._data[section][key] = val

        # validate some important values
        try:
            assert self._data['Settings']['uplay_name']
        except AssertionError:
            raise ValueError('uplay_name is empty.')

        try:
            assert os.path.exists(self._data['Settings']['replay_path'])
        except AssertionError:
            raise ValueError('replay_path does not exist.')

        self._data['Settings']['map_packs'] = [map_pack.strip() for map_pack in
                                               self._data['Settings']['map_packs'].split(',') if map_pack]

    def __call__(self, section, key):
        return self._data[section][key]
