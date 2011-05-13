from   quex.core_engine.generator.skipper.common    import *
import quex.core_engine.state_machine.index         as     sm_index
from   quex.input.setup                             import setup as Setup
from   quex.frs_py.string_handling                  import blue_print
from   quex.core_engine.generator.languages.address import __nice, get_label
from   quex.core_engine.generator.languages.variable_db import Variable
import quex.lexer_mode                              as     lexer_mode

def do(Data):

    LanguageDB      = Setup.language_db
    OpeningSequence = Data["opener_sequence"]
    ClosingSequence = Data["closer_sequence"]
    ModeName        = Data["mode_name"]

    assert type(ModeName) in [str, unicode]
    assert Data.has_key("indentation_counter_terminal_id")
    
    indentation_counter_terminal_id = Data["indentation_counter_terminal_id"]

    Mode = None
    if ModeName != "":
        Mode = lexer_mode.mode_db[ModeName]

    code_str, db = get_skipper(OpeningSequence, ClosingSequence, 
                               Mode=Mode, 
                               IndentationCounterTerminalID=indentation_counter_terminal_id) 

    txt =    "{\n"                                          \
           + LanguageDB["$comment"]("Range skipper state")  \
           + code_str                                       \
           + "\n}\n"

    return code_str, db

template_str = """
{
    const QUEX_TYPE_CHARACTER   Opener$$SKIPPER_INDEX$$[]  = { $$OPENER$$ }; /* $$OPENER_COMMENT$$ */
    const QUEX_TYPE_CHARACTER*  Opener$$SKIPPER_INDEX$$End = Opener$$SKIPPER_INDEX$$ + $$OPENER_LENGTH$$;
    const QUEX_TYPE_CHARACTER*  Opener$$SKIPPER_INDEX$$_it = Opener$$SKIPPER_INDEX$$;
    const QUEX_TYPE_CHARACTER   Closer$$SKIPPER_INDEX$$[]  = { $$CLOSER$$ }; /* $$CLOSER_COMMENT$$ */
    const QUEX_TYPE_CHARACTER*  Closer$$SKIPPER_INDEX$$End = Closer$$SKIPPER_INDEX$$ + $$CLOSER_LENGTH$$;
    const QUEX_TYPE_CHARACTER*  Closer$$SKIPPER_INDEX$$_it = Closer$$SKIPPER_INDEX$$;

    QUEX_TYPE_CHARACTER*        text_end = QUEX_NAME(Buffer_text_end)(&me->buffer);
$$LC_COUNT_COLUMN_N_POINTER_DEFINITION$$

$$ENTRY$$:
    QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
    __quex_assert(QUEX_NAME(Buffer_content_size)(&me->buffer) >= $$OPENER_LENGTH$$ );

    /* NOTE: If _input_p == end of buffer, then it will drop out immediately out of the
     *       loop below and drop into the buffer reload procedure.                      */

    /* Loop eating characters: Break-out as soon as the First Character of the Delimiter
     * (FCD) is reached. Thus, the FCD plays also the role of the Buffer Limit Code. There
     * are two reasons for break-out:
     *    (1) we reached a limit (end-of-file or buffer-limit)
     *    (2) there was really the FCD in the character stream
     * This must be distinguished after the loop was exited. But, during the 'swallowing' 
     * we are very fast, because we do not have to check for two different characters.  */
    while( 1 + 1 == 2 ) {
        $$INPUT_GET$$ 
        if( input == QUEX_SETTING_BUFFER_LIMIT_CODE ) {
            goto $$GOTO_RELOAD$$;
        }
        if( input == *Closer$$SKIPPER_INDEX$$_it ) {
            ++Closer$$SKIPPER_INDEX$$_it;
            if( Closer$$SKIPPER_INDEX$$_it == Closer$$SKIPPER_INDEX$$End ) {
                if( counter == 0 ) {
                    /* NOTE: The initial state does not increment the input_p. When it detects that
                     * it is located on a buffer border, it automatically triggers a reload. No 
                     * need here to reload the buffer. */
                    $$INPUT_P_INCREMENT$$ /* Now, BLC cannot occur. See above. */
                    $$LC_COUNT_END_PROCEDURE$$
                    /* No need for re-entry preparation. Acceptance flags and modes are untouched after skipping. */
                    $$GOTO_AFTER_END_OF_SKIPPING$$ /* End of range reached. */
                }
                --counter;
                Opener$$SKIPPER_INDEX$$_it = (QUEX_TYPE_CHARACTER*)Opener$$SKIPPER_INDEX$$;
                Closer$$SKIPPER_INDEX$$_it = (QUEX_TYPE_CHARACTER*)Closer$$SKIPPER_INDEX$$;
                goto CONTINUE_$$SKIPPER_INDEX$$;
            }
        } else {
            Closer$$SKIPPER_INDEX$$_it = (QUEX_TYPE_CHARACTER*)Closer$$SKIPPER_INDEX$$;
        }
        if( input == *Opener$$SKIPPER_INDEX$$_it ) {
            ++Opener$$SKIPPER_INDEX$$_it;
            if( Opener$$SKIPPER_INDEX$$_it == Opener$$SKIPPER_INDEX$$End ) {
                ++counter;
                Opener$$SKIPPER_INDEX$$_it = (QUEX_TYPE_CHARACTER*)Opener$$SKIPPER_INDEX$$;
                Closer$$SKIPPER_INDEX$$_it = (QUEX_TYPE_CHARACTER*)Closer$$SKIPPER_INDEX$$;
                goto CONTINUE_$$SKIPPER_INDEX$$;
            }
        } else {
            Opener$$SKIPPER_INDEX$$_it = (QUEX_TYPE_CHARACTER*)Opener$$SKIPPER_INDEX$$;
        }
CONTINUE_$$SKIPPER_INDEX$$:
$$LC_COUNT_IN_LOOP$$
        $$INPUT_P_INCREMENT$$ /* Now, BLC cannot occur. See above. */
    }

$$RELOAD$$:
    QUEX_BUFFER_ASSERT_CONSISTENCY_LIGHT(&me->buffer);
    /* -- When loading new content it is checked that the beginning of the lexeme
     *    is not 'shifted' out of the buffer. In the case of skipping, we do not care about
     *    the lexeme at all, so do not restrict the load procedure and set the lexeme start
     *    to the actual input position.                                                    */
    $$MARK_LEXEME_START$$

$$LC_COUNT_BEFORE_RELOAD$$
    if( QUEX_NAME(Buffer_is_end_of_file)(&me->buffer) == false ) {
        QUEX_NAME(buffer_reload_forward_LA_PC)(&me->buffer, &last_acceptance_input_position,
                                               post_context_start_position, PostContextStartPositionN);
        /* Recover '_input_p' from lexeme start 
         * (inverse of what we just did before the loading) */
        me->buffer._input_p = me->buffer._lexeme_start_p;
        /* After reload, we need to increment _input_p. That's how the game is supposed to be played. 
         * But, we recovered from lexeme start pointer, and this one does not need to be incremented. */
        text_end = QUEX_NAME(Buffer_text_end)(&me->buffer);
$$LC_COUNT_AFTER_RELOAD$$
        QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
        goto $$GOTO_ENTRY$$;          /* End of range reached.             */
    }
    /* Here, either the loading failed or it is not enough space to carry a closing delimiter */
    me->buffer._input_p = me->buffer._lexeme_start_p;
    $$ON_SKIP_RANGE_OPEN$$
}
"""

