from   quex.core_engine.generator.state_machine_decorator import StateMachineDecorator
import quex.core_engine.state_machine.core                as     state_machine 
#
from   quex.core_engine.generator.languages.address import __nice, get_address, get_label
from   quex.input.setup                             import setup as Setup

LanguageDB = None

def do(State, StateIdx, SMD, ForceSaveLastAcceptanceF=False):
    assert isinstance(State, state_machine.State)
    assert isinstance(SMD,   StateMachineDecorator)
    global LanguageDB

    LanguageDB = Setup.language_db
    
    mode = SMD.mode()
    if   mode == "ForwardLexing":                  txt = forward_lexing(State, StateIdx, SMD, ForceSaveLastAcceptanceF)
    elif mode == "BackwardLexing":                 txt = backward_lexing(State.origins().get_list())
    elif mode == "BackwardInputPositionDetection": txt = backward_lexing_find_core_pattern(State.origins().get_list())
    else:
        assert False, "This part of the code should never be reached"
    assert type(txt) == list
    return txt

def forward_lexing(State, StateIdx, SMD, ForceSaveLastAcceptanceF=False):
    """Forward Lexing:

       (1) Pure 'Store-Input-Position' States

           States that mark the end of a core pattern that is followed by a post
           condition. If such a state reached, then the current position needs 
           to be stored in a dedicated register---ultimatively.

       (2) 'Real'-Acceptance States

           States that terminate an analyzis step and declare the winning pattern.

           -- No pre-conditions, or all pre-conditions have lower priority than
              the highest priority non-pre-condition 
              
              => decision of who wins can be made at code-generation time.

           -- High-priority pre-conditions involved 

              => code must select from all pre-conditions that have higher
                 priority than the first non-pre-conditioned pattern.
           
           => use 'get_acceptance_detector()' in order to get a sequence of 'if-else'
              blocks that determine acceptance. 
    """
    assert SMD.__class__.__name__ == "StateMachineDecorator"
    LanguageDB = Setup.language_db

    OriginList = State.origins().get_list()

    # (1) Set the post context registers (if appropriate)
    txt = __handle_post_conditioned_core_patterns(OriginList, SMD)

    # -- If there is no 'real' acceptance, then we're done
    #    (Post conditioned core pattern end states are not in itself 
    #     cannot be acceptance states. If the state is an acceptance 
    #     state than there must be 'real' acceptance origins.)
    if not State.is_acceptance(): 
        return txt 

    # -- If the current acceptance does not need to be stored, then do not do it
    if     not ForceSaveLastAcceptanceF \
       and not subsequent_states_require_save_last_acceptance(StateIdx, State, SMD.sm()): 
        return txt
   
    # (2) Create detector for normal and pre-conditioned acceptances
    def _on_detection_code(Origin):
        """Store the name of the winner pattern (last_acceptance) and the position
           where it has matched (use of $input/tell_position).
        """
        if type(Origin) == type(None):
            # Case if no un-conditional acceptance occured, then register nothing
            return ""

        assert Origin.is_acceptance()

        info = [ 
           "    last_acceptance                = QUEX_LABEL(%i);\n" \
           % get_address("$terminal-direct", Origin.state_machine_id, U=True, R=True) 
        ]

        # NOTE: When a post conditioned pattern ends it does not need to store the input 
        #       position. Rather, the acceptance position of the core pattern is retrieved
        #       in the terminal state.
        if Origin.post_context_id() == -1:
            info.append("    ")
            info.append(LanguageDB["$input/tell_position"]("last_acceptance_input_position") + "\n")

        return info

    txt.extend(get_acceptance_detector(OriginList, _on_detection_code))

    return txt

