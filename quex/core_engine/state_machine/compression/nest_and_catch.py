# (C) 2010 Frank-Rene Schaefer
"""
   Barren Tree Compression _____________________________________________________
   
   The goal of barren tree compression is to be able to express parts of the
   state machine directly as nested if-then clauses--without the need of 
   explicit state transitions (i.e. gotos). For example, a state machine that
   identifies the keywords 'move' and 'mode' as well as the identifiers matching
   the regular expression [a-z]+ should be written as


      /* Something that identifies 'm' */
      ...

      /* Barren tree to check for 'ove', 'ode' and identifier. */
BARREN_TREE_ROOT_0:
      ++input_p;
      if( *input_p == 'o' ) { 
          ++input_p;
          if( *input_p == 'd' ) { 
              ++input_p;
              if( *input_p == 'e' ) { 
                  ++input_p;
                  goto TERMINAL_MODE;
              }
          }
          else if( *input_p == 'v' ) { 
              ++input_p;
              if( *input_p == 'e' ) { 
                  ++input_p;
                  goto TERMINAL_MOVE;
              }
          }
      }
      if( *input_p in [a-z] ) { 
          goto CHECK_IDENTIFIER;
      }
      if( *input_p == BufferLimitCode ) { 
          reload(...);
          goto __InitialState;
      }
      else { 
          goto TERMINAL_IDENTIFIER;
      }

CHECK_IDENTIFIER:
      ++input_p;
      if( *input_p >= 'a' && *input_p <= 'z' ) { 
          goto TERMINAL_IDENTIFIER;
      }
      goto TERMINAL_IDENTIFIER;
      
   Note, that the detection of 'm' cannot be part of the barren tree, since for
   if the lexeme does not start with 'm' and is not in [a-z] and not the buffer
   limit code, then it is a failure. For the barren tree above the state
   machine transits to success for IDENTIFIER.


   Requirements for a state to be part of a barren tree ________________________

       Transition to state requires less then N comparisons
       (N=2 is may be the best for checking just one range.)

   Result of Analysis __________________________________________________________

       A barren tree is a set of states organized as a tree. A tree_node
       contains:

            barren_transition_map[target_index] --> trigger_set 

                This is the list of all transition to subsequent states
                that can be reached by a 'barren' transition, i.e. a very
                tiny trigger set.

            fat_transition_map[target_index] --> trigger_set

                Remaining transitions that are not considered to be 
                'barren'.

            drop_out_info

                Information about 'drop-out' behavior.

      All nodes of the barren tree are accessible via a dictionary, i.e.

            tree_db[state_index] --> tree_node

   _____________________________________________________________________________
"""
from quex.core_engine.interval_handling            import NumberSet

from math import log

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

"""An object of this class describes the 'relationship' between
   a state A (the 'parent') and a state B (the 'child') where 
   there are transitions from A to B. That means, that B can
   potentially be nested into A.

   The decision about nesting B into A is based on how much of 
   the transition map of B can be caught by A's transition map.
   For example:

    STATE_A:                   STATE_B:
                                                 
       if *p == 'm':              if *p == 'z':
           goto STATE_B;              goto 4712;
       if *p in [a-ln-z]:         if *p in [a-y]:
           goto 4711;                 goto 4711;

    Can be transformed into:

       if *p == 'm':         # From STATE_A
          ++p;
          if *p == 'z':      # From STATE_B
              goto 4712;
       if *p in [a-z]:       # Common remainder for both, provided
          goto 4711;         # that 'm' and 'z' are checked before.

    Potentially, there might be open wildcards from trigger ranges
    that appear in A and B. This object contains:

        -- common catch map.

        -- wildcard trigger map.
"""

