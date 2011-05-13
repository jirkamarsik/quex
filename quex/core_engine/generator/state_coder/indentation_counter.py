from   quex.frs_py.string_handling                   import       blue_print
from   quex.input.setup                              import       setup as Setup
import quex.core_engine.state_machine.index          as           sm_index
import quex.core_engine.generator.state_coder.transition_block as transition_block
from   quex.core_engine.generator.languages.variable_db        import Variable
from   quex.core_engine.generator.languages.address  import       get_label, Address
from   quex.core_engine.interval_handling            import       Interval
import quex.output.cpp.action_code_formatter         as           action_code_formatter
import quex.lexer_mode                               as           lexer_mode

from   math import log
import sys

class IndentationCounter(transition_block.TriggerAction):
    def __init__(self, Type, Number, StateIndex):
        self.type        = Type
        self.number      = Number
        self.state_index = StateIndex

    def __eq__(self, Other):
        if Other.__class__ != IndentationCounter: return False
        return self.type == Other.type and self.number == Other.number

    def __ne__(self, Other):
        return not self.__eq__(Other)

    def get_code(self):
        """Indentation counters may count as a consequence of a 'triggering'."""
        LanguageDB = Setup.language_db

        # Spaces simply increment
        if self.type == "space": 
            if self.number != -1: add_str = "%i" % self.number
            else:                 add_str = "me->" + self.variable_name
            return "me->counter._indentation += %s;" % add_str + \
                   "goto %s;" % get_label("$entry", self.state_index, U=True)
        
        # Grids lie on a grid:
        elif self.type == "grid":
            if self.number != -1: 
                log2 = log(self.number)/log(2)
                if log2.is_integer():
                    # For k = a potentials of 2, the expression 'x - x % k' can be written as: x & ~log2(mask) !
                    # Thus: x = x - x % k + k = x & mask + k
                    mask = (1 << int(log2)) - 1
                    return "me->counter._indentation &= ~ ((QUEX_TYPE_INDENTATION)0x%X);\n" % mask + \
                           "me->counter._indentation += %i;\n" % self.number + \
                           "goto %s;" % get_label("$entry", self.state_index, U=True)
                else:
                    add_str = "%i" % self.number
            else:   
                add_str = "me->" + self.variable_name

            return "me->counter._indentation = (me->counter._indentation - (me->counter._indentation %% %s)) + %s;" \
                   % (add_str, add_str) + \
                   LanguageDB["$goto"]("$entry", self.state_index)

        elif self.type == "bad":
            assert self.state_index != -1
            return "goto INDENTATION_COUNTER_%i_BAD_CHARACTER;\n" % self.state_index

        else:
            assert False, "Unreachable code has been reached."
    
    def is_drop_out(self):
        return False

class IndentationBadCharacter:
    def __init__(self, StateIndex):
        self.state_index = StateIndex

    def __eq__(self, Other):
        if Other.__class__ != IndentationBadCharacter: return False
        return self.state_index == Other.state_index 

    def __ne__(self, Other):
        return not self.__eq__(Other)

prolog_txt = """
{ 
    $$DELIMITER_COMMENT$$
$$INIT_REFERENCE_POINTER$$

    QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
    __quex_assert(QUEX_NAME(Buffer_content_size)(&me->buffer) >= 1);

INDENTATION_COUNTER_$$COUNTER_INDEX$$_ENTRY:
    $$INPUT_GET$$ 
"""

epilog_txt = """
    /* No need for re-entry preparation. Acceptance flags and modes are untouched. */
$$END_PROCEDURE$$                           
    goto $$GOTO_START$$;

$$LOOP_REENTRANCE$$:
    $$INPUT_P_INCREMENT$$ /* Now, BLC cannot occur. See above. */
    goto INDENTATION_COUNTER_$$COUNTER_INDEX$$_ENTRY;

$$RELOAD$$:
    /* -- In the case of 'indentation counting' we do not worry about the lexeme at all --
     *    HERE, WE DO! We can only set the lexeme start to the current reference_p, i.e.
     *    the point of the last newline!
     *    The appplication might actually do something with indented region.
     *
     * -- The input_p will at this point in time always point to the buffer border.     */
    me->buffer._lexeme_start_p = reference_p;
    if( $$INPUT_EQUAL_BUFFER_LIMIT_CODE$$ ) {
        QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
        if( QUEX_NAME(Buffer_is_end_of_file)(&me->buffer) ) {
            goto $$GOTO_TERMINAL_EOF$$;
        } else {
            QUEX_NAME(buffer_reload_forward_LA_PC)(&me->buffer, &last_acceptance_input_position,
                                                   post_context_start_position, PostContextStartPositionN);

            QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
            $$INPUT_P_INCREMENT$$ /* Now, BLC cannot occur. See above. */
            goto INDENTATION_COUNTER_$$COUNTER_INDEX$$_ENTRY;
        } 
    }

$$BAD_CHARACTER_HANDLING$$
}
"""

