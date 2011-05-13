from   quex.core_engine.state_machine.core         import State 
import quex.core_engine.generator.languages.core   as languages
from   quex.core_engine.generator.languages.address            import Address, get_address, get_label
import quex.core_engine.generator.state_coder.transition_block as transition_block
import quex.core_engine.generator.state_coder.transition       as transition
import quex.core_engine.generator.state_coder.acceptance_info  as acceptance_info
import quex.core_engine.generator.state_coder.drop_out         as drop_out
import quex.core_engine.generator.state_coder.input_block      as input_block
from   quex.input.setup                                        import setup as Setup
from   copy import deepcopy


def do(state, StateIdx, SMD=False):
    """Produces code for all state transitions. Programming language is determined
       by 'Language'.
    """    
    assert isinstance(state, State)
    assert SMD.__class__.__name__   == "StateMachineDecorator"
    assert len(state.transitions().get_epsilon_target_state_index_list()) == 0, \
           "Epsilon transition contained target states: state machine was not made a DFA!\n" + \
           "Epsilon target states = " + repr(state.transitions().get_epsilon_target_state_index_list())
    InitStateF = StateIdx == SMD.sm().init_state_index

    LanguageDB = Setup.language_db

    # (*) Dead End States 
    #     i.e. states with no further transitions.
    dead_end_state_info = SMD.dead_end_state_db().get(StateIdx)
    if dead_end_state_info != None:
        state_stub = __dead_end_state_stub(dead_end_state_info, SMD)
        # Some states do not need 'stubs' to terminal since they are straight
        # forward transitions to the terminal.
        if len(state_stub) == 0: return []
        return [ get_label("$entry", StateIdx), ":\n",
                "    ", LanguageDB["$debug-state"](StateIdx, SMD.forward_lexing_f())
               ] + state_stub 
        

    # (*) Normal States
    TriggerMap = state.transitions().get_trigger_map()
    assert TriggerMap != []  # Only dead end states have empty trigger maps.
    #                        # => Here, the trigger map cannot be empty.

    txt = []
    txt.extend(input_block.do(StateIdx, InitStateF, SMD))
    txt.extend(acceptance_info.do(state, StateIdx, SMD))
    txt.extend(transition_block.do(TriggerMap, StateIdx, SMD))
    txt.extend(drop_out.do(state, StateIdx, SMD))
    txt.extend(get_epilog(StateIdx, InitStateF, SMD))
    
    return txt 

def __dead_end_state_stub(DeadEndStateInfo, SMD):
    """Dead end states are states which are void of any transitions. They 
       all drop out to some terminal (or drop out totally). Many transitions 
       to goto states can be replaced by direct transitions to the correspondent
       terminal. Some dead end states, though, need to be replaced by 'stubs'
       where some basic handling is necessary. The implementation of such 
       stubs is handled inside this function.
    """
    LanguageDB = Setup.language_db

    pre_context_dependency_f, \
    winner_origin_list,       \
    state                     = DeadEndStateInfo

    assert isinstance(state, State)
    assert state.is_acceptance()

    if SMD.forward_lexing_f():
        if not pre_context_dependency_f:
            assert len(winner_origin_list) == 1
            # Direct transition to terminal possible, no stub required.
            return [] 

        else:
            def _on_detection_code(Origin):
                return transition.get_transition_to_terminal(Origin)

            return acceptance_info.get_acceptance_detector(state.origins().get_list(), 
                                                           _on_detection_code)

    elif SMD.backward_lexing_f():
        # When checking a pre-condition no dedicated terminal exists. However, when
        # we check for pre-conditions, a pre-condition flag needs to be set.
        return acceptance_info.backward_lexing(state.origins().get_list()) + \
               [ "goto %s;" % get_label("$terminal-general-bw", U=True) ] 


    elif SMD.backward_input_position_detection_f():
        # When searching backwards for the end of the core pattern, and one reaches
        # a dead end state, then no position needs to be stored extra since it was
        # stored at the entry of the state.
        return [ LanguageDB["$input/decrement"], "\n"] + \
               acceptance_info.backward_lexing_find_core_pattern(state.origins().get_list()) + \
               [ "goto %s;" % get_label("$terminal-general-bw", U=True) ] 

    assert False, \
           "Unknown mode '%s' in terminal stub code generation." % Mode

def get_epilog(StateIdx, InitStateF, SMD):
    """The init state does not increment the input position, thus we do the
       increment in a separate fragment. This fragment acts then as the entry
       to the init state. Finally, it jumps to the transition block of the 
       init state as defined above.

       (The backward init state decrements the input pointer, so this is not necessary.)
    """
    LanguageDB = Setup.language_db

    if not (InitStateF and SMD.forward_lexing_f()): return [""]

    txt = ["\n"]
    txt.append(Address("$entry", StateIdx))
    txt.append("\n")
    txt.extend(["    ", LanguageDB["$input/increment"], "\n"])
    txt.append("    goto %s;\n" % get_label("$init_state_fw_transition_block"))
    return txt