def get_private_map_for_child(Child, ParentCM):
    """ParentCM -- Parent State's Catch Trigger Map
                   This is the trigger map that is placed after all
                   nested states. The nested states drop into this map
                   if they fail with their tests.

       ** NOTE: The ParentCM must contain a '-1' target that triggers **
       **      on 'drop-out', i.e. when no other target triggers.     **

       Child  -- Child State

       IDEA: The child might be nested in the parent state so that some
             transitions of the child might actually happen in the parent's
             trigger map (provided they are partly the same). Thus, the 'sum' 

                           child's private trigger map
                         + parent's catch map
               (1)     ---------------------------------
                         = child's trigger map

             The 'sum' is actually more like a union where the child's private
             trigger map dominated. That means, that if the parent's catch map
             and the child's private trigger map might trigger on the same
             trigger, but the private trigger map dominates.

        SOLUTION: 
        
            A child's private trigger map that can be determined so that
            equation (1) holds can be determined as follows:

            (A) If child's trigger map triggers to a target which is not in
                parent's catch map, then the whole transition enters the
                child's private trigger map. Here the child cannot rely at all
                on the parent's catch map.

            (B) If the child's triggers to a target that is also in the parent's 
                catch map, then 

                  (i) if the related trigger maps are the same
                      => nothing to be done, parent catches correctly.

                  (ii) else this means that the parent's catch map can't help
                       for the whole trigger set. 
                       => Difference of the trigger set, must enter the child's 
                          private trigger map.

             This solution only works, if the 'drop-out' target is contained 
             as a target, here '-1'.
    """
    assert type(ParentCM) == dict
    assert ParentCM.has_key(-1L)

    def add(private_tm, Target, TriggerSet):
        trigger_set = private_tm.get(Target)
        if trigger_set == None:
            private_tm[Target] = deepcopy(TriggerSet)
        else:
            trigger_set.unite_with(TriggerSet)

    # Generate a trigger map that also contains the '-1' for drop out.
    child_tm = Child.transitions().get_map().items() 
    child_tm.append((-1L, Child.transitions().get_drop_out_trigger_set_union()))

    # -- Anything that contradicts with the parent's catch map must be done in the
    #    child's private map:  
    #                          target state index ---> trigger set 
    private_tm = {}

    for child_target, child_trigger in child_tm:
        parent_catch_trigger = ParentCM.has_key(child_target)
        if parent_catch_trigger == None:
            # (A) Parent's catch map doesn't even transit to target
            add(private_tm, child_target, child_trigger)

        elif parent_catch_trigger.is_equal(child_trigger):
            # (B.i) Parent's catch map is exactly the same as the child
            #       => child does not have to do anything.
            pass
        else:
            # (B.ii) Parent's catch map is not enough.
            #        => child needs to do something
            add(private_tm, child_target, child_trigger.difference(parent_catch_trigger))

    return private_tm
            

def nest(SM, State):

    def get_metric(trigger_map):
        complexity = 0
        for trigger_set in trigger_map.values():
            complexity += trigger_set.interval_number()
        return complexity

    parent_tm = copy(State.transitions().get_map())

    # Go through all subsequent states (childs) and determine their 'private map'.
    # That is, the trigger map that cannot be done by a drop into the parent's trigger map.
    child_list = parent_tm.iterkeys()
    # Find commonalities between childs
    for i, child_a in enumerate(child_list):
        for child_b in child_list[i+1:]:
            get_common_transitions(SM, child_a, child_b)


    # Determine commonality between child's private maps
    commonality = determine_commonality(db)
    
    # Determine the set of nested childs

    # Recompute the catch map

    # Recompute the child's private map

    # See what parts of private maps can be done by wildcards

CommonTransitionDB_Entry_id_counter = -1L
class CommonTransitionDB_Entry:
    def __init__(self, TargetIdx, TriggerSet, *StateIndeces):
        CommonTransitionDB_Entry_id_counter += 1L

        self.id              = CommonTransitionDB_Entry_id_counter
        self.target_index    = TargetIdx
        self.trigger_set     = TriggerSet
        self.state_index_set = set(StateIndeces)