def do(Data):
    """The generated code is very similar to the 'skipper' code. It is to be executed
       as soon as a 'real' newline arrived. Then it skips whitespace until the next 
       non-whitepace (also newline may trigger a 'stop'). 

       Dependent on the setup the indentation is determined.
    """
    IndentationSetup = Data["indentation_setup"]
    assert IndentationSetup.__class__.__name__ == "IndentationSetup"


    LanguageDB = Setup.language_db
    Mode = None
    if IndentationSetup.containing_mode_name() != "":
        Mode = lexer_mode.mode_db[IndentationSetup.containing_mode_name()]

    counter_index = sm_index.get()
    
    # Mini trigger map:  [ trigger set ] --> loop start
    # That means: As long as characters of the trigger set appear, we go to the loop start.

    trigger_map = []
    # If the indentation consists only of spaces, than it is 'uniform' ...
    if IndentationSetup.has_only_single_spaces():
        # Count indentation/column at end of run;
        # simply: current position - reference_p

        character_set = IndentationSetup.space_db.values()[0]
        for interval in character_set.get().get_intervals(PromiseToTreatWellF=True):
            trigger_map.append([interval, counter_index])

        # Reference Pointer: Define Variable, Initialize, determine how to subtact.
        end_procedure = \
        "    me->counter._indentation = (size_t)(QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer) - reference_p);\n" 
    else:
        # Count the indentation/column during the 'run'

        # Add the space counters
        for count, character_set in IndentationSetup.space_db.items():
            for interval in character_set.get().get_intervals(PromiseToTreatWellF=True):
                trigger_map.append([interval, IndentationCounter("space", count, counter_index)])

        # Add the grid counters
        for count, character_set in IndentationSetup.grid_db.items():
            for interval in character_set.get().get_intervals(PromiseToTreatWellF=True):
                trigger_map.append([interval, IndentationCounter("grid", count, counter_index)])

        # Reference Pointer: Not required.
        #                    No subtraction 'current_position - reference_p'.
        #                    (however, we pass 'reference_p' to indentation handler)
        end_procedure = "" 

    # Bad character detection
    if IndentationSetup.bad_character_set.get().is_empty() == False:
        for interval in IndentationSetup.bad_character_set.get().get_intervals(PromiseToTreatWellF=True):
            trigger_map.append([interval, IndentationCounter("bad", None, counter_index)])

    # Since we do not use a 'TransitionMap', there are some things we need 
    # to do by hand.
    arrange_trigger_map(trigger_map)

    local_variable_db = { "reference_p" : 
                          Variable("reference_p", 
                                   "QUEX_TYPE_CHARACTER_POSITION", 
                                   None, 
                                   "(QUEX_TYPE_CHARACTER_POSITION)0x0")
    }
    init_reference_p  = "    reference_p = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer);\n" + \
                        "    me->counter._indentation = (QUEX_TYPE_INDENTATION)0;\n"

    iteration_code = transition_block.do(trigger_map, 
                                         counter_index, 
                                         DSM=None, 
                                         GotoReload_Str="goto %s;" % get_label("$reload", counter_index))

    comment_str    = LanguageDB["$comment"]("Skip whitespace at line begin; count indentation.")

    # NOTE: Line and column number counting is off
    #       -- No newline can occur
    #       -- column number = indentation at the end of the process

    end_procedure += "    __QUEX_IF_COUNT_COLUMNS_ADD(me->counter._indentation);\n"
    if Mode == None or Mode.default_indentation_handler_sufficient():
        end_procedure += "    QUEX_NAME(on_indentation)(me, me->counter._indentation, reference_p);\n"
    else:
        # Definition of '%s_on_indentation' in mode_classes.py.
        end_procedure += "    QUEX_NAME(%s_on_indentation)(me, me->counter._indentation, reference_p);\n" \
                         % Mode.name

    # The finishing touch
    prolog = blue_print(prolog_txt,
                         [
                           ["$$DELIMITER_COMMENT$$",              comment_str],
                           ["$$INIT_REFERENCE_POINTER$$",         init_reference_p],
                           ["$$COUNTER_INDEX$$",                  repr(counter_index)],
                           ["$$INPUT_GET$$",                      LanguageDB["$input/get"]],
                         ])

    # The finishing touch
    epilog = blue_print(epilog_txt,
                      [
                       ["$$INPUT_P_INCREMENT$$",              LanguageDB["$input/increment"]],
                       ["$$INPUT_P_DECREMENT$$",              LanguageDB["$input/decrement"]],
                       ["$$IF_INPUT_EQUAL_DELIMITER_0$$",     LanguageDB["$if =="]("SkipDelimiter$$COUNTER_INDEX$$[0]")],
                       ["$$ENDIF$$",                          LanguageDB["$endif"]],
                       ["$$LOOP_REENTRANCE$$",                get_label("$entry",  counter_index)],
                       ["$$INPUT_EQUAL_BUFFER_LIMIT_CODE$$",  LanguageDB["$BLC"]],
                       ["$$RELOAD$$",                         get_label("$reload", counter_index)],
                       ["$$COUNTER_INDEX$$",                  repr(counter_index)],
                       ["$$GOTO_TERMINAL_EOF$$",              get_label("$terminal-EOF", U=True)],
                       # When things were skipped, no change to acceptance flags or modes has
                       # happend. One can jump immediately to the start without re-entry preparation.
                       ["$$GOTO_START$$",                     get_label("$start", U=True)], 
                       ["$$END_PROCEDURE$$",                  end_procedure],
                       ["$$BAD_CHARACTER_HANDLING$$",         get_bad_character_handler(Mode, IndentationSetup, counter_index)],
                      ])

    txt = [prolog]
    txt.extend(iteration_code)
    # txt.append(Address("$drop-out", counter_index))
    txt.append("\n")
    txt.append(epilog)

    return txt, local_variable_db

