
def do(state_machine):
    """(1) Delete transitions to non-acceptance states that have no further 
           transition. Delete also the correspondent empty states.

           This can be done, since a transition to a non-acceptance state
           where there is no further path is identical to a drop-out. The
           drop out happens if no transition happens on current character.
       
       (2) Collect all states that have no further transitions, i.e. dead end states.
           Some of them need to be investigated, since it depends on pre-conditions
           what terminal state is to be considered. The mapping works as follows:

            CASE 1: db.has_key(state_index) == False    
            
                ==> (i)  state is not a dead end at all.
                    (ii) state is a DEAD END and a NON-ACCEPTANCE state.
                         --> simply delete all transitions to this state.
                         --> the state that triggers to it drops out immediately.

            CASE 2: db[state_index][0] == True

                ==> State is a DEAD END and an ACCEPTANCE state
                    It contains a dependency on PRE-CONTEXTS, thus,
                    it needs to be implemented as a 'pre-condition base router'.
                    Depending on the pre-context it routes to a terminal.

            CASE 3: db[state_index][0] == False

                ==> State is a DEAD END and an ACCEPTANCE state
                    There are NO PRE-CONTEXTS, so no check is necessary.
                    Transition to state can be replaced by a transition to the 
                    terminal corresponding the ACCEPTANCE.
 
    """
    db = {}
    # non_acceptance_dead_end_state_index_list = []
    for state_index, state in state_machine.states.items():

        # A dead end state does not have any transition.
        if not state.transitions().is_empty(): continue

        if state.is_acceptance(): 
            # (1) Acceptance States 
            #     --> short cuts to terminals / terminal stubs
            db[state_index] = state
            if state.origins().contains_any_pre_context_dependency():
                # (a) state require run time investigation since pre-conditions have to be checked
                #     Terminals are reached via a 'router'. nevertheless, they are reached 
                #     without a seek.
                winner_origin_list = []
                for origin in state.origins().get_list():
                    if not origin.is_acceptance(): continue
                    winner_origin_list.append(origin)
                # pre-context dependency = True
                db[state_index] = (True, winner_origin_list, state)

            else:
                # Find the first acceptance origin (origins are sorted already)
                winner_origin = state.origins().find_first_acceptance_origin()
                # There **must** be an acceptance state, see above
                assert type(winner_origin) != type(None)

                # (b) state transits automatically to terminal given below
                #     pre-context dependency = False
                #     winner_origin_list     = 'defined at compile time'
                db[state_index] = (False, [winner_origin], state)
        else:
            # (2) Non-Acceptance states (total drop outs) 
            #     --> deletion of state and all transitions to it
            for state in state_machine.states.values():
                state.transitions().delete_transitions_to_target(state_index) 

            del state_machine.states[state_index]
            # non_acceptance_dead_end_state_index_list.append(state_index)

    return db

