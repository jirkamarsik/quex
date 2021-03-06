import sys
import StringIO
import quex.core_engine.utf8 as utf8
import quex.core_engine.regular_expression.snap_backslashed_character as snap_backslashed_character
from quex.core_engine.interval_handling  import *
from quex.exception                      import RegularExpressionException
from quex.input.setup import setup as Setup



class Tracker:
    def __init__(self):
        self.match_set  = NumberSet()
        self.negation_f = False
 
    def consider_interval(self, Begin, End):
        if Begin > End:
            raise RegularExpressionException("Character range: '-' requires character with 'lower code' to preceed\n" + \
                                             "found range '%s-%s' which corresponds to %i-%i as unicode code points." % \
                                             (utf8.map_unicode_to_utf8(Begin), utf8.map_unicode_to_utf8(End), Begin, End))

        self.match_set.add_interval(Interval(Begin, End))

    def consider_letter(self, CharCode):
        self.consider_interval(CharCode, CharCode+1)
 
def do_string(UTF8_String):
    return do(StringIO.StringIO(UTF8_String))

class DoubleQuoteChecker:
    def __init__(self):
        self.quote_n = 0

    def do(self, CharacterCode):
        if CharacterCode != ord("\""): return
        self.quote_n += 1
        if self.quote_n != 2: return
        raise RegularExpressionException(
                "Character '\"' appears twice in character range [ ... ] expression.\n"
                "You cannot exempt characters this way. Please, use backslash or\n"
                "split the character range expression.")


def do(sh):
    """Transforms an expression of the form [a-z0-9A-Z] into a NumberSet of
       code points that corresponds to the characters and character ranges mentioned.
    """
    assert     sh.__class__.__name__ == "StringIO" \
            or sh.__class__.__name__ == "file"

    def __check_letter(stream, letter):
        position = stream.tell()
        if stream.read(1) == letter: return True
        else:                        stream.seek(position); return False

    # check, if the set is thought to be inverse (preceeded by '^')
    tracker = Tracker()

    if __check_letter(sh, "^"): tracker.negation_f = True

    char_code     = None
    quote_checker = DoubleQuoteChecker() # Checks for " appearing twice. Some users did use
    #                                    # constructs such as "-" and ended up in confusing behavior.
    while char_code != 0xFF:
        char_code = utf8.__read_one_utf8_code_from_stream(sh)

        quote_checker.do(char_code)
        if char_code == ord("-"):
            raise RegularExpressionException("Character range operator '-' requires a preceding character as in 'a-z'.")
        elif char_code == 0xFF: 
            raise RegularExpressionException("Missing closing ']' in character range expression.")
        elif char_code == ord("]"):
            break
        elif char_code == ord("\\"):
            char_code = snap_backslashed_character.do(sh)

        if not __check_letter(sh, "-"): 
            # (*) Normal character
            tracker.consider_letter(char_code)
        else:
            # (*) Character range:  'character0' '-' 'character1'
            char_code_2 = utf8.__read_one_utf8_code_from_stream(sh)
            quote_checker.do(char_code_2)
            if char_code_2 in [0xFF, ord(']')]: 
                raise RegularExpressionException("Character range: '-' requires a character following '-'.")
            elif char_code == ord("-"):
                raise RegularExpressionException("Character range operator '-' followed by '-'.")
            elif char_code_2 == ord("\\"): 
                char_code_2 = snap_backslashed_character.do(sh)  

            # value denotes 'end', i.e first character outside the interval => add 1
            if char_code == char_code_2:
                utf8_string = utf8.map_unicode_to_utf8(char_code)
                raise RegularExpressionException("Character range '%s-%s' has only one element.\n" \
                                                 % (utf8_string, utf8_string) + \
                                                 "In this case avoid range expression for clarity.")
            tracker.consider_interval(char_code, char_code_2 + 1)

    if tracker.negation_f: 
        result = tracker.match_set.inverse()
        if Setup.get_character_value_limit() != sys.maxint:
            result.intersect_with(Interval(0, Setup.get_character_value_limit()))
        return result
    else:                  
        return tracker.match_set


