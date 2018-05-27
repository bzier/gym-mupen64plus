import numpy as np
import cv2
import os.path


_HEIGHT = 38

SUCCESS = 0
PERCENT_UNDETECTED = 1  # Couldn't detect the % character.
DIGIT_AFTER_PERCENT_UNDETECTED = 2  # Couldn't detect any digits after the % character.
ZERO_NOT_RIGHT_COLOR = 3  # We detected 0, but it was unexpectedly dark, so
                          # we likely just missed some digits to its left.

# Read ideal outlines of characters from saved files. These were generated
# using the same OpenCV method as below, but were picked as especially clean
# examples, ideal for comparisons.
def _initialize_character_pixels_from_files():
    full_path = os.path.dirname(__file__)
    fname = os.path.join(full_path, 'outlines/percent.png')
    percent_pixels = np.asarray(cv2.imread(fname))
    percent_pixels = np.squeeze(percent_pixels[:, :, 0:1])
    percent_pixels = percent_pixels == 0  # True if black, False if white.
    assert len(percent_pixels) == _HEIGHT

    digit_to_pixels = []

    for i in range(10):
        fname = os.path.join(full_path, 'outlines/%d.png' % i)
        digit_pixels =  np.asarray(cv2.imread(fname))
        digit_pixels = np.squeeze(digit_pixels[:, :, 0:1])
        digit_pixels = digit_pixels == 0  # True if black, False if white.
        assert len(digit_pixels) == _HEIGHT
        digit_to_pixels.append(digit_pixels)
    return (percent_pixels, digit_to_pixels)

PERCENT_PIXELS, DIGIT_TO_PIXELS = _initialize_character_pixels_from_files()

