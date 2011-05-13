"""Identify 'barren' transitions that can be nested in a state.

   -- find 'simple transitions'.

   -- arrange the paths in a tree data structure (dictionary)
"""

class TreeNode:
    def __init__(self, FirstTarget, FirstTriggerSet):
        self.parent_state_index        = ParentStateIndex
        self.parent_tm                 = ParentTM
        self.child_db[ChildStateIndex] = ChildTM

        self.parent_catch_tm     = []
        self.children_common_tm  = []
        self.children_private_tm = {}

    def add_child(self, ChildStateIndex, ChildTM):
        self.child_db[ChildStateIndex] = ChildTM

    def child_list(self):
        return self.child_db.items()
        
    def freeze_this(self, ChildIndexList, ParentCatchTM, ChildrenCommonTM, ChildrenPrivateTM):
        for child_index in self.child_list.keys(): # NOT 'iterkeys()' we change the dictionary!
            if child_index not in ChildIndexList:
                del self.child_db[child_index]

        self.parent_catch_tm     = ParentCatchTM
        self.children_common_tm  = ChildrenCommonTM
        self.children_private_tm = ChildrenPrivateTM

def do(SM):

    # Build database about what state has what 'barren child transitions'
    child_db = __build_child_db(SM, LimitEffort=2.0) # DONE

    # Take only children that can be combined nicely, i.e. that are either
    # very small or have a lot in common.
    construction_db = {}
    for construction in map(__build_best_construction, child_db.itervalues()):
        construction_db[construction.parent_state_index] = construction

    return child_db

def __build_child_db(SM, LimitEffort):
    """Build a database about 'child states' that are reached from their
       parent state through a 'barren transition', i.e. a transition that
       requires only view comparisons.

              child_db:  state_index --> list of child state indices

       The number of comparisons is limited by the 'LimitEffort'.
    """
    child_db = {}
    for state_index, state in SM.states.iteritems():
        for target_index, trigger_set in state.transitions().get_map().iteritems():
            if effort(trigger_set) < LimitEffort:
                node = child_db.get(state_index)
                if node == None: child_db[target_index] = TreeNode(state_index, target_index, trigger_set, trigger_map)
                else:            node.add_child(target_index)

    return child_db

class Construction:
    def __init__(self, ParentStateIndex, ParentTM, ChildList):
        """Childlist = list of pairs: (child_state_index, child_tm)
                       child_tm = child's trigger map
        """

        # Delete transitions to children from ParentTM
        parent_tm = copy(ParentTM)
        for child_index, dummy in ChildList:
            del parent_tm[child_index]
        
        total_common_tm, adapt_list = __get_common_tm((ParentStateIndex, parent_tm) + ChildList)
        # adapt_list[0] == adaptations of the parent. 
        # adapt_list[1:] = adaptations of the children.
        children_common_tm = __get_common_tm(adapt_list[1:])

        children_private_tm_db  = {}

        cost =   effort(parent_catch_tm) \
               + effort(children_common_tm)
        for child_index, child_tm in ChildList:
            private_tm  = __difference(child_tm, children_common_tm)
            cost       += effort(private_tm)
            children_private_tm_db[child_index] = private_tm

def __build_best_construction(SM, parent_tm, node):
    # Start with all children present
    child_list = node.child_list()
    # Loop over exclusion. Always remove the 'worst' child and store
    # consider the cost of the 'construction'. Keep track of the best
    # construction in 'best_cost' and 'best_construction'.
    best_cost         = 1e37
    best_construction = None
    length = len(child_list)
    while length != 1:
        # Iterate over all children and determine the one that causes the highest cost
        best_tmp_cost         = 1e37
        best_tmp_construction = None
        best_tmp_child_list   = None
        for i in range(length):
            tmp_child_list = set(child_list)
            del tmp_child_set[i]
            cost, construction = __get_construction(ParentTM, tmp_child_list)
            if cost < best_tmp_cost:
                best_tmp_cost         = cost
                best_tmp_construction = construction
                best_tmp_child_list   = tmp_child_list

        # For the best child combination, check whether it competes with previous combinations
        if best_tmp_cost < best_cost:
            best_cost         = best_tmp_cost
            best_construction = best_tmp_construction
            best_child_list   = best_tmp_child_list

    # Tell the node, that may be some children are remove from the barren
    # transition. Also, tell the node about the code construction details.
    node.freeze_this(best_child_list, best_construction)