def get_skipper(OpenerSequence, CloserSequence, Mode=None, IndentationCounterTerminalID=None, OnSkipRangeOpenStr=""):
    assert OpenerSequence.__class__  == list
    assert len(OpenerSequence)       >= 1
    assert map(type, OpenerSequence) == [int] * len(OpenerSequence)
    assert CloserSequence.__class__  == list
    assert len(CloserSequence)       >= 1
    assert map(type, CloserSequence) == [int] * len(CloserSequence)
    assert OpenerSequence != CloserSequence

    LanguageDB    = Setup.language_db

    skipper_index = sm_index.get()

    opener_str, opener_length_str, opener_comment_str = get_character_sequence(OpenerSequence)
    closer_str, closer_length_str, closer_comment_str = get_character_sequence(CloserSequence)

    if not end_delimiter_is_subset_of_indentation_counter_newline(Mode, CloserSequence):
        goto_after_end_of_skipping_str = "goto %s;" % get_label("$start", U=True)
    else:
        # If there is indentation counting involved, then the counter's terminal id must
        # be determined at this place.
        assert IndentationCounterTerminalID != None
        # If the ending delimiter is a subset of what the 'newline' pattern triggers 
        # in indentation counting => move on to the indentation counter.
        goto_after_end_of_skipping_str = "goto %s;" % get_label("$terminal-direct", 
                                                                IndentationCounterTerminalID, U=True)

    if OnSkipRangeOpenStr != "": on_skip_range_open_str = OnSkipRangeOpenStr
    else:                        on_skip_range_open_str = get_on_skip_range_open(Mode, CloserSequence)

    local_variable_db = { 
        "counter":     Variable("counter", "size_t", None, "0"),
        "QUEX_OPTION_COLUMN_NUMBER_COUNTING/reference_p": 
                       Variable("reference_p", 
                                "QUEX_TYPE_CHARACTER_POSITION", 
                                None,
                                "(QUEX_TYPE_CHARACTER_POSITION)0x0", 
                                "QUEX_OPTION_COLUMN_NUMBER_COUNTING")
    }
    reference_p_def = "    __QUEX_IF_COUNT_COLUMNS(reference_p = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer));\n"

    reference_p_def = "    __QUEX_IF_COUNT_COLUMNS(reference_p = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer));\n"
    before_reload   = "    __QUEX_IF_COUNT_COLUMNS_ADD((size_t)(QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer)\n" + \
                      "                                - reference_p));\n" 
    after_reload    = "        __QUEX_IF_COUNT_COLUMNS(reference_p = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer));\n"

    if CloserSequence[-1] == ord('\n'):
        end_procedure  = "       __QUEX_IF_COUNT_LINES_ADD((size_t)1);\n"
        end_procedure += "       __QUEX_IF_COUNT_COLUMNS_SET((size_t)1);\n"
    else:
        end_procedure = "        __QUEX_IF_COUNT_COLUMNS_ADD((size_t)(QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer)\n" + \
                        "                                    - reference_p));\n" 

    code_str = blue_print(template_str,
                          [
                           ["$$SKIPPER_INDEX$$",   __nice(skipper_index)],
                           #
                           ["$$OPENER$$",          opener_str],
                           ["$$OPENER_LENGTH$$",   opener_length_str],
                           ["$$OPENER_COMMENT$$",  opener_comment_str],
                           ["$$CLOSER$$",          closer_str],
                           ["$$CLOSER_LENGTH$$",   closer_length_str],
                           ["$$CLOSER_COMMENT$$",  closer_comment_str],
                           # 
                           ["$$INPUT_P_INCREMENT$$",              LanguageDB["$input/increment"]],
                           ["$$INPUT_P_DECREMENT$$",              LanguageDB["$input/decrement"]],
                           ["$$INPUT_GET$$",                      LanguageDB["$input/get"]],
                           ["$$IF_INPUT_EQUAL_DELIMITER_0$$",     LanguageDB["$if =="]("Skipper$$SKIPPER_INDEX$$[0]")],
                           ["$$ENDIF$$",                          LanguageDB["$endif"]],
                           ["$$ENTRY$$",                          get_label("$entry", skipper_index)],
                           ["$$RELOAD$$",                         get_label("$reload", skipper_index)],
                           ["$$GOTO_AFTER_END_OF_SKIPPING$$",     goto_after_end_of_skipping_str], 
                           ["$$GOTO_RELOAD$$",                    get_label("$reload", skipper_index)],
                           # When things were skipped, no change to acceptance flags or modes has
                           # happend. One can jump immediately to the start without re-entry preparation.
                           ["$$GOTO_ENTRY$$",                     get_label("$entry", skipper_index)],
                           ["$$MARK_LEXEME_START$$",              LanguageDB["$mark-lexeme-start"]],
                           ["$$ON_SKIP_RANGE_OPEN$$",             on_skip_range_open_str],
                           #
                           ["$$LC_COUNT_COLUMN_N_POINTER_DEFINITION$$", reference_p_def],
                           ["$$LC_COUNT_IN_LOOP$$",                     line_column_counter_in_loop],
                           ["$$LC_COUNT_END_PROCEDURE$$",               end_procedure],
                           ["$$LC_COUNT_BEFORE_RELOAD$$",               before_reload],
                           ["$$LC_COUNT_AFTER_RELOAD$$",                after_reload],
                          ])

    return code_str, local_variable_db


