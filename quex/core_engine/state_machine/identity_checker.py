class Checker:
    def __init__(self, SM0, SM1):
        """Checks wether the set of patterns matched by SM0 is identical to the
           set of patterns matched by SM1.

           RETURNS: 'True'  if so,
                    'False' if not.
        """
        self.sm1 = SM1
        self.sm0 = SM0
        self.visited_state_index_db = {}

    def do(self):
        return self.__dive(self.sm1.init_state_index, [self.sm0.init_state_index])

    def __dive(self, SM1_StateIndex, SM0_StateIndexList):
        """SM1_StateIndex:     state index in SM1

           SM0_StateIndexList: list of states in the 'sm0 set' state machine that
                               was reached by the same trigger set as SM1_StateIndex.      
                               They are the set of states that can 'mimik' the current
                               state indexed by 'SM1_StateIndex'.
        """
        # (*) Determine the states behind the indices
        sm1_state      = self.sm1.states[SM1_StateIndex]
        sm0_state_list = map(lambda index: self.sm0.states[index], SM0_StateIndexList)
        #     Bookkeeping
        self.visited_state_index_db[SM1_StateIndex] = True
        #     Union of all triggers were the 'mimiking' sm0 states trigger.
        #     (For speed considerations, keep it in prepared, so it does not have to 
        #      be computed each time it is required.)
        sm0_trigger_set_union_db = {} 
        for index in SM0_StateIndexList:
            sm0_trigger_set_union_db[index] = self.sm0.states[index].transitions().get_trigger_set_union()

        sm1_trigger_set_union = sm1_state.transitions().get_trigger_set_union()

        # (*) Here comes the condition:
        #
        #     For every trigger (event) in the 'sm1 state' that triggers to a follow-up state
        #     there must be pendant triggering from the mimiking 'sm0 states'.
        #
        #     That is: 
        #     -- No 'mimiking sm0 state' is allowed to trigger on something beyond
        #        the trigger_set present on sm1, and vice versa.
        for index in SM0_StateIndexList:
            if not sm0_trigger_set_union_db[index].is_equal(sm1_trigger_set_union): 
                return False

        #     -- All 'mimiking sm0 states' must trigger on the given trigger_set to 
        #        a subsequent state of the same 'type' as the 'sm1 state'.
        for target_index, trigger_set in sm1_state.transitions().get_map().items():
            target_state = self.sm1.states[target_index]

            # (*) Collect the states in the 'sm0' that can be reached via the 'trigger_set'
            sm0_target_state_index_list = []
            for sm0_state in sm0_state_list:
                for index in sm0_state.transitions().get_resulting_target_state_index_list(trigger_set):
                    if index in sm0_target_state_index_list: continue
                    sm0_target_state_index_list.append(index)

            # (*) If there is one single state in the collection of follow-up states in sm0
            #     that has not the same type as the target state, then 'sm0' and 'sm1' are 
            #     not identical.
            if not self.__correspondance(target_state, sm0_target_state_index_list): 
                return False

            # (*) No need to go along loops, do not follow paths to states already visited.
            if not self.visited_state_index_db.has_key(target_index):
                if self.__dive(target_index, sm0_target_state_index_list) == False: return False

        # If the condition held for all sub-pathes of all trigger_sets then we can reports
        # that the currently investigated sub-path supports the claim that 'sm1 sm' is a
        # sub set state machine of 'sm0 sm'.
        return True

    def __correspondance(self, S1, S0List):
        """Checks whether all states in SList are of the same type as S0. 
           (With respect to the criteria of out algorithm.)
        """
        sm1c = S1.core()                         # core of the 'sm1' state
        for index in S0List:
            sm0c = self.sm0.states[index].core() # core of the 'sm0' state

            if    sm0c.is_acceptance()               !=  sm1c.is_acceptance():               return False
            elif (sm0c.post_context_id() == -1)      != (sm1c.post_context_id() == -1):      return False
            elif (sm0c.pre_context_id() == -1)       != (sm1c.pre_context_id() == -1):       return False
            elif  sm0c.store_input_position_f()      !=  sm1c.store_input_position_f():      return False
            elif  sm0c.pre_context_begin_of_line_f() !=  sm1c.pre_context_begin_of_line_f(): return False
            elif    (sm0c.pseudo_ambiguous_post_context_id() == -1) \
                 != (sm1c.pseudo_ambiguous_post_context_id() == -1):                         return False
        return True

def do(SM0, SM1):
    # Check whether SM0 and SM1 are identical, i.e they match exactly the same patterns 
    # and provide exactly the same behavior of the lexical analyzer.
    identity_f = Checker(SM0, SM1).do()

    if not identity_f: return False
    # NOTE: Post-conditions are handled in the identity check already.
    #
    # Pre-Condition: 
    #
    #       If only one state machine is pre-conditioned, then they are not identical
    if (SM0.core().pre_context_sm_id() == -1) != (SM1.core().pre_context_sm_id() == -1): 
        return False
    else:
        if SM0.core().pre_context_sm_id() != -1:
            # Both are pre-conditioned by state machine
            assert SM1.core().pre_context_sm_id() != -1
            # Pre-condition by 'begin of line' excludes other pre-conditions.
            assert not SM0.core().pre_context_begin_of_line_f()
            assert not SM1.core().pre_context_begin_of_line_f()
            return Checker(SM0.core().pre_context_sm(), SM1.core().pre_context_sm()).do()

    # Here: None SM0 and SM1 is dependent on pre-context state machine
    if  SM0.core().pre_context_begin_of_line_f() != SM1.core().pre_context_begin_of_line_f(): 
        return False
    else:
        if SM0.core().pre_context_begin_of_line_f():
            # Both are pre-conditioned by 'begin of line' => judgement remains as above
            assert SM1.core().pre_context_begin_of_line_f()
            # Pre-condition by 'begin of line' excludes other pre-conditions.
            assert SM0.core().pre_context_sm_id() == -1
            assert SM1.core().pre_context_sm_id() == -1
            # Here: identity_f == True
            return True

    # Here: None SM0 and SM1 is dependent on pre-context by 'begin of line

    # If there is no pre-condition at all, then the old judgement holds
    return True

