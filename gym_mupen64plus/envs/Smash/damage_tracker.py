from gym_mupen64plus.envs.Smash \
  import damage_parser

_NUM_DMGS_TO_DETECT = 3  # How many times we need to detect a damage to update.

# When the player dies, his damage disappears for a few frames before
# resetting to zero. We detect this to detect deaths, which is necessary
# because you can die at 0% damage, and we still want to penalize this.
_MISSING_PERCENTS_IN_ROW_THRESHOLD = 12

# This class tracks damage observations, making sure the observations
# make sense, and reporting the likely confident current damage. Note that
# reported damage may be slightly delayed to ensure we are confident in
# the reported damage value.
# Note: We recommend using a frame_skip no higher than 2, or it may be
# unreliable at detecting deaths at 0 damage.
class DamageTracker(object):
    def __init__(self, frame_skip, playernum=1):
        self._damage_parser = damage_parser.DamageParser()
        # How many frames are skipped at every update.
        self._frame_skip = frame_skip
        self._playernum = playernum
        self._curr_dmg = 0
        # Value of damage last time reward was updated.
        self._dmg_at_last_reward = 0
        # Cache of recently detected damages.
        self._recent_damages = [0] * _NUM_DMGS_TO_DETECT
        # Counter for _MISSING_PERCENTS_IN_ROW_THRESHOLD.
        self._missing_percents_in_row = 0
        # Whether to report death to reward function on next update.
        self._has_processed_death = False
        # Whether we have met the _MISSING_PERCENTS_IN_ROW_THRESHOLD
        # and thus can process a death and resetting the damage to 0%.
        self._met_percent_threshold = False

    # Record a damage observation from the screen.
    def observe_damage(self, screen):
        dmg_observation, error = self._damage_parser.GetDamage(self._playernum, screen)
        if error == damage_parser.SUCCESS:
            assert dmg_observation >= 0 and dmg_observation <= 999
            # Reset this counter, since we have detected a % sign.
            self._missing_percents_in_row = 0
            if dmg_observation != 0:
                if self._recent_damages[-1] != 0:
                    # Detected two nonzeroes in a row. There likely
                    # wasn't an actual death, so reset
                    # _met_percent_threshold.
                    self._met_percent_threshold = False
            self._recent_damages.pop(0)
            self._recent_damages.append(dmg_observation)
            # See how if everything in the cache matches the most recent
            # observation
            num_match_measurements = sum(
                d == dmg_observation for d in self._recent_damages)
            # We can update the damage if the following conditions are met:
            # 1) We have _NUM_DMGS_TO_DETECT consistent observations
            # 2)
            #   a) The damage is nonzero and the damage increased
            # OR
            #   b) Damage reset to zero and we have met the number of
            #      nondetected % threshold.
            if (num_match_measurements == _NUM_DMGS_TO_DETECT and
                ((dmg_observation != 0 and dmg_observation >= self._curr_dmg) or
                 (dmg_observation == 0 and self._met_percent_threshold))):
                old_dmg = self._curr_dmg
                self._curr_dmg = dmg_observation
                if dmg_observation == 0:
                    # If the damage is zero, we have processed a death.
                    self._met_percent_threshold = False
                    self._has_processed_death = True
                    # Any damage taken since the last reward update needs
                    # to be accounted for, potentially by setting it below
                    # 0.
                    self._dmg_at_last_reward -= old_dmg
        elif error ==  damage_parser.PERCENT_UNDETECTED:
            # We couldn't detect a % character. If this happens a lot,
            # it means the character likely died.
            self._missing_percents_in_row += 1
            if (self._missing_percents_in_row * (self._frame_skip + 1) >=
                _MISSING_PERCENTS_IN_ROW_THRESHOLD):
                 self._met_percent_threshold = True
        else:
            # The other two errors are that we couldn't detect any digit
            # to the left of the % sign, or that a zero with the wrong
            # color was returned. Both of these involve a detected % sign.
            self._missing_percents_in_row = 0

    # Return a pair. The first value is a bool, indicating whether a death
    # was processed since the last time this function was called. The
    # second is the total damage taken since the last time this function
    # was called.
    def get_death_and_delta_dmg_for_reward(self):
        damage_taken = self._curr_dmg - self._dmg_at_last_reward
        has_died = self._has_processed_death
        self._has_processed_death = False
        self._dmg_at_last_reward = self._curr_dmg
        return (has_died, damage_taken)

    # Return the current damage.
    def get_curr_damage(self):
        return self._curr_dmg
