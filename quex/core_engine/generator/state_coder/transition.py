from quex.input.setup import setup as Setup
from quex.core_engine.generator.languages.address import get_address, get_label, Address

def do(TargetInfo, CurrentStateIdx, SMD):
    LanguageDB = Setup.language_db

    # (*) Normal Transitions: goto + label
    #
    if TargetInfo == None:
        return get_transition_to_drop_out(CurrentStateIdx)

    elif TargetInfo == -1:
        return get_transition_to_reload(CurrentStateIdx)

    else:
        return get_transition_to_state(TargetInfo)

def get_transition_to_state(TargetInfo):
    LanguageDB = Setup.language_db
    return "goto %s;" % get_label("$entry", TargetInfo, U=True)

def get_transition_to_drop_out(CurrentStateIdx):
    LanguageDB = Setup.language_db
    return "goto %s;" % get_label("$drop-out", CurrentStateIdx, U=True)

def get_transition_to_reload(StateIdx, SMD, ReturnStateIndexStr=None):
    LanguageDB = Setup.language_db

    if SMD != None and SMD.backward_lexing_f(): direction = "BACKWARD"
    else:                                       direction = "FORWARD"

    if SMD != None and (StateIdx == SMD.sm().init_state_index and SMD.forward_lexing_f()):
        return "goto __RELOAD_INIT_STATE;" 

    elif SMD == None or not SMD.backward_input_position_detection_f():
        if ReturnStateIndexStr != None: 
            state_reference = ReturnStateIndexStr
        else:                           
            state_reference = "QUEX_LABEL(%i)" % get_address("$entry", StateIdx, R=True)

        # Ensure that '__STATE_ROUTER' is marked as referenced
        get_label("$state-router", U=True)

        return "QUEX_GOTO_RELOAD(%s, %s, QUEX_LABEL(%i));" \
               % (get_label("$reload-%s" % direction, U=True),
                  state_reference,
                  get_address("$drop-out", StateIdx, U=True, R=True)) 

    else:
        return "" 

def get_transition_to_terminal(Origin):
    LanguageDB = Setup.language_db

    # No unconditional case of acceptance 
    if type(Origin) == type(None): 
        get_label("$terminal-router", U=True) # Mark __TERMINAL_ROUTER as used
        return [ LanguageDB["$goto-last_acceptance"] ]

    assert Origin.is_acceptance()
    # The seek for the end of the core pattern is part of the 'normal' terminal
    # if the terminal 'is' a post conditioned pattern acceptance.
    if Origin.post_context_id() == -1:
        return [ "goto %s;" % get_label("$terminal", Origin.state_machine_id, U=True) ]
    else:
        return [ "goto %s;" % get_label("$terminal-direct", Origin.state_machine_id, U=True) ]

def get_index(StateIdx, SMD):
    # During forward lexing (main lexer process) there are dedicated terminal states.
    if     SMD != None \
       and SMD.dead_end_state_db().has_key(StateIdx) \
       and SMD.forward_lexing_f():
        # The state is a dead-end-state. It transits immediately to a terminal.
        pre_context_dependency_f, \
        winner_origin_list,       \
        dead_end_target_state     = SMD.dead_end_state_db()[StateIdx]
        if not pre_context_dependency_f:
            assert len(winner_origin_list) == 1
            return get_address_of_terminal(winner_origin_list[0])
    return StateIdx

# The state is a dead-end-state. It transits immediately to a terminal
def get_real_address(TargetStateIdx, SMD):
    LanguageDB = Setup.language_db

    if     SMD != None \
       and SMD.dead_end_state_db().has_key(TargetStateIdx) \
       and SMD.forward_lexing_f():
        # Transitions to 'dead-end-state'
        return __get_address_of_dead_end_state(TargetStateIdx, SMD)
    else:
        # The very normal transition to another state
        return TargetStateIdx

def get_address_of_terminal(Origin):
    assert Origin.is_acceptance()
    LanguageDB = Setup.language_db
    # The seek for the end of the core pattern is part of the 'normal' terminal
    # if the terminal 'is' a post conditioned pattern acceptance.
    if Origin.post_context_id() == -1:
        return get_address("$terminal", Origin.state_machine_id)
    else:
        return get_address("$terminal-direct", Origin.state_machine_id)

def __get_address_of_dead_end_state(TargetStateIdx, SMD):
    """The TargetStateIdx is mentioned to be a dead-end-state! That means, that
       there is actually no 'transition block' in that state and it transits
       directly to a terminal.  The jump to those states can be shortcut. It is
       not necessary to go to that state and then drop out, and then goto the
       terminal. The transition to the terminal can be done directly.  
    """
    assert SMD != None
    LanguageDB = Setup.language_db

    pre_context_dependency_f, \
    winner_origin_list,       \
    dead_end_target_state     = SMD.dead_end_state_db()[TargetStateIdx]

    assert dead_end_target_state.is_acceptance(), \
           "NON-ACCEPTANCE dead end detected during code generation!\n"                 + \
           "A dead end that is not deleted must be an ACCEPTANCE dead end. See\n"       + \
           "state_machine.dead_end_analyzis.py and generator.state_machine_coder.py.\n" + \
           "If this is not the case, then something serious went wrong. A transition\n" + \
           "to a non-acceptance dead end is to be translated into a drop-out."

    if SMD.forward_lexing_f():
        if not pre_context_dependency_f:
            assert len(winner_origin_list) == 1
            # During forward lexing (main lexer process) there are dedicated terminal states.
            return get_address_of_terminal(winner_origin_list[0])

        else:
            # Pre-context dependency can only appear in forward lexing which is the analyzis
            # that determines the winning pattern. BackwardInputPositionDetection and 
            # BackwardLexing can never depend on pre-conditions.
            return TargetStateIdx

    elif SMD.backward_lexing_f():
        return TargetStateIdx

    elif SMD.backward_input_position_detection_f():
        # When searching backwards for the end of the core pattern, and one reaches
        # a dead end state, then no position needs to be stored extra since it was
        # stored at the entry of the state.
        return TargetStateIdx

    else:
        assert False, "Impossible engine generation mode: '%s'" % SMD.mode()

