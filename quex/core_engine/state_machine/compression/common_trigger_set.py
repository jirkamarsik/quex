class Candidate:
    def __init__(self, TargetStateIndex, Union, Intersection, TriggerSetA, TriggerSetB):
        """TargetStateIndex -- index of target state to which the transition shall 
                               happen.
           TriggerSetA/B    -- trigger set of state A and B
        """
        self.target_index  = TargetStateIndex
        self.trigger_set_a = TriggerSetA
        self.trigger_set_b = TriggerSetB
        self.union         = TriggerSetA.union(TriggerSetB)
        self.intersection  = TriggerSetA.intersection(TriggerSetB)
        self.effort_trigger_set_a = effort(TriggerSetA)
        self.effort_trigger_set_b = effort(TriggerSetB)
        self.effort_union         = effort(self.union)
        self.effort_intersection  = effort(self.intersection)

    def propose(self, MaxCost):

        return cost, common_trigger_set, private_trigger_set_a, private_trigger_set_b



def do(TM_A, TM_B):

    trigger_set_drop_out_A = TM_A.get_trigger_set_union().inverse()
    trigger_set_drop_out_B = TM_B.get_trigger_set_union().inverse()
    candidate_db[None] = Candidate(None, trigger_set_drop_out_A, trigger_set_drop_out_B)
    for target_A, trigger_set_A in TM_A.iteritems():
        trigger_set_B = TM_B.get(target_A)
        if trigger_set_B == None:                             continue
        if not trigger_set_A.has_intersection(trigger_set_B): continue

        candidate_db[target_A] = Candidate(target_A, trigger_set_A, trigger_set_B)

    # A run for what is in TM_B is not necessary, because:
    #    if a target in TM_B is in TM_A, then is has already been checked.
    #    if a target in TM_B is not in TM_A, then it cannot contain a common transition.

LOG_2 = log(2)
def effort(TriggerSet):
    """This function determines the effort determine whether a number is in a
       trigger set. Assumed, that bisectioning is applied, the effort is
       proportional to log2 of the interval number.  
       
       Note, that a single value interval can be checked with a single comparison,
       thus the 'effort' is half of a normal interval.
    """
    global LOG_2

    sum = 0
    for interval in TriggerSet.get_intervals(PromiseToTreatWellF=True):
        if interval.end - interval.begin == 1: sum += 1
        else:                                  sum += 2

    return log(sum) / LOG_2  # = log2(sum)