class CommonTransitionDB:
    def __init__(self):
        self.db             = []
        # Map: superset id --> subset id
        self.superset_db       = {}
        # Map: state index to the database entry that contains it
        self.state_to_entry_db = {}

    def add(self, StateIndexA, StateIndexB, CommonTriggerSet):
        global common_transition_id_counter

        for info in common_transition_group_db:
            # (1) If the common transition is already there, 
            #     then just add the new state indeces.
            if CommonTriggerSet.is_equal(info.trigger_set): 
                info.state_index_set.add(StateIndexA) 
                info.state_index_set.add(StateIndexB) 
                self.state_index_to_entry_db.setdefault(StateIndexA, set([]).add(entry.id)
                self.state_index_to_entry_db.setdefault(StateIndexB, set([]).add(entry.id)
                break
        else:
            # (2) If the transition was not known to the database,
            #     then add it.
            new_entry = CommonTransitionDBEntry(TargetIdx, CommonTriggerSet, StateIndexA, StateIndexB])
            self.db.append(new_entry)
            self.state_index_to_entry_db.setdefault(StateIndexA, set([]).add(entry.id)
            self.state_index_to_entry_db.setdefault(StateIndexB, set([]).add(entry.id)

            # Now, the superset/subset relations must be registered
            for entry in common_transition_group_db:
                if entry.trigger_set.is_superset(CommonTriggerSet):
                    self.superset_db[entry.id]     = new_entry.id
                elif CommonTriggerSet.is_superset(entry.trigger_set):
                    self.superset_db[new_entry.id] = entry.id

common_transition_db = {}
def common_transition_db_get(A, B):
    """The common transitions between two states are kept in a 
       little database, so that they do not have to be computed twice.

       Once, all computations are done 'common_transition_db_cleer()'
       can be called to free the related memory.
    """
    global common_transition_db

    x = common_transition_db.get(A)
    if x == None: return None
    y = x.get(B)
    if y == None: return None
    return y

def common_transition_db_clear(A, B):
    """Free the memory related to the cache."""
    global common_transition_db
    common_transition_db.clear()


class Info:
    """Note: The path.CharacterPath class a lot in common with the Info.

       The transitions of a state are categorized into 'barren' and 'fat'.

       -- A barren transition is a transition to subsequent state on the 
          bases of very few comparisons with respect to the input.

       -- Also, the state to which the barren transition triggers must
          fit, i.e. its 'fat transitions' and drop-out action must
          correspond.

       A transition that is not barren is fat.
    """
    def __init__(self, State, FatTransitionMap, BarrentTransitionMap):
        assert isinstance(StartStateIndex, long)
        assert isinstance(FatTransitionMap, dict)

        self.__state  = State

        # Transitions: target_index --> trigger set that triggers to target
        #    barren transitions: transitions on small sets to small fitting states.
        #    fat transitions:    remainder of transitions.
        self.__barren = BarrenTransitionMap
        self.__fat    = FatTransitionMap

        # The trigger sets of 'barren' transitions can be occupied by 
        # arbitrary values, let them be called 'wildcards'.
        trigger_set = NumberSet()
        for trigger_set in self.__barren.values():
            self.__wildcard_set.unite_with(trigger_set)

    def barren(self):
        return self.__barren

    def fat(self):
        return self.__fat

    def move_to_fat(self, TargetIndex):
        """Moves a transition to TargetIndex from the set of barren
           transitions to the set of 'fat' transitions.
        """
        assert self.__barren.has_key(TargetIndex)

        trigger_set = self.__fat.get(TargetIndex)
        if trigger_set == None: self.__fat[TargetIndex] = self.__barren[TargetIndex]
        else:                   trigger_set.unite_with(self.__barren[TargetIndex])

        del self.__barren[TargetIndex]

    def plug_wildcards(self, WildcardMap):
        """The given wildcards become part of the fat transitions."""
        for target_index, trigger_set in WildcardMap.items():
            fat_trigger_set = self.__fat.get(target_index)
            if fat_trigger_set == None: self.__fat[target_index] = trigger_set
            else:                       fat_trigger_set.unite_with(trigger_set)

            self.__wildcard_set.subtract(trigger_set)

    def match(self, CandidateFatTransitionMap, CandidateBarrenTriggerSet):
        """-- The candidate **needs** all transitions in the fat transition map
              in case that no one of its sub-trees is concerned. 

           -- The Tree **can** provide the 'skeleton' transition map and can
              extend the map characters in the wildcard set.

           RETURNS: NumberSet --> Characters from the wild card that need to be used to 
                                  achieve the match. Match is good.
                    empty set --> No wildcard necessary, but match is good.
                    None      --> No match possible.
        """
        # All transitions in the FatTransitionMap must appear in the Skeleton
        #
        #     [     5     ][2]     [    3    ][ 1 ]              skeleton
        #                   *                 *****              wildcard set
        #
        #     [     5     ][6]     [    3    ]     [    6     ]  candidate FAIL
        #     [     5     ][6]     [    3         ]              candidate OK
        #     [     5     ][1]     [    3         ]              candidate OK
        #
        #     -- except for those covered by the wildcards.
        only_in_A, \
        only_in_B, \
        diff_in_both      = \
                get_metric(self.__fat, CandidateFatTransitionMap)

        # (1) what is in self's 'fat' but not in candidate's 'fat transition' 
        #     can **only** be covered by barren transitions of candidate.
        if not only_in_A.is_empty():
            if not CandidateBarrenTriggerSet.is_superset(only_in_A): return None

        # (2) If self and candidate transit to different states on the same trigger set, then
        #     They can only be covered by barren trigger sets of the candidate.
        if not diff_in_both.is_empty():
            if not CandidateFatTransitionMap.is_superset(diff_in_both): return None

        # (3) what is in candidate's 'fat' but not in self's 'fat transition' 
        #     can **only** be covered by wildcards.
        used_wildcard_set = NumberSet()
        if not only_in_B.is_empty():
            if not self.__wildcard_set.is_superset(diff_in_both): return None
            # Take the reference to 'only_in_B' to avoid object creation
            used_wildcard_set = only_in_B
            used_wildcard_set.intersect_with(self.__wildcard_set)

        return used_wildcard_set

def categorize(SM, MaxComparisonN):
    # A state can only be absorbed by one other state.
    # => book keeping about each state that has been absorbed already.
    done_set = set([])

    tree_db  = {}
    # Here, the loop determines the sequence of processing, therefore 
    # determines the **priorization** of where states are absorbed. States that
    # come first, can absorb a subsequent state, later states **must** transit
    # to the subsequent state.
    for state_index, state in SM.items():
        barren, fat = categorize_transitions(State, MaxComparisonN)
        for target_index, trigger_set in barren.items():
            if target_index in done_set: 
                # Move transition to 'fat transitions'
                fat[target_index] = trigger_set
                del barren[target_index]
            else:
                done_set.add(target_index)

        if barren.is_empty(): barren = None
        tree_db[state_index] = TreeBase(state, fat, barren)

    # Barren transitions to states which misfit become part of the fat transitions.
    info_changed_f = False
    while 1 + 1 == 2:

        for state_index, info in sorted(tree_db.items(), my_sort):

            transition_change_f = False
            while 1 + 1 == 2:

                backup = info.wildcard_set()

                for target_index, trigger_set in info.barren_transition_map():
                    target_info        = tree_db[target_index]
                    required_wildcards = info.match(target_info)
                    #
                    if required_wildcards == None:
                        # Misfit --> 'fat transition'
                        info.move_to_fat(target_index)
                        transition_change_f = True
                        info_changed_f      = True
                        break

                    elif required_wildcards.is_empty() == False:
                        info.plug_wildcards(required_wildcards)

                # While there was a change in the 'fat transitions' we need to check
                # again if the fat transitions match.
                if not transition_change_f: break
                
                info.set_wildcard_set(backup)

        if not info_changed_f: break

    return tree_db

def categorize_transitions(State, MaxComparisonN):
    """This function categorizes the transitions of a state into 'barren' and
       'fat' transitions. That is, barren transitions happen on small character
       sets that can be compared with less or equal MaxComparisonN. Any
       transition taking more comparisons than that are 'fat' transitions.
    """
    transition_map = State.transitions().get_map()

    barren_transition_map = {}
    for target_index, trigger_set in transition_map.items():
        interval_list = trigger_set.get_intervals(PromiseToTreatWellF=True)
        cmp_required  = 0
        for interval in interval_list:
            if interval.end - interval.begin < 2: cmp_required += 1 # Check '==' begin
            else:                                 cmp_required += 2 # Check '>=' begin and '<' end
            if cmp_required > MaxComparisonN: break
        if cmp_required > MaxComparisonN: 
            fat_transition_map[target_index] = trigger_set
        else:
            barren_transition_map[target_index] = trigger_set

    return barren_transition_map, fat_transition_map