def arrange_trigger_map(trigger_map):
     """Arrange the trigger map: Sort, and insert 'drop-out-regions'
     """
     #  -- sort by interval
     trigger_map.sort(lambda x, y: cmp(x[0].begin, y[0].begin))
     
     #  -- insert lower and upper 'drop-out-transitions'
     if trigger_map[0][0].begin != -sys.maxint: 
         trigger_map.insert(0, [Interval(-sys.maxint, trigger_map[0][0].begin), None])
     if trigger_map[-1][0].end != sys.maxint: 
         trigger_map.append([Interval(trigger_map[-1][0].end, sys.maxint), None])

     #  -- fill gaps
     previous_end = -sys.maxint
     i    = 0
     size = len(trigger_map)
     while i < size:
         interval = trigger_map[i][0]
         if interval.begin != previous_end: 
             trigger_map.insert(i, [Interval(previous_end, interval.begin), None])
             i    += 1
             size += 1
         i += 1
         previous_end = interval.end

def get_bad_character_handler(Mode, IndentationSetup, CounterIdx):
    if Mode == None: return ""
    if IndentationSetup.bad_character_set.get().is_empty(): return ""

    txt  = "INDENTATION_COUNTER_%i_BAD_CHARACTER:\n" % CounterIdx
    if not Mode.has_code_fragment_list("on_indentation_bad"):
        txt += 'QUEX_ERROR_EXIT("Lexical analyzer mode \'%s\': bad indentation character detected!\\n"' \
                                % Mode.name + \
               '                "No \'on_indentation_bad\' handler has been specified.\\n");'
    else:
        code, eol_f = action_code_formatter.get_code(Mode.get_code_fragment_list("on_indentation_bad"))
        txt += "#define BadCharacter ((QUEX_TYPE_CHARACTER)*(me->buffer._input_p))\n"
        txt += code
        txt += "#undef  BadCharacter\n"

    return txt

