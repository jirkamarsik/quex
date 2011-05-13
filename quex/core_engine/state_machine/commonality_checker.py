from quex.core_engine.state_machine.core import StateMachine

NONE   = 0
BOTH   = 1
A_IN_B = 2
B_IN_A = 3

name = {
        NONE:   "NONE",
        BOTH:   "BOTH",
        A_IN_B: "A_IN_B",
        B_IN_A: "B_IN_A",
}

class Checker:
    def __init__(self, A, B):
        """Checks whether one state machine may match a lexeme that 
           is the START of a lexeme that is matched by the other 
           state machine. For example:

              A:  [a-z]{5}
              B:  otto

           B matches 'otto', A does not. However, A would match 'ottoy' 
           would which contains the pattern that B can match.

           A is not a superset, since it does not match everything that 
           B matches. It happens only that A and B have a commonality.
        """
        assert isinstance(A, StateMachine)
        assert isinstance(B, StateMachine)

        self.a_sm = A
        self.a_visited_state_indices = set([])
        self.b_sm = B
        self.b_visited_state_indices = set([])

    def do(self):
        """RETURNS:  
                     0, if no commonalities exist.
                     1, if both ACCEPT a common lexeme.
                     2, if A has a pattern that lies inside the state machine of B.
                     3, if B has a pattern that lies inside the state machine of A.
        """
        return self.__dive(self.a_sm.init_state_index, self.b_sm.init_state_index)

    def __dive(self, ATargetIdx, BTargetIdx):
        a_state = self.a_sm.states[ATargetIdx]
        b_state = self.b_sm.states[BTargetIdx]
        if a_state.is_acceptance(): 
            if b_state.is_acceptance(): return BOTH    # both share a commonality
            else:                       return A_IN_B  # A has something in B
        elif b_state.is_acceptance():   return B_IN_A  # B has something in A

        # Follow the path of common trigger sets
        for a_target, a_trigger_set in a_state.transitions().get_map().items():
            for b_target, b_trigger_set in b_state.transitions().get_map().items():
                if   a_trigger_set.has_intersection(b_trigger_set) == False: continue

                if     a_target in self.a_visited_state_indices \
                   and b_target in self.b_visited_state_indices: continue

                self.a_visited_state_indices.add(ATargetIdx)
                self.b_visited_state_indices.add(BTargetIdx)

                result = self.__dive(a_target, b_target)
                if result != 0: return result

        return NONE

def do(A, B):

    # If pre-conditions differ, they cannot have any commonality
    pre_result = NONE
    if A.core().pre_context_begin_of_line_f() != B.core().pre_context_begin_of_line_f():
        # One depends on begin-of-line, the other doesn't => no commonality
        pre_result = NONE

    elif (A.core().pre_context_sm_id() != -1) != (B.core().pre_context_sm_id() != -1):
        # One depends on pre-conditions, the other doesn't => no commonality
        pre_result = NONE

    elif A.core().pre_context_sm_id() != -1:
        assert B.core().pre_context_sm_id() != -1
        # Both depend on pre-conditions: Are there commonalities in the pre-conditions?
        pre_result = Checker(A.pre_context_sm(), B.pre_context_sm())
    else:
        pre_result = BOTH

    if pre_result == NONE: return NONE

    # NOTE: Post-conditions do not change anything, since they match only when the whole
    #       lexeme has matched (from begin to end of post condition). Post-conditions only
    #       tell something about the place where the analyzer returns after the match.
    result = Checker(A, B).do()

    if result == NONE: return NONE

    if   pre_result == BOTH:   return result
    elif pre_result == result: return result 
    else:                      return NONE


