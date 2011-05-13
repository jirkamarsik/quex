from   quex.core_engine.interval_handling     import NumberSet
from   quex.core_engine.generator.action_info import *
from   quex.input.setup                       import setup as Setup

def do(Mode, CodeFragment_or_CodeFragments, SafePatternStr, PatternStateMachine, 
       Default_ActionF=False, EOF_ActionF=False, SelfCountingActionF=False):
    """-- If there are multiple handlers for a single event they are combined
    
       -- Adding debug information printer (if desired)
    
       -- The task of this function is it to adorn the action code for each pattern with
          code for line and column number counting.
    """
    assert Mode.__class__.__name__  == "Mode"
    assert type(SafePatternStr)     == str
    assert PatternStateMachine      == None or PatternStateMachine.__class__.__name__ == "StateMachine" 
    assert type(Default_ActionF)    == bool
    assert type(EOF_ActionF)        == bool
    # We assume that any state machine presented here has been propperly created
    # and thus contains some side information about newline number, character number etc.
    assert PatternStateMachine      == None or PatternStateMachine.side_info != None, \
           repr(PatternStateMachine)

    if type(CodeFragment_or_CodeFragments) == list:
        assert Default_ActionF or EOF_ActionF, \
               "Action code formatting: Multiple Code Fragments can only be specified for default or\n" + \
               "end of stream action."
        CodeFragmentList = CodeFragment_or_CodeFragments
    else:
        CodeFragmentList = [ CodeFragment_or_CodeFragments ]

    on_every_match_code = ""
    lc_count_code       = ""
    debug_code          = ""
    user_code           = ""
    variable_db         = {}

    # (*) Code to be performed on every match -- before the related action
    for code_info in Mode.get_code_fragment_list("on_match"):
        on_every_match_code += code_info.get_code()

    # (*) Code to count line and column numbers
    if not SelfCountingActionF: 
        lc_count_code  = __get_line_and_column_counting(PatternStateMachine, EOF_ActionF)

    if (not Default_ActionF) and (not EOF_ActionF):
        lc_count_code += "    __QUEX_ASSERT_COUNTER_CONSISTENCY(&self.counter);\n"

    # (*) THE user defined action to be performed in case of a match
    user_code, require_terminating_zero_preparation_f = get_code(CodeFragmentList, variable_db)

    txt  = ""
    txt += on_every_match_code
    txt += "#   ifdef __QUEX_OPTION_COUNTER\n"
    txt += lc_count_code
    txt += "    __quex_debug_counter();\n"
    txt += "#   endif\n"
    txt += "    {\n"
    txt += user_code
    txt += "\n    }"

    return CodeFragment(txt, require_terminating_zero_preparation_f), variable_db

def get_code(CodeFragmentList, variable_db={}):
    code_str = ""
    require_terminating_zero_preparation_f = False
    for code_info in CodeFragmentList:
        result = code_info.get_code()
        if type(result) == tuple: 
            result, add_variable_db = result
            variable_db.update(add_variable_db)

        if type(result) == list: code_str += "".join(result)
        else:                    code_str += result        

        if code_info.require_terminating_zero_f():
            require_terminating_zero_preparation_f = True

    return code_str, require_terminating_zero_preparation_f

def __get_line_and_column_counting(PatternStateMachine, EOF_ActionF):

    # shift the values for line and column numbering
    txt = "    __QUEX_IF_COUNT_LINES(self.counter._line_number_at_begin     = self.counter._line_number_at_end);\n" + \
          "    __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_begin = self.counter._column_number_at_end);\n"

    if EOF_ActionF:
        return txt

    if PatternStateMachine == None:
        return txt + "    QUEX_NAME(Counter_count)(&self.counter, self.buffer._lexeme_start_p, self.buffer._input_p);\n"

    newline_n   = PatternStateMachine.side_info.get_newline_n()
    character_n = PatternStateMachine.side_info.get_character_n()

    if   newline_n == -1:
        # Run the general algorithm, since not even the number of newlines in the 
        # pattern can be determined directly from the pattern
        return txt + "    QUEX_NAME(Counter_count)(&self.counter, self.buffer._lexeme_start_p, self.buffer._input_p);\n"

    elif newline_n != 0:
        txt += "    __QUEX_IF_COUNT_LINES(self.counter._line_number_at_end += %i);\n" % newline_n 
        if PatternStateMachine.get_ending_character_set().contains_only(ord('\n')):
            # A pattern that ends with newline, lets the next column start at zero.
            txt += "    __QUEX_IF_COUNT_COLUMNS_SET((size_t)1);\n"
        else:
            # TODO: Try to determine number of characters backwards to newline directly
            #       from the pattern state machine. (Those seldom cases won't bring much
            #       speed-up)
            txt += "    QUEX_NAME(Counter_count_chars_to_newline_backwards)(&self.counter, self.buffer._lexeme_start_p, self.buffer._input_p);\n"
        return txt

    else:
        if character_n == -1: incr_str = "    ((size_t)(self.buffer._input_p - self.buffer._lexeme_start_p))"
        else:                 incr_str = "%i" % int(character_n)

        return txt + "    __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += %s);\n" % incr_str