def __handle_post_conditioned_core_patterns(OriginList, SMD):
    """Creates code to store the input position for post conditioned
       core patterns. That means, that the input pointer must return
       to this place in case that the post condition is fulfilled.
    """
    global LanguageDB

    # (1) Set the post context registers (if appropriate)
    #     (also determine the list of acceptance origins)
    txtl = []
    for origin in OriginList: 
        if origin.is_end_of_post_contexted_core_pattern():
            # Assumption about origin based on assumption about single pattern state machine:
            #
            #    According to 'setup_post_context.py' (currently line 121) no acceptance
            #    state of a post context can store the input position. This has been made 
            #    impossible! Otherwise, the post context would have zero length.
            #
            #    Post-conditions via backward search, i.e. pseudo ambigous post conditions,
            #    are a different ball-game.
            #
            assert origin.is_acceptance() == False

            # Store current input position, to be restored when post condition really matches
            post_context_index = SMD.get_post_context_index(origin.state_machine_id)
            txtl += [
                    "    __quex_debug(\"post context %s: mark position\");\n" % __nice(origin.state_machine_id),
                    "    " + LanguageDB["$input/tell_position"]("post_context_start_position[%i]" % \
                             post_context_index),
                    "\n"
                    ]

    return txtl

def backward_lexing(OriginList):
    """Backward Lexing:
       -- Using an inverse state machine from 'real' current start position backwards
          until a drop out occurs.
       -- During backward lexing, there is no 'winner' so all origins that indicate
          acceptance need to be considered. They raise there flag 'pre-condition fulfilled'.
    """
    LanguageDB = Setup.language_db

    # There should be nothing, but unconditional acceptances or no-acceptance 
    # origins in the list of origins.
    inadmissible_origin_list = filter(lambda origin:
                                      origin.pre_context_begin_of_line_f() or
                                      origin.pre_context_id() != -1L or
                                      origin.post_context_id() != -1L,
                                      OriginList)
    assert inadmissible_origin_list == [], \
           "Inadmissible origins for inverse state machine."
    #___________________________________________________________________________________________

    txt = []
    for origin in OriginList:
        if not origin.store_input_position_f(): continue
        assert origin.is_acceptance()
        variable = "pre_context_%s_fulfilled_f" % __nice(origin.state_machine_id)
        txt.append("    " + LanguageDB["$assignment"](variable, 1))
        txt.append("    __quex_debug(\"pre context %s fulfilled\");\n" % __nice(origin.state_machine_id));
    txt.append("\n")

    return txt

def backward_lexing_find_core_pattern(OriginList):
    """Backward Lexing:
       -- (see above)
       -- for the search of the end of the core pattern, the acceptance position
          backwards must be stored. 
       -- There is only one pattern involved, so no determination of 'who won'
          is important.
    """
    LanguageDB = Setup.language_db

    # There should be nothing, but unconditional acceptances or no-acceptance 
    # origins in the list of origins.
    inadmissible_origin_list = filter(lambda origin:
                                      origin.pre_context_begin_of_line_f() or
                                      origin.pre_context_id() != -1L or
                                      origin.post_context_id() != -1L,
                                      OriginList)
    assert len(inadmissible_origin_list) == 0, \
           "Inadmissible origins for inverse state machine."
    #___________________________________________________________________________________________


    for origin in OriginList:
        if origin.store_input_position_f():
            assert origin.is_acceptance()
            return ["    ", LanguageDB["$input/tell_position"]("end_of_core_pattern_position"), "\n"]
    return ["\n"]

def trivial_terminal(OriginList):
    """If the acceptance depends on pre-context, then the acceptance
       detection is non-trivial. If it is trivial a simple 'goto terminal'
       can be applied.

       RETURNS:  None  -- if the acceptance determination is not trivial
                 >= 0  -- index of the acceptance terminal
                 -1    -- if it is a non-acceptance state
    """

    acceptance_terminal_id = -1
    for origin in OriginList:
        if not origin.is_acceptance():     continue
        if   origin.pre_context_id() != -1L:       return False
        elif origin.pre_context_begin_of_line_f(): return False
        if acceptance_terminal_id == -1:
            acceptance_terminal_id = origin.state_machine_id
    return acceptance_terminal_id

