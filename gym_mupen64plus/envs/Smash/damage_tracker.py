import health_parser

_NUM_DMGS_TO_DETECT = 3
_NUM_DMGS_TO_DETECT_ZERO = 10
_MISSING_PERCENTS_IN_ROW_THRESHOLD = 12

class DamageTracker(object):
    def __init__(self, playernum=1):
        self._playernum = playernum
        self._curr_dmg = 0
        self._dmg_at_last_reward = 0
        self._recent_damages = [0] * _NUM_DMGS_TO_DETECT_ZERO
        self._missing_percents_in_row = 0
        self._has_processed_death = False
        self._met_percent_threshold = False
        self._nonzeroes_detected_in_row = 0

    def observe_damage(self, pixels):
        dmg_observation, error = health_parser.GetHealth(
            self._playernum, pixels)
        if error == health_parser.SUCCESS:
            assert dmg_observation >= 0 and dmg_observation <= 999
            self._missing_percents_in_row = 0
            if dmg_observation == 0:
                self._nonzeroes_detected_in_row = 0
                num_measurements_required = _NUM_DMGS_TO_DETECT_ZERO
            else:
                self._nonzeroes_detected_in_row += 1
                if self._recent_damages[-1] != 0:  # Detected two nonzeroes in a row.
                    self._met_percent_threshold = False
                num_measurements_required = _NUM_DMGS_TO_DETECT
            self._recent_damages.pop(0)
            self._recent_damages.append(dmg_observation)
            num_match_measurements = sum(
                d == dmg_observation for d in
                self._recent_damages[::-1][:num_measurements_required])
            if (num_match_measurements == num_measurements_required and
                (dmg_observation == 0 or dmg_observation >= self._curr_dmg) and
                (dmg_observation != 0 or self._met_percent_threshold)):
                self._curr_dmg = dmg_observation
                if dmg_observation == 0:
                    self._met_percent_threshold = False
                    self._has_processed_death = True
                    self._dmg_at_last_reward = 0
        elif error ==  health_parser.PERCENT_UDETECTED:
            self._missing_percents_in_row += 1
            if (self._missing_percents_in_row >=
                _MISSING_PERCENTS_IN_ROW_THRESHOLD):
                 self._met_percent_threshold = True
        else:
            self._missing_percents_in_row = 0

    def get_death_and_delta_dmg_for_reward(self):
        damage_taken = self._curr_dmg - self._dmg_at_last_reward
        has_died = self._has_processed_death
        self._has_processed_death = False
        self._dmg_at_last_reward = self._curr_dmg
        return (has_died, damage_taken)

    def get_curr_damage(self):
        return self._curr_dmg
