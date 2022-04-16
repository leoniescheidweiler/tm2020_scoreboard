import os
import re

from .config import Config


class Replay:

    """
    Container which stores information about a given replay file.
    """

    file_template = '{uplay_name}_{track_name}_PersonalBest_TimeAttack.Replay.Gbx'

    def __init__(self, track_name):
        config = Config()
        self.file_path = os.path.join(config('Settings', 'replay_path'),
                                      self.file_template.format(uplay_name=config('Settings', 'uplay_name'),
                                                                track_name=track_name))
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file.readlines():
                if 'times best' in line:
                    self.time_ms = float(re.search(r'times best="(\d+)"', line).group(1))
                    self.time_s = self.time_ms / 1000
                    break