class HealthParser(object):
    def __init__(self):
        # Records the color of the inside of 0 when health is 0%.
        self._zero_pixel = None

    # Returns the pixel index and score of the best match of digit_pixels in
    # health_pixels. We start looking with the leftmost pixels of digit_pixels
    # at start_pixel, and stop when those leftmost pixels reach stop_pixel.
    # If it doesn't find a match, returns a negative pixel index.
    def _find_match(self, digit_pixels, health_pixels, start_pixel,
                    stop_pixel):
        mask_len = len(digit_pixels[0])
        inc_or_dec = 1 if stop_pixel > start_pixel else -1
        best_score = -1e9
        best_idx = -1
        for i in range(start_pixel, stop_pixel, inc_or_dec):
            if i < 0 or i + mask_len > len(health_pixels[0]):
                continue
            cut_pixels = health_pixels[:, i:i + mask_len]
            intersection = np.sum(np.logical_and(digit_pixels, cut_pixels))
            union = np.sum(np.logical_or(digit_pixels, cut_pixels))

            score = intersection / float(union)  # Jaccard overlap of the black areas.
            if (score > 0.35 and score > best_score):
                best_score = score
                best_idx = i
        return (best_idx, best_score)

    # Slice the pixels to contain only the section which contains the
    # health.
    def _get_health_screen_section(self, player_num, pixels):
        x_pixel_range = (45, 178) if player_num == 1 else (185, 318)
        y_pixel_range = (400, 400 + _HEIGHT)
        return pixels[y_pixel_range[0]:y_pixel_range[1],
                      x_pixel_range[0]:x_pixel_range[1], :]

    # Uses OpenCV to get the outline of the score. Returned as a boolean array:
    # True if the image is black, False if it is white.
    def _get_score_outline_from_pixels(self, player_num, pixels):
        assert player_num == 1 or player_num == 2
        pixels = self._get_health_screen_section(player_num, pixels)
        x_len = len(pixels[0])
        assert len(pixels) == _HEIGHT
        # Use OpenCV to find the outlines of the numbers in black and white.
        bw = cv2.cvtColor(pixels, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(bw, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 3, 2)
        dilated = cv2.dilate(thresh, np.ones((2,2), np.uint8), iterations = 1)
        return dilated == 0  # True where the pixels are black, False where white.

    # The first time we detect a zero, record its inner pixels. Later, we
    # can determine whether a zero is a true zero or not based on whether
    # it is the correct color.
    def _set_zero_pixel(self, player_num, screen, zero_x_idx):
        pixels = self._get_health_screen_section(player_num, screen)
        self._zero_pixel = pixels[32][13 + zero_x_idx]

    # If the zero pixel doesn't match the first pixel we recorded, it is
    # not a true zero- we missed some digits.
    def _is_zero_reasonable(self, player_num, screen, zero_x_idx):
        pixels = self._get_health_screen_section(player_num, screen)
        zero_pixel = pixels[32][13 + zero_x_idx]
        if np.any(zero_pixel != self._zero_pixel):
            return False
        return True

    # Given the player number (1 and 2) and a screenshot of the game,
    # return the health of the player. Returns a pair. The first value returned is
    # the health if it is detected, or else -1. The second value returned is
    # an error code, one of the three above.
    def GetHealth(self, player_num, screen):
        pixels = self._get_score_outline_from_pixels(player_num, screen)
        percent_len = len(PERCENT_PIXELS[0])
        x_len = len(pixels[1])
        # First find the %, and work left from there.
        # X range below hand tuned to properly find the % in the smallest case (1%).
        percent_match = self._find_match(
            PERCENT_PIXELS, pixels, x_len // 2 - 9, x_len - percent_len)
        if percent_match[0] == -1:
            return (-1, PERCENT_UNDETECTED)
        start_match_px = percent_match[0]
        multiplier = 1
        digits_found = 0
        first_digit_x = -1
        # Search for up to 3 digits. Look to the left of the most recently found
        # character.
        for i in range(3):  # Need to find potentially 3 digits.
            best_digit_match = (-1, -1e9)
            best_digit = -1
            start_idx = 1 if i == 2 else 0  # Don't search for 0 in the final digit.
            for digit in range(start_idx, 10):
                digit_pixels = DIGIT_TO_PIXELS[digit]
                digit_len = len(digit_pixels[0])
                # These have been tuned a bit to give the best possible values.
                # We may see tiny decreases from making them too large as we have
                # false positive digits identified, but things get really bad
                # if they get much smaller.
                start_search = start_match_px - digit_len
                end_search = start_match_px - 4 - digit_len
                digit_match = self._find_match(
                    digit_pixels, pixels, start_search, end_search)
                if digit_match[1] > best_digit_match[1]:
                    best_digit_match = digit_match
                    best_digit = digit
                    if i == 0:
                        first_digit_x = best_digit_match[0]
            if best_digit_match[0] >= 0:
                digits_found += best_digit * multiplier
                start_match_px = best_digit_match[0]
            elif i == 0:
                return (-1, DIGIT_AFTER_PERCENT_UNDETECTED)
            else:
                break
            multiplier *= 10
        if self._zero_pixel is None and digits_found == 0:
            self._set_zero_pixel(player_num, screen, first_digit_x)
        elif (digits_found == 0 and
              not self._is_zero_reasonable(player_num, screen,
                                           first_digit_x)):
            return (-1, ZERO_NOT_RIGHT_COLOR)
        return (digits_found, SUCCESS)

def main():  # Can be run as a test on the screenshots_below
    # Screenshots with health identified correctly.
    correct = 0
    # Screenshots which returned no value.
    no_val_returned = 0
    # Screenshots which were incorrect, but would be easy to identify were
    # incorrect in the context of the game.
    incorrect_easy_to_identify = 0
    # Screenshots which were incorrect, but might be harder to identify in
    # gameplay
    incorrect_hard_to_identify = 0
    total = 0
    for p in [1, 2]:
        for h in range(0, 999):
            screenshot_fname = "screenshots/p%d_health_%03d.png" % (p, h)
            img = cv2.imread(screenshot_fname)
            if img is not None:
                pixels = np.asarray(img)
                health, error = HealthParser().GetHealth(p, pixels)
                total += 1
                if health == -1:
                    no_val_returned += 1
                elif health == h:
                    correct += 1
                else:
                    # If health increases too much, or decreases to a nonzero
                    # value, this is easy to identify in gameplay.
                    if health > 40 + h or (health < h and health != 0):
                        incorrect_easy_to_identify += 1
                    else:
                        incorrect_hard_to_identify += 1
    t = float(total) * 0.01
    print("Correct values: %d, %0.2f%%" % (correct, correct / t))
    print("No value returned:  %d, %0.2f%%" % (
        no_val_returned, no_val_returned / t))
    print("Incorrect, but easy to account for in game: %d, %0.2f%%" % (
        incorrect_easy_to_identify, incorrect_easy_to_identify / t))
    print("Incorrect, harder to identify in game %d, %0.2f%%:" % (
        incorrect_hard_to_identify, incorrect_hard_to_identify / t))

if __name__ == '__main__':
    main()