def __get_common_trigger_set_to_target(TargetIndex, InfoList):
    """Determine whether all related states trigger to the same target
       on the same trigger set. 

       -- If one state does not trigger to target at all, then the
          transition "trigger_set --> target" cannot be common, whatever
          trigger_set may be.

       -- If the trigger_set of one state differs, then the transition
          cannot be common.
    """
    common_trigger_set = None
    for dummy, tm in InfoList:

        trigger_set = tm.get(Target)

        if trigger_set == None: 
            return None

        elif common_trigger_set != None and common_trigger_set.is_equal(trigger_set):
            return -1

        common_trigger_set = trigger_set

    return common_trigger_set

def __union_is_covered(Target, InfoList, CommonTM):
    """The union of all trigger sets may be part of the common trigger map,
       if and only if, the triggers to targets that are not common cover
       for each state the 'holes'.
    """
    # Compute the union of all trigger sets to a certain target

    # We already know, that there are differences for certain trigger sets.
    # Now, if a difference appears, then try to cover it with 'uncommon' transitions.
    for dummy, tm in InfoList:
        raw_trigger_set = tm.get_map()[Target]
        if raw_trigger_set.is_equal(union): continue

        missing = union.difference(raw_trigger_set)

        # Try to 'cover' the miss-matching transitions with transitions that
        # are not part of the common transition map.
        for Target, trigger_set in tm.iteritems():
            # Only consider uncommon transitions
            if CommonTM.has_key(Target): continue
            missing.subtract(trigger_set)
            if missing.is_empty(): break
        else:
            # One state could not cover uncommon transitions with other transitions
            return None

        # State can cover holes with its own transitions --> Good, next please.

    return union

def __get_common_transitions(InfoList):
    """This function determines the common transition map of two states
       provided that their non-common transitions are checked before. For
       example:

         STATE A:  [a]  --> 4710          STATE B:  [b]  --> 4713
                   [bc] --> 4711                    [ac] --> 4711

       have the common transition: 

                                [abc] --> 4711 

       Provided that their other non-common transitions are checked before. 
       That is

         STATE A:  [a]  --> 4710          STATE B:  [b]  --> 4713
                   else --> COMMON                  else --> COMMON

                          COMMON:  [abc] --> 4711  

       Thus, the fact that 'a' is in the common transition does not harm state
       A, because if the input is 'a' it takes care of it before the COMMON is
       reached. Respectively, state B does not mind about 'b' being in the
       common set, ...

       RETURNS: A dictionary that contains the common transitions, i.e. a map

                target state index --> trigger_set

       The 'private transitions' of A and B can be determined easily. Any target
       state that appears in the common transition (the RETURN value) is not
       a 'private transition'. Any other is. This holds for the transition map
       of A and B.

    """
    target_state_set = set([])
    for state_index, tm in InfoList:
        target_state_set.update(tm.keys())

    common_tm        = {}
    partly_common_tm = {}
    # (1) Obviously common transitions ________________________________________
    #     Here, only transitions are considered to be common if they trigger
    #     on the **same** trigger set to the **same** target state.
    #
    #     Some transitions might not be exactly be the same, but their union 
    #     might be considered common, if the 'holes' are covered by other 
    #     transitions. Those candidates are collected in 'remainder'.
    remainder = []
    # 
    for target in target_state_set:

        common_trigger_set = __get_common_trigger_set_to_target(target, InfoList)

        if common_trigger_set == None: 
            # There is simply no common transition to the target. Forget it.
            continue

        elif common_trigger_set == -1:
            # If all have the same target but differ in their trigger sets
            # then the transition can still enter the common set. This is 
            # possible if the differences are covered by their 'holes'.
            # => Watch out, later.
            remainder.append(target)
            continue

        else:
            # If all transitions trigger at exactly the same trigger set
            # => Accept the transition the trigger set into the common set.
            common_tm[target] = (a_trigger_set, None, None)
            continue

    # (2) Non-obvious common transitions _____________________________________
    # 
    #     EXAMPLE:    StateA:               StateB:
    #                 'a'   --> 4710        'z'   --> 4709
    #                 [b-z] --> 4711        [a-y] --> 4711
    #
    #     Both states do not have an exact common transition. But, considering
    #     that the uncommon transitions are tested first, it becomes clear that
    #     '[a-z]' is a common transition. The test for 'a' and 'z' covers the
    #     later test and the fact that is is included in the common set does 
    #     not harm.
    # 
    #     The 'cover' depends on the set of remaining uncommon transitions.
    #     It also relative to the currently tested candidate for a common
    #     transition.
    candidate_list = []
    # Compute the 'unions' and sort them by effort.
    for target in remainder:
        union = NumberSet()
        for dummy, tm in InfoList:
            union.unite_with(tm.get_map()[Target])
        candidate_list.append((effort(union), target, union))

    candidate_list.sort(key=itemgetter(0), reverse=True)

    common_union_trigger_set = NumberSet()
    for trigger_set in common.itervalues():
        common_union_trigger_set.unite_with(trigger_set)

    
    for cost, target, union in candidate_list:
        if __union_is_covered(union, InfoList):
            common_tm[target] = union_trigger_set
            common_union_trigger_set.unite_with(union_trigger_set)
            # ! If a new target is added to common_tm, this may change the !
            # ! shadowing set.                                             !