def get_acceptance_detector(OriginList, get_on_detection_code_fragment):
        
    LanguageDB = Setup.language_db

    txt       = []
    debug_txt = []
    first_if_statement_f         = True
    unconditional_case_treated_f = False
    OriginList.sort()
    for origin in OriginList:
        if not origin.is_acceptance(): continue

        info = get_on_detection_code_fragment(origin)

        if origin.pre_context_id() != -1L:
            txt.append(1)
            if first_if_statement_f: txt.append(LanguageDB["$if pre-context"](origin.pre_context_id()))
            else:                    txt.append(LanguageDB["$elseif pre-context"](origin.pre_context_id()))
            txt.append(2)
            txt.extend(info)
            txt.append("\n")
            txt.append(1)
            txt.append(LanguageDB["$endif"])
            debug_txt.append(1)
            debug_txt.append("__quex_debug2(\"pre condition %i: %%s\", "         % origin.pre_context_id() + \
                             "pre_context_%i_fulfilled_f ? \"yes\" : \"no\");\n" % origin.pre_context_id())
        
        elif origin.pre_context_begin_of_line_f():
            txt.append(1)
            if first_if_statement_f: txt.append(LanguageDB["$if begin-of-line"])
            else:                    txt.append(LanguageDB["$elseif begin-of-line"])
            txt.append(1)
            txt.extend(info)
            txt.append("\n")
            txt.append(1)
            txt.append(LanguageDB["$endif"])
            debug_txt.append(1)
            debug_txt.append("__quex_debug2(\"begin of line pre-context: ")
            debug_txt.append("%")
            debug_txt.append("s\", ")
            debug_txt.append("me->buffer._character_before_lexeme_start ? \"yes\" : \"no\");\n")
        
        else:
            if first_if_statement_f: 
                txt.extend(info)
            else:
                # if an 'if' statements preceeded, the acceptance needs to appear in an else block
                txt.append(1)
                txt.append(LanguageDB["$else"])
                txt.append("\n")
                txt.append(2)
                txt.extend(info)
                txt.append("\n")
                txt.append(1)
                txt.append(LanguageDB["$endif"])
            unconditional_case_treated_f = True
            break  # no need for further pre-condition consideration

        first_if_statement_f = False

    if unconditional_case_treated_f == False:
        debug_txt.append(1)
        default_action = get_on_detection_code_fragment(None)
        assert default_action != None
        txt.extend(default_action)

    return debug_txt + txt

def subsequent_states_require_save_last_acceptance(StateIdx, State, SM):
    """For the 'longest match' approach it is generally necessary to store the last
       pattern that has matched the current input stream. This means, that the
       current pattern index **and** the current input position need to be stored.
       Nothing of that is necessary, if one knows that a state does not have any
       'critical' follow-up states where the position is to be restored. For example,

                 (0)--- 'a' --->(( 1 ['a'] ))---- 'b' --->(( 2 ['ab'] ))

       When state 1 is reached, it indicates that pattern 'a' has matched. Since
       all subsequent states are acceptance states the last acceptance does
       not have to be stored. The only way that 'a' is detected is on drop
       out from state 1 (see drop-out handling).

       Note, that this is equally true, if the acceptance state transits 
       on itself.
    """
    assert isinstance(State, state_machine.State)
    assert SM.__class__.__name__ == "StateMachine"
    assert State.is_acceptance()

    reachable_state_list = State.transitions().get_target_state_index_list()

    for state_index in reachable_state_list:
        state = SM.states[state_index]

        if state.is_acceptance() == False: return True
        # Is there at least one origin that is unconditioned? If not,
        # the trailing last acceptance must be stored.
        for origin in state.origins().get_list():
            if   not origin.is_acceptance():                      continue
            elif origin.pre_context_begin_of_line_f():            continue
            elif origin.pre_context_id() != -1L:                  continue
            elif origin.pseudo_ambiguous_post_context_id() != -1: continue
            else:
                # We found an un-conditioned acceptance state.
                # => State is 'OK' (There will be an acceptance that 
                # overwrites the acceptance of the current one)
                break
                # (Post conditioned states store only the input position,
                #  but are not acceptance states)
        else:
            # No un-conditioned acceptance origin found 
            # => State must be treated as if it was non-acceptance
            return True

    return False



