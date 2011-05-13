from copy import copy
from quex.frs_py.string_handling import blue_print
db={}

def get_label(StateMachineName, StateIdx, SuccessfulOriginalStateMachineID=None):
    """
        (1) StateIdx != None
            jump label for state machine state entry    
        (2) StateIdx == None:  terminal state
            (1a) SuccessfulOriginalStateMachineID == None: not acceptance terminal state
            (1b) else: acceptance terminal state
    """
    def nice(SM_ID): return repr(SM_ID).replace("L", "")

    if StateIdx != None: 
        return "QUEX_LABEL_%s_ENTRY_%s" % (StateMachineName, nice(StateIdx))
    elif SuccessfulOriginalStateMachineID == None:
        return "QUEX_LABEL_%s_TERMINAL" % StateMachineName
    else:       
        return "QUEX_LABEL_%s_TERMINAL_%s" % (StateMachineName, nice(SuccessfulOriginalStateMachineID))

#________________________________________________________________________________
# C++
#
def __cpp_goto_state(UserDefinedStateMachineName, StateIdx, SuccessfulOriginalStateMachineID=None):
    return "goto %s;" % get_label(UserDefinedStateMachineName, StateIdx, SuccessfulOriginalStateMachineID)
         
def __cpp_acceptance_info(SuccessfulOriginalStateMachineID, LanguageDB):
    if SuccessfulOriginalStateMachineID != None:
        txt =  "last_acceptance = %s;\n" % SuccessfulOriginalStateMachineID
        txt += LanguageDB["$input/tell_position"]("last_acceptance_input_position") + "\n"
    else:
        txt = ""    
    return txt

__cpp_function_header = \
"""
"""

def __cpp_terminal_states(StateMachineName, sm, action_db, DefaultAction):
    
    # -- specific terminal states of patterns (entered from acceptance states)
    txt = ""
    for state_machine_id in action_db.keys():
        txt += "  %s:\n" % get_label("", None, state_machine_id)
        action_code = "    " + action_db[state_machine_id].replace("\n", "\n    ")   
        txt += "    QUEX_STREAM_SEEK(last_acceptance_input_position);"
        txt += action_code + "\n"    
        txt += "    // if action code returns from the function, then the following is meaningless\n"
        if sm.states[sm.init_state_index].transitions().is_empty() == False:
            txt += "    QUEX_STREAM_GET(input);"
        txt += "    goto QUEX_LABEL_%s_ENTRY_INITIAL_STATE;\n" %  StateMachineName

    specific_terminal_states_str = txt

    #  -- general terminal state (entered from non-acceptance state)    
    txt = ""    
    for state_machine_id in action_db.keys():
        txt += "     case %s: goto %s;\n" % \
                (repr(state_machine_id), get_label("", None, state_machine_id))
    jumps_to_acceptance_states_str = txt


    #     -- execute default pattern action 
    #     -- reset character stream to last success             
    #     -- goto initial state 
    txt = blue_print(__cpp_terminal_state_str, 
                     [["$$JUMPS_TO_ACCEPTANCE_STATE$$",    jumps_to_acceptance_states_str],   
                      ["$$SPECIFIC_TERMINAL_STATES$$",     specific_terminal_states_str],
                      ["$$DEFAULT_ACTION$$",               DefaultAction.replace("\n", "        \n")],
                      ["$$STATE_MACHINE_NAME$$",           StateMachineName],
                      ["$$INITIAL_STATE_INDEX_LABEL$$",    get_label(StateMachineName, sm.init_state_index)]])
    return txt
    
#________________________________________________________________________________
# Visual Basic 6
#    
db["VisualBasic6"] = {
    "$if":     "If",
    "$then":   "Then",
    "$endif":  "End If",
    "$>=":     ">=",
    "$==":     "==",
    "$input":  "input",
    "$return_true":  "$the_function = True: Exit Function",
    "$return_false": "$the_function = True: Exit Function",
    }


def replace_keywords(program_txt, LanguageDB, NoIndentF):
    """Replaces pseudo-code keywords with keywords of the given language."""

    txt = blue_print(program_txt, LanguageDB.items())

    if NoIndentF == False:
        # delete the last newline, to prevent additional indentation
        if txt[-1] == "\n": txt = txt[:-1]
        # indent by four spaces
        # (if this happens in recursively called functions nested indented blocks
        #  are correctly indented, see NumberSet::get_condition_code() for example)     
        txt = txt.replace("\n", "\n    ") + "\n"
    
    return txt          
