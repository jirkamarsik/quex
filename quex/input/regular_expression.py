from StringIO import StringIO
from   quex.input.setup import setup as Setup

from   quex.frs_py.file_in                 import EndOfStreamException, error_msg
from   quex.exception                      import RegularExpressionException
from   quex.core_engine.interval_handling  import NumberSet, Interval
from   quex.core_engine.state_machine.core import StateMachine 
import quex.lexer_mode                          as lexer_mode
import quex.core_engine.regular_expression.core as regex
import quex.core_engine.regular_expression.character_set_expression as charset_expression
import quex.core_engine.regular_expression.snap_character_string    as snap_character_string

def parse(fh, AllowNothingIsFineF=False):

    start_position = fh.tell()
    try:
        # (*) parse regular expression, build state machine
        pattern_state_machine = regex.do(fh, lexer_mode.shorthand_db, 
                                         DOS_CarriageReturnNewlineF = Setup.dos_carriage_return_newline_f,
                                         AllowNothingIsNecessaryF   = AllowNothingIsFineF)


    except RegularExpressionException, x:
        fh.seek(start_position)
        error_msg("Regular expression parsing:\n" + x.message, fh)

    except EndOfStreamException:
        fh.seek(start_position)
        error_msg("End of file reached while parsing regular expression.", fh)

    return __post_process(fh, start_position, pattern_state_machine, ReturnRE_StringF=True)

def parse_character_string(Txt_or_File, PatternStringF=False):

    sh, sh_ref, start_position = __prepare_text_or_file_stream(Txt_or_File)

    try:
        # -- parse regular expression, build state machine
        state_machine = snap_character_string.do(sh)
        state_machine = regex.__clean_and_validate(state_machine, AllowNothingIsNecessaryF=False, fh=sh)

        if state_machine == None:
            error_msg("No valid regular character string expression detected.", sh_ref)

    except RegularExpressionException, x:
        error_msg("Regular expression parsing:\n" + x.message, sh_ref)

    except EndOfStreamException:
        if sh_ref != -1: sh_ref.seek(start_position)
        error_msg("End of character string reached while parsing.", sh_ref)

    return __post_process(sh, start_position, state_machine, PatternStringF)

def parse_character_set(Txt_or_File, PatternStringF=False):

    sh, sh_ref, start_position = __prepare_text_or_file_stream(Txt_or_File)

    try:
        # -- parse regular expression, build state machine
        character_set = charset_expression.snap_set_expression(sh, lexer_mode.shorthand_db)

        if character_set == None:
            error_msg("No valid regular character set expression detected.", sh_ref)

        # -- character set is not supposed to contain buffer limit code
        if character_set.contains(Setup.buffer_limit_code):
            character_set.cut_interval(Interval(Setup.buffer_limit_code))
        if character_set.contains(Setup.path_limit_code):
            character_set.cut_interval(Interval(Setup.path_limit_code))

    except RegularExpressionException, x:
        error_msg("Regular expression parsing:\n" + x.message, sh_ref)

    except EndOfStreamException:
        if sh_ref != -1: sh_ref.seek(start_position)
        error_msg("End of character set expression reached while parsing.", sh_ref)

    return __post_process(sh, start_position, character_set, PatternStringF)

def __prepare_text_or_file_stream(Txt_or_File):
    if Txt_or_File.__class__ in [file, StringIO]:
        sh       = Txt_or_File
        sh_ref   = sh
    else:
        sh     = StringIO(Txt_or_File)
        sh_ref = -1

    return sh, sh_ref, sh.tell()

def __post_process(fh, StartPosition, object, ReturnRE_StringF):
    assert    object == None                   \
           or isinstance(object, StateMachine) \
           or isinstance(object, NumberSet)

    if isinstance(fh, StringIO):
        regular_expression = ""
    else:
        end_position = fh.tell()
        fh.seek(StartPosition)
        regular_expression = fh.read(end_position - StartPosition)
        if regular_expression == "":
            regular_expression = fh.read(1)
            fh.seek(-1, 1)

    # (*) error in regular expression?
    if object == None:
        error_msg("No valid regular expression detected, found '%s'." % regular_expression, fh)

    # NOT: Do not transform here, since transformation might happen twice when patterns
    #      are defined and when they are replaced.
    if ReturnRE_StringF: return regular_expression, object
    else:                return object