#def __Partly common transitions not handled yet.
#        # NOTE: Set operation '-':   X - Y = X & (not Y)
#        #
#        # Union = candidate trigger set for common transition
#        #       = a_trigger_set | b_trigger_set
#        #
#        # The set of 'holes' in A is what A does not have in its own trigger set, i.e.
#        #
#        # a_holes = Union - a_trigger_set
#        #         = Union & (not a_trigger_set)
#        #         = (a_trigger_set & not a_trigger_set) | (b_trigger_set & not a_trigger_set)
#        #
#        # Thus:
#        a_holes = b_trigger_set.difference(a_trigger_set)
#        # Respectively:
#        b_holes = a_trigger_set.difference(b_trigger_set)
#
#        # (1) If both 'holes' are covered by their 'shadows' (see above) then the union
#        #     can enter the set of common transitions
#        if     a_shadow_trigger_set.is_superset(a_holes) \
#           and b_shadow_trigger_set.is_superset(b_holes):
#            common_tm[target] = a_trigger_set.union(b_trigger_set)
#            continue
#
#        if not PartlyCommonTransitionsF: continue
#
#        # (2) Consider 'partly common transitions', i.e. where the states do parts of 
#        #     the transitions on their own.
#        partly_common = get_common_transition(a_shadow_trigger_set, a_trigger_set,
#                                              b_shadow_trigger_set, b_trigger_set)
#        if partly_common != None:
#            common_tm[target]     = partly_common 
#            a_adaption_db[target] = a_trigger_set.union(a_shadow_trigger_set).difference(partly_common)
#            b_adaption_db[target] = b_trigger_set.union(a_shadow_trigger_set).difference(partly_common)
#
#    return common_tm, a_adaption_db, b_adaption_db
#
#def __get_partly_common_transition(a_shadow, ATriggerSet, a_shadow, BTriggerSet):
#    """Determine the set of partly common transitions.
#
#       RETURNS: None, None, None 
#       
#                   If it is not worth to consider the set of partly
#                   common transitions, because it is too expensive.
#
#                PartlyCommon, DiffA, DiffB 
#                
#                   The set of partly common transitions, the trigger set
#                   that A needs to implement, and the trigger set that 
#                   remains for B to implement.
#
#       EFFORT:
#
#           Determine the 'effort' to implement the partly common transitions.
#           Recall the setup for an implemented partly common transition:
#
#             STATE A:  [a]  --> 4710          STATE B:  [b]  --> 4713
#                       [e]  --> 4711                    [d]  --> 4711
#                       else --> COMMON                  else --> COMMON
#                                                        
#
#                              COMMON:  [abc] --> 4711
#
#           The effort for transitions not-related to the partly common set can
#           be omitted. It is the same anyway-with and without partly common
#           implementation. Now, the effort of the implementation is
#
#                      effort(PartlyCommon) 
#                    + effort(TransitionInA) 
#                    + effort(TransitionInB)
#    """
#    partly_common = determine_partly_common_transition(a_shadow, ATriggerSet, 
#                                                       b_shadow, BTriggerSet)
#
#    diff_a = ATriggerSet.difference(PartlyCommon)
#    diff_b = BTriggerSet.difference(PartlyCommon) 
#    effort = effort(partly_common) + effort(in_a) + effort(in_b)
#
#    # Effort without a partly common transition = effort for 'a_trigger_set'
#    # plus effort for 'b_trigger_set'. This we do bisectioning the effort is 
#    # proportional log2(number of intervals).
#    original_effort =   effort(a_trigger_set)
#                      + effort(b_trigger_set)
#
#    # Only if it is worth, accept the partly common transition         
#    if original_effort > effort:
#        return partly_common, diff_a, diff_b
#
#    return None, None, None
#
#def determine_partly_common_transition(a_shadow, ATriggerSet, a_shadow, BTriggerSet):
#    """ASSUMPTION: 
#    
#          "a_shadow" and "b_shadow" are no longer needed. We modify them to
#          avoid expensive copying.
#
#          (Note, that "ATriggerSet" and "BTriggerSet" are not modified.)
#
#       EXPLANATION:
#    
#       It is possible that there is a common trigger set that just needs some
#       help from one or the other state. Example:
#
#         STATE A:  [a]   --> 4710          STATE B:  [b]   --> 4713
#                   [bce] --> 4711                    [acd] --> 4711
#
#       Here, [abc] or [abcd] would not be a common trigger set in the sense of
#       'get_common_transitions()'. It cannot be [abc], because state B triggers
#       on [d] to 4711 and it cannot be [abcd] because state A does not require
#       [d] to trigger to 4711. But, if one of the two states 'helps' then there
#       can be a solution. Actually, there are three possible solutions:
#
#       Solution:
#
#         STATE A:  [a]  --> 4710          STATE B:  [b]  --> 4713
#                   [e]  --> 4711                    [d]  --> 4711
#                   else --> COMMON                  else --> COMMON
#                                                    
#
#                          COMMON:  [abc] --> 4711
#
#                          Union               = [abcde] = A | B
#                          SymmetricDifference = [abde]  = A (-) B
#                          a_shadow            = [a]
#                          b_shadow            = [b]
#
#       SymmetricDifference(A, B) is the set of elements that are in A or B but
#       not in both.  For the term 'shadow' see function 'get_common_transitions()'. 
#       Let
#                          S = a_shadow | b_shadow
#       Then,
#                .----------------------------------------------------.
#          (1)   | PartlyCommon = Union - (SymmetricDifference - S)   |
#                '----------------------------------------------------'
#
#       With "X - (Y - Z) = (X & Z) | (X - Y)", where X = Union, 
#       Y = SymmetricDifference, and Z = S, it follows
#
#          (2) PartlyCommon = (Union & S) | (Union - SymmetricDifference)
#
#          (3) Union - SymmetricDifference = (A | B) - (A (-) B) = A & B
#              -----------------------------                     --------
#
#       If this is not clear, then draw it or calculate it. Thus, with (3)
#       in (2) it follows
#
#          (4) PartlyCommon = ((A | B) & S) | (A & B)
#    """
#
#    # S = a_shadow | b_shadow
#    s = a_shadow
#    s.unite_with(b_shadow)
#
#    # Union = A | B
#    union = ATriggerSet.union(BTriggerSet)
#
#    # Intersection = A & B
#    intersection = ATriggerSet.intersection(BTriggerSet)
#
#    # PartlyCommon = (Union & S) | Intersection
#    result = union
#    result.intersect_with(s)
#    result.unite_with(intersection)
#    return result
#    
