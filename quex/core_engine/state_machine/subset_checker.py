from quex.core_engine.state_machine.core import StateMachine

class Checker:
    def __init__(self, SuperSM, AllegedSubSM):
        """Checks wether all patterns matched by the SuperSM are also matched by the 
           AllegedSubSM. Basically it tries to answer the question:

              ? Is the set of patterns matched by 'AllegedSubSM' a subset of the ?
              ? set of patterns matched by 'SuperSM'                              ?

           RETURNS: 'True'  if so,
                    'False' if not.
        """
        assert isinstance(SuperSM, StateMachine)
        assert isinstance(AllegedSubSM, StateMachine)

        self.sub   = AllegedSubSM
        self.super = SuperSM
        self.visited_state_index_db = {}

    def do(self):
        return self.__dive(self.sub.init_state_index, [self.super.init_state_index])

    def __dive(self, SubSM_StateIndex, SuperSM_StateIndexList):
        """SubSM_StateIndex:       refers to a state in the alleged subset state machine.

           SuperSM_StateIndexList: list of states in the 'super set' state machine that
                                   was reached by the same trigger set as SubSM_StateIndex.      
                                   They are the set of states that can 'mimik' the current
                                   state indexed by 'SubSM_StateIndex'.
        """
        # (*) Determine the states behind the indices
        sub_state        = self.sub.states[SubSM_StateIndex]
        super_state_list = map(lambda index: self.super.states[index], SuperSM_StateIndexList)
        #     Bookkeeping
        self.visited_state_index_db[SubSM_StateIndex] = True
        #     Union of all triggers were the 'mimiking' super states trigger.
        #     (For speed considerations, keep it in prepared, so it does not have to 
        #      be computed each time it is required.)
        super_trigger_set_union_db = {} 
        for index in SuperSM_StateIndexList:
            super_trigger_set_union_db[index] = self.super.states[index].transitions().get_trigger_set_union()

        # (*) Here comes the condition:
        #
        #     For every trigger (event) in the 'sub sm state' that triggers to a follow-up state
        #     there must be pendant triggering from the mimiking 'super sm states'.
        #
        #     If a trigger set triggers to an 'acceptance' state, then all mimiking 'super sm states' 
        #     must trigger to an 'acceptance' state. Thus, saying that the 'super sm' also recognizes
        #     the pattern that was reached until here can be matched by the 'super set sm'. If not
        #     all mimiking state machines would trigger on the trigger set to an acceptance state,
        #     this means that there is a path to an acceptance state in 'subset sm' that the 'super
        #     sm' has no correspondance. Thus, then the claim to be a super set state machine can
        #     be denied.
        #
        for target_index, trigger_set in sub_state.transitions().get_map().items():
            target_state = self.sub.states[target_index]

            # (*) Require that all mimiking states in the 'super sm' trigger to a valid
            #     target state on all triggers in the trigger set. 
            #     
            #     This is true, if the union of all trigger sets of a mimiking 'super state'
            #     covers the trigger set. It's not true, if not. Thus, use set subtraction:
            for index in SuperSM_StateIndexList:
                if trigger_set.difference(super_trigger_set_union_db[index]).is_empty() == False:
                    return False

            # (*) Collect the states in the 'super set sm' that can be reached via the 'trigger_set'
            super_target_state_index_list = []
            for super_state in super_state_list:
                for index in super_state.transitions().get_resulting_target_state_index_list(trigger_set):
                    if index in super_target_state_index_list: continue
                    super_target_state_index_list.append(index)

            # (*) The acceptance condition: 
            if target_state.is_acceptance():
                # (*) Require that all target states in 'super sm' reached by 'trigger_set' are 
                #     acceptance states, otherwise the alleged 'sub sm' has found a pattern which
                #     is matched by it and which is not matched by 'super sm'. Thus, the claim 
                #     that the alleged 'sub sm' is a sub set state machine can be repudiated.
                for index in super_target_state_index_list:
                    if self.super.states[index].is_acceptance() == False: return False

            # (*) No need to go along loops, do not follow paths to states already visited.
            if not self.visited_state_index_db.has_key(target_index):
                if self.__dive(target_index, super_target_state_index_list) == False: return False

        # If the condition held for all sub-pathes of all trigger_sets then we can reports
        # that the currently investigated sub-path supports the claim that 'sub sm' is a
        # sub set state machine of 'super sm'.
        return True

def do(SuperSM, AllegedSubSM):
    # Check wether SuperSM matches a superset of patterns of what AllegedSubSM matches.
    sub_set_f = Checker(SuperSM, AllegedSubSM).do()

    if not sub_set_f: return False
    # NOTE: Post-conditions do not change anything, since they match only when the whole
    #       lexeme has matched (from begin to end of post condition). Post-conditions only
    #       tell something about the place where the analyzer returns after the match.
    #
    super_core = SuperSM.core()
    sub_core   = AllegedSubSM.core()

    super_pre_conditioned_f = (super_core.pre_context_sm_id() != -1 or super_core.pre_context_begin_of_line_f()) 
    sub_pre_conditioned_f   = (sub_core.pre_context_sm_id() != -1   or sub_core.pre_context_begin_of_line_f()) 
    # Pre-Condition: 
    #
    #       (i) If (only) the alleged subset state machine is pre-conditioned this does not 
    #           change anything in our considerations. It only restricts the 'set of applicable
    #           situations' further. If the set of patterns matched by AllegedSubSM is
    #           a subset of what SuperSM matches, then any subset of that is also a subset
    #           of what SuperSM matches.
    if not super_pre_conditioned_f: return True

    #
    #       (ii) If the SuperSM is pre-conditioned then the enclosing set is restricted, and
    #            it has to be made sure that it still encloses all what AllegedSubSM matches.
    #
    #            -- If the AllegedSubSM is not pre-conditioned at all, then it's free!
    #               Any pattern that does not have the precondition of SuperSM and matches
    #               AllegedSubSM can only be matched by AllegedSubSM.
    if not sub_pre_conditioned_f: return False

    # Here: Both are pre-conditioned.
    if super_core.pre_context_begin_of_line_f() and sub_core.pre_context_begin_of_line_f():
        assert super_core.pre_context_sm_id() != -1
        assert sub_core.pre_context_sm_id() != -1
        # It holds the judgement about the main patterns:
        return True

    #            -- If the AllegedSubSM is pre-conditioned, then its pre-condition must be
    #               a subset of SuperSM pre-condition. If not, its free for the same reason
    #               as mentioned above.
    return Checker(SuperSM.core().pre_context_sm(), AllegedSubSM.core().pre_context_sm()).do()


def do_list(SuperSM_List, AllegedSubSM):
    for super_sm in SuperSM_List:
        if do(super_sm, AllegedSubSM) == True: return True
    return False
