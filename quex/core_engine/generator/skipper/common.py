from   quex.input.setup import setup         as Setup
import quex.core_engine.utf8                 as utf8
import quex.output.cpp.action_code_formatter as action_code_formatter

line_counter_in_loop = """
#   if defined(QUEX_OPTION_LINE_NUMBER_COUNTING)
    if( input == (QUEX_TYPE_CHARACTER)'\\n' ) { 
        __QUEX_IF_COUNT_LINES_ADD((size_t)1);
    }
#   endif
"""

line_column_counter_in_loop = """
#   if defined(__QUEX_OPTION_COUNTER)
    if( input == (QUEX_TYPE_CHARACTER)'\\n' ) { 
        __QUEX_IF_COUNT_LINES_ADD((size_t)1);
        __QUEX_IF_COUNT_COLUMNS_SET((size_t)0);
        __QUEX_IF_COUNT_COLUMNS(reference_p = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer));
    }
#   endif
"""

def get_character_sequence(Sequence):
    LanguageDB = Setup.language_db

    txt = ""
    comment_txt = ""
    for letter in Sequence:
        comment_txt += "%s, " % utf8.unicode_to_pretty_utf8(letter)
        txt += "0x%X, " % letter
    length_txt = "%i" % len(Sequence)

    return txt, length_txt, comment_txt

def end_delimiter_is_subset_of_indentation_counter_newline(Mode, EndSequence):
    if Mode == None: return False

    indentation_setup = Mode.options.get("indentation")
    if indentation_setup == None: return False

    return indentation_setup.newline_state_machine.get().does_sequence_match(EndSequence)

def get_on_skip_range_open(Mode, CloserSequence):
    """For unit tests 'Mode' may actually be a string, so that we do not
       have to generate a whole mode just to get the 'on_skip_range_open' 
       code fragment.
    """
    if Mode == None: return ""

    txt = ""
    if type(Mode) in [str, unicode]:
        txt += Mode

    elif not Mode.has_code_fragment_list("on_skip_range_open"):
        txt += 'QUEX_ERROR_EXIT("\\nLexical analyzer mode \'%s\':\\n"\n' % Mode.name + \
               '                "End of file occured before closing skip range delimiter!\\n"' + \
               '                "The \'on_skip_range_open\' handler has not been specified.");'
    else:
        closer_string = ""
        for letter in CloserSequence:
            closer_string += utf8.unicode_to_pretty_utf8(letter).replace("'", "")

        code, eol_f = action_code_formatter.get_code(Mode.get_code_fragment_list("on_skip_range_open"))
        txt += "#define Closer \"%s\"\n" % closer_string
        txt += code
        txt += "#undef  Closer\n"
        txt += "RETURN;\n"

    return txt


