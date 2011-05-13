from   quex.frs_py.string_handling import blue_print
#
from   quex.core_engine.interval_handling        import NumberSet, Interval
import quex.core_engine.state_machine.index      as     state_machine_index
from   quex.core_engine.state_machine.transition_map  import *
from   quex.core_engine.state_machine.state_core_info import StateCoreInfo
from   quex.core_engine.state_machine.origin_list     import StateOriginList

import sys
from   copy import copy, deepcopy
from   operator import attrgetter


class State:
    # Information about all transitions starting from a particular state. Transitions are
    # of two types:
    #   
    #      -- normal transitions: triggered when a character arrives that falls into 
    #                             a trigger set.
    #      -- epsilon transition: triggered when no other trigger of the normal transitions
    #                             triggers.
    #
    # Objects of this class are to be used in class StateMachine, where a dictionary maps 
    # from a start state index to a State-object.

    def __init__(self, AcceptanceF=False, StateMachineID=-1L, StateIndex=-1L):
        """Contructor of a State, i.e. a aggregation of transitions.
        """
        self.__core        = StateCoreInfo(StateMachineID, StateIndex, AcceptanceF=AcceptanceF)
        self.__origin_list = StateOriginList()

        # normal transitions: trigger, action, target-state-index
        self.__transition_map = TransitionMap()

    def core(self):
        return self.__core

    def _set(self, Core, OriginList, TMap):
        """This function allows a derived class to impose values on 
           the core members of this class.
        """
        self.__core        = Core
        self.__origin_list = OriginList
        if isinstance(TMap, dict): self.__transition_map = TransitionMap(TMap)
        else:                      self.__transition_map = TMap

    def origins(self):
        return self.__origin_list

    def transitions(self):
        return self.__transition_map

    def merge(self, Other):
        # merge core information of self with other state
        self.core().merge(Other.core())
        if   Other.origins().is_empty(): return 
        elif self.origins().is_empty():  
            self.origins().set(Other.origins().get_list())
        else: 
            self.origins().append(Other.origins().get_list(), 
                                  StoreInputPositionFollowsAcceptanceF=False,
                                  SelfAcceptanceF=self.is_acceptance())

    def is_acceptance(self):
        return self.core().is_acceptance()

    def is_equivalent(self, Other):
        """Determines whether two states are 'equivalent' in the sense that 
           they have the same acceptance, store input positions, pre-context, etc.
           attributes.
        """
        return     self.core().is_equivalent(Other.core())       == True \
               and self.origins().is_equivalent(Other.origins()) == True
        
    def set_acceptance(self, Value=True, LeaveStoreInputPositionF=False):
        self.core().set_acceptance_f(Value, LeaveStoreInputPositionF)

    def mark_self_as_origin(self, StateMachineID, StateIndex):
        self.core().state_machine_id = StateMachineID
        self.core().state_index      = StateIndex
        # use the own 'core' as only origin
        self.origins().set([self.core()])

    def add_origin(self, StateMachineID_or_StateOriginInfo, StateIdx=None, StoreInputPositionF=None):
        self.origins().add(StateMachineID_or_StateOriginInfo, StateIdx, 
                           StoreInputPositionF, self.is_acceptance())

    def add_transition(self, Trigger, TargetStateIdx): 
        self.__transition_map.add_transition(Trigger, TargetStateIdx)

    def transform(self, TrafoInfo):
        """RETURNS: True  transformation successful
                    False transformation failed, number set possibly in inconsistent state!
        """
        return self.__transition_map.transform(TrafoInfo)
    
    def clone(self, ReplacementDictionary=None):
        """Creates a copy of all transitions, but replaces any state index with the ones 
           determined in the ReplacementDictionary."""
        result = State()
        result.__core           = deepcopy(self.__core)
        result.__transition_map = deepcopy(self.__transition_map)
        result.__origin_list    = deepcopy(self.__origin_list)
        # if replacement of indices is desired, than do it
        if ReplacementDictionary != None:
            result.transitions().replace_target_indices(ReplacementDictionary)

        return result

    def __repr__(self):
        return self.get_string()

    def get_string(self, StateIndexMap=None, Option="utf8"):
        # if information about origins of the state is present, then print
        msg = self.origins().get_string()
        fill_str = ""
        if msg != "": fill_str = "     "

        msg = self.core().get_string(StateMachineAndStateInfoF=False) + msg

        # print out transitionts
        msg += self.transitions().get_string(fill_str, StateIndexMap, Option)
        return msg

    def get_graphviz_string(self, OwnStateIdx, StateIndexMap, Option):
        assert Option in ["hex", "utf8"]
        return self.transitions().get_graphviz_string(OwnStateIdx, StateIndexMap, Option)

class StateMachineCoreInfo:
    def __init__(self, ID, 
                 PreContextSM=None, 
                 PreContext_BeginOfLineF=False, 
                 PreContext_SingleCharacterList=[]):

        self.__id                                  = ID 
        self.__pre_context_sm                      = PreContextSM
        self.__pre_context_begin_of_line_f         = PreContext_BeginOfLineF
        self.__pre_context_single_character_list   = PreContext_SingleCharacterList
        self.__post_context_id                     = -1L
        self.__post_context_backward_input_position_detector_sm = None

    def id(self):                                  
        return self.__id
    def pre_context_sm(self):                      
        return self.__pre_context_sm
    def pre_context_sm_id(self):
        if self.__pre_context_sm != None: return self.__pre_context_sm.core().id()
        else:                             return -1L
    def pre_context_begin_of_line_f(self):         
        return self.__pre_context_begin_of_line_f         
    def pre_context_single_character_list(self):   
        return self.__pre_context_single_character_list   
    def post_context_id(self):                     
        return self.__post_context_id                     
    def post_context_backward_input_position_detector_sm(self): 
        return self.__post_context_backward_input_position_detector_sm
    def post_context_backward_input_position_detector_sm_id(self): 
        if self.__post_context_backward_input_position_detector_sm != None: 
            return self.__post_context_backward_input_position_detector_sm.core().id()
        else:
            return -1L

    def has_pre_or_post_context(self):
        return    self.__pre_context_single_character_list \
               or self.__pre_context_single_character_list != [] \
               or self.__pre_context_sm != None \
               or self.__post_context_id != -1L \
               or self.__post_context_backward_input_position_detector_sm != None

    def set_id(self, Value):                                  
        assert type(Value) == long
        self.__id = Value
    def set_pre_context_sm(self, Value):                      
        assert Value.__class__.__name__ == "StateMachine" or Value == None
        self.__pre_context_sm = Value
    def set_pre_context_begin_of_line_f(self, Value=True):         
        assert type(Value) == bool
        self.__pre_context_begin_of_line_f = Value
    def set_pre_context_single_character_list(self, Value):   
        assert type(Value) == list
        self.__pre_context_single_character_list = Value
    def set_post_context_id(self, Value):                     
        assert type(Value) == long
        self.__post_context_id = Value
    def set_post_context_backward_input_position_detector_sm(self, Value): 
        assert Value.__class__.__name__ == "StateMachine" or Value == None
        self.__post_context_backward_input_position_detector_sm = Value

class SideInfo:
    def __init__(self, NewlineN=-1, CharacterN=-1):
        self.__newline_n         = NewlineN
        self.__character_n       = CharacterN

    def get_newline_n(self):
        """  -1    => number of newlines in matching lexemes is not deterministic
             N > 0 => number of newlines in matching lexemes is always 'N'.
        """
        # Value is to be computed by 'character_counter.get_newline_n()'
        # for the core pattern, not for pre-conditions and not for post-conditions.
        assert self.__newline_n != None, \
               "Pattern state machine not constructed by regular_expresion.__construct(...)"
        return self.__newline_n

    def get_character_n(self):
        """  -1    => length of lexemes that match pattern is not deterministic
             N > 0 => length of lexemes that match is always 'N'.
        """
        # Value is to be computed by 'character_counter.get_newline_n()'
        # for the core pattern, not for pre-conditions and not for post-conditions.
        assert self.__character_n != None, \
               "Pattern state machine not constructed by regular_expresion.__construct(...)"
        return self.__character_n

class StateMachine:

    def __init__(self, InitStateIndex=None, AcceptanceF=False, Core=None):

        # print "##state_machine_init"
        if InitStateIndex == None: self.init_state_index = state_machine_index.get()
        else:                      self.init_state_index = InitStateIndex
            
        # State Index => State (information about what triggers transition to what target state).
        self.states = { self.init_state_index: State(AcceptanceF) }        

        # get a unique state machine id 
        id = state_machine_index.get_state_machine_id()

        # Setup core information
        if Core != None: 
            self.__core = deepcopy(Core)
            self.__core.set_id(id)
        else:            
            self.__core = StateMachineCoreInfo(id)

        self.side_info = None

    def core(self):
        return self.__core
            
    def clone(self):
        """Clone state machine, i.e. create a new one with the same behavior,
        i.e. transitions, but with new unused state indices. This is used when
        state machines are to be created that combine the behavior of more
        then one state machine. E.g. see the function 'sequentialize'. Note:
        the state ids SUCCESS and TERMINATION are not replaced by new ones.

        RETURNS: cloned object if cloning successful
                 None          if cloning not possible due to external state references

        """
        replacement = {}

        # (*) create the new state machine
        #     (this has to happen first, to get an init_state_index)
        result = StateMachine()

        # every target state has to appear as a start state (no external states)
        # => it is enough to consider the start states and 'rename' them.
        # if later a target state index appears, that is not in this set we
        # return 'None' to indicate that this state machine cannot be cloned.
        sorted_state_indices = self.states.keys()
        sorted_state_indices.sort()
        for state_idx in sorted_state_indices:
            # NOTE: The constructor already delivered an init state index to 'result'.
            #       Thus self's init index has to be translated to result's init index.
            if state_idx == self.init_state_index:
                replacement[state_idx] = result.init_state_index
            else:
                replacement[state_idx] = state_machine_index.get()
        # termination is a global state, it is not replaced by a new index 

        for state_idx, state in self.states.items():
            new_state_idx = replacement[state_idx]
            result.states[new_state_idx] = self.states[state_idx].clone(replacement)
        
        result.__core = deepcopy(self.__core)

        ## DEBUG: Check that every transition target is part of state machine
        ## for state in result.states.values():
        ##    for target_idx in state.transitions().get_map().keys():
        ##        assert result.states.has_key(target_idx)
            
        return result

    def get_id(self):
        return self.__core.id()

    def get_init_state(self):
        return self.states[self.init_state_index]

    def is_init_state_a_target_state(self):
        init_state_index = self.init_state_index
        for state in self.states.values():
            target_state_index_list = state.transitions().get_target_state_index_list()
            if init_state_index in target_state_index_list: return True
        return False
        
    def has_orphaned_states(self):
        """Detect whether there are states where there is no transition to them."""
        unique = set([])
        for state in self.states.values():
            unique.update(state.transitions().get_target_state_index_list())

        for state_index in self.states.keys():
            # The init state is never considered to be an 'orphan'
            if state_index not in unique and state_index != self.init_state_index: return True
        return False

    def get_orphaned_state_index_list(self):
        """This function checks for states that are not targeted via any trigger
           by any other state. This indicates most likely a lack off efficiency 
           or an error in the algorithms.
        """
        unique = set([])
        for state in self.states.values():
            unique.update(state.transitions().get_target_state_index_list())

        result = []
        for state_index in self.states.keys():
            # The init state is never considered to be an 'orphan'
            if state_index not in unique and state_index != self.init_state_index: 
                result.append(state_index)

        return result

    def get_epsilon_closure_db(self):
        db = {}
        for index, state in self.states.items():
            # Do the first 'level of recursion' without function call, to save time
            index_list = state.transitions().get_epsilon_target_state_index_list()

            # Epsilon closure for current state
            ec = { index: True }
            if len(index_list) != 0: 
                for target_index in index_list:
                    if ec.has_key(target_index): continue
                    ec[target_index] = True
                    self.__dive_for_epsilon_closure(target_index, ec)

            db[index] = ec

        return db

    def get_epsilon_closure_of_state_set(self, StateIdxList, EC_DB):
        """Returns the epsilon closure of a set of states, i.e. the union
           of the epsilon closures of the single states.
           
           StateIdxList: List of states to be considered.
           EC_DB:        Epsilon closure database, as computed once by
                         'get_epsilon_closure_db()'.
        """
        result = {}
        for index in StateIdxList:
            result.update(EC_DB[index])

        return result.keys()

    def __dive_for_epsilon_closure(self, state_index, result):
        index_list = self.states[state_index].transitions().get_epsilon_target_state_index_list()
        for target_index in index_list:
            if result.has_key(target_index): continue
            result[target_index] = True
            self.__dive_for_epsilon_closure(target_index, result)

    def get_epsilon_closure(self, StateIdx):
        """Return all states that can be reached from 'StateIdx' via epsilon
           transition."""
        assert self.states.has_key(StateIdx)

        result = { StateIdx: True } 

        self.__dive_for_epsilon_closure(StateIdx, result)

        return result.keys()
 
    def get_elementary_trigger_sets(self, StateIdxList, epsilon_closure_db):
        """NOTE: 'epsilon_closure_db' must previously be calculcated by 
                 self.get_epsilon_closure_db(). This has to happen once
                 and for all in order to save computation time.
        
           Considers the trigger dictionary that contains a mapping from target state index 
           to the trigger set that triggers to it: 
     
                   target_state_index   --->   trigger_set 
    
           The trigger sets of different target state indices may intersect. As a result,
           this function produces a list of pairs:
    
                  [ state_index_list, elementary_trigger_set ]
    
           where the elementary trigger set is the set of all triggers that trigger
           at the same time to all states in the state_index_list. The list contains 
           for one state_index_list only one elementary_trigger_set. All elementary
           trigger sets are disjunct, i.e. they do not intersect.
    
          NOTE: A general solution of this problem would have to consider the 
                inspection of all possible subset combinations. The number of 
                combinations for N trigger sets is 2^N - which potentially blows
                the calculation power of the computer. Excessive optimizations
                would have to be programmed, if not the following were the case: 
    
          NOTE: Fortunately, we are dealing with one dimensional sets! Thus, there is
                a very effective way to determine the elementary trigger sets. Imagine
                three trigger sets stretching over the range of numbers as follows:

          different targets, e.g. T0, T1, T2 are triggered by different sets of letters
          in the alphabet. 
                                                                    letters of alphabet
                      ---------------------------------------------------->

                  T0  [---------)       [----------)
                  T1          [------)      [-----)
                  T2              [----------------------)    
    
          => elementary sets: 
     
             only T0  [-------)
             T0, T1           [-)
             only T1            [-)
             T1, T2               [--)
             only T2                 [---)          [----)
             T0, T2                      [---)     [)
             T0, T1, T2                      [-----)
        """
        # For Documentation Purposes: The following approach has been proven to be SLOWER
        #                             then the one currently implemented. May be, some time
        #                             it can be tweaked to be faster.
        #
        #                             Also, it is not proven to be correct! 
        #
        ## combination_list = []
        ## for state_index in StateIdxList:
        ##     state = self.states[state_index]
        ##     for target_index, trigger_set in state.transitions().get_map().iteritems():
        ##         target_epsilon_closure = epsilon_closure_db[target_index] 
        ##         # Delay the 'deepcopy' of the trigger set to the point, when it is actually needed
        ##         remaining_trigger_set  = None
        ##         for target_state_set, existing_trigger_set in combination_list:
        ##             if not existing_trigger_set.has_intersection(trigger_set): continue
        ##             target_state_set.update(target_epsilon_closure)
        ##             # We want to subtract from the set, so now, the remaining_trigger_set must be present
        ##             if remaining_trigger_set == None:
        ##                 remaining_trigger_set = trigger_set.difference(existing_trigger_set)
        ##             else:
        ##                 remaining_trigger_set.subtract(existing_trigger_set)
        ##         
        ##         if remaining_trigger_set == None:
        ##             combination_list.append([set(target_epsilon_closure), trigger_set])
        ##             
        ##         elif not remaining_trigger_set.is_empty():
        ##             combination_list.append([set(target_epsilon_closure), remaining_trigger_set])
        ##             
        ## return combination_list


        #def DEBUG_print_history(history):
        #    txt = ""
        #    for item in history:
        #        txt += repr(item) + "\n"
        #    print txt

        # (*) accumulate the transitions for all states in the state list.
        #     transitions to the same target state are combined by union.
        history = []
        for state_idx in StateIdxList:
            # -- trigger dictionary:  target_idx --> trigger set that triggers to target
            line_up = self.states[state_idx].transitions().get_trigger_set_line_up() 
            # NOTE: Duplicate entries in history are perfectly reasonable at this point,
            #       simply if two states trigger on the same character range to the same 
            #       target state. When ranges are opened/closed via the history items
            #       this algo keeps track of duplicates (see below).
            history.extend(line_up)

        # (*) sort history according to position
        history.sort(key = attrgetter("position")) # lambda a, b: cmp(a.position, b.position))
        ## DEBUG_print_history(history)

        # (*) build the elementary subset list 
        combinations = {}                             # use dictionary for uniqueness
        current_interval_begin = None
        current_target_indices = {}          # use dictionary for uniqueness
        current_target_epsilon_closure = []
        for item in history:
            # -- add interval and target indice combination to the data
            #    (only build interval when current begin is there, 
            #     when the interval size is not zero, and
            #     when the epsilon closure of target states is not empty)                   
            if current_interval_begin != None and \
               current_interval_begin != item.position and \
               current_target_indices.keys() != []:

                interval = Interval(current_interval_begin, item.position)

                current_target_epsilon_closure.sort()             
                key_str  = repr(current_target_epsilon_closure)
                combination = combinations.get(key_str)
                if combination == None:
                    combinations[key_str] = (current_target_epsilon_closure, \
                                             NumberSet(interval, ArgumentIsYoursF=True))
                else:
                    combination[1].unite_with(interval)
           
            # -- BEGIN / END of interval:
            #    add or delete a target state to the set of currently considered target states
            #    NOTE: More than one state can trigger on the same range to the same target state.
            #          Thus, one needs to keep track of the 'opened' target states.
            if item.change == INTERVAL_BEGIN:
                if current_target_indices.has_key(item.target_idx):
                    current_target_indices[item.target_idx] += 1
                else:
                    current_target_indices[item.target_idx] = 1
            else:        # == INTERVAL_END
                if current_target_indices[item.target_idx] > 1:
                    current_target_indices[item.target_idx] -= 1
                else:    
                    del current_target_indices[item.target_idx] 
    
            # -- re-compute the epsilon closure of the target states
            current_target_epsilon_closure = \
                self.get_epsilon_closure_of_state_set(current_target_indices.keys(),
                                                      epsilon_closure_db)
            # -- set the begin of interval to come
            current_interval_begin = item.position                      
    
        # (*) create the list of pairs [target-index-combination, trigger_set] 
        return combinations.values()

    def get_acceptance_state_list(self, 
                                  ReturnNonAcceptanceTooF=False, 
                                  SplitAcceptanceStatesByOriginF=False,
                                  CorePatternF=False):
        """Returns the set of states that are 'acceptance'. If the optional     
           argument 'ReturnNonAcceptanceTooF' is specified, then the non-
           acceptance states are also returned.

           If 'SplitAcceptanceStatesByOriginF'=True, then the list of acceptance
           states is split into sets of states of the same origin. The last state
           set is then the set of non-acceptance states (if requested).

           If 'CorePatternF'=True then the 'end acceptance states' of post conditions
           are not returned (acceptance + post condition flag). Instead the core
           patterns acceptance states are returned (post condition flag only).
        """   
        return filter(lambda s: s.is_acceptance(), self.states.values())

    def get_acceptance_state_index_list(self):
        result = []
        for index, state in self.states.items():
            if state.is_acceptance(): result.append(index)
        return result

    def get_inverse(self, CutAtShortestAcceptanceF=False):
        """Creates an inverse representation of the state machine. Optionally,
           the longer acceptance paths can be cut, in case that there are shorter
           once. This is the contrary of a 'greedy' wildcard, i.e.
                
                ("hello"|"h") would be equivalent to "h" this is by pure
                logic an redundant construct, since "h" causes acceptance", except
                one goes for 'longest match'
        
           Also "h"*|"h" : HERE cut at first match because it ends after "h"    
        """
        #__________________________________________________________________________________________
        # TODO: See th above comment and think about it.
        assert     self.__core.pre_context_sm() == None \
               and not self.core().pre_context_begin_of_line_f(), \
               "pre-conditioned state machines cannot be inverted via 'get_inverse()'"

        #__________________________________________________________________________________________
        result = StateMachine(InitStateIndex=self.init_state_index)
           
        # Ensure that each target state index has a state inside the state machine
        for state_index in self.states.keys():
            result.create_new_state(StateIdx=state_index)

        for state_index, state in self.states.items():
            for target_state_index, trigger_set in state.transitions().get_map().items():
                result.states[target_state_index].add_transition(deepcopy(trigger_set), state_index)

            for target_state_index in state.transitions().get_epsilon_target_state_index_list():
                result.states[target_state_index].transitions().add_epsilon_target_state(state_index)

        # -- copy all origins of the original state machine
        for state_index, state in self.states.items():
            original_origin_list = state.origins().get_list()
            result.states[state_index].origins().set(original_origin_list) # deepcopy implicit

        # -- only the initial state becomes an acceptance state
        result.states[self.init_state_index].set_acceptance(True)

        # -- setup an epsilon transition from an new init state to all previous 
        #    acceptance states.
        new_init_state_index = result.create_new_init_state() 
        for state_index in self.get_acceptance_state_index_list():
            result.add_epsilon_transition(new_init_state_index, state_index)        

        # -- for uniqueness of state ids, clone the result
        return result.clone()    
        
    def does_sequence_match(self, UserSequence):
        """Returns: True, if the sequences ends in an acceptance state.
                    False, if not.

           Works for NFA and DFA.
        """
        assert type(UserSequence) == list

        def dive(StateIndex, Sequence):
            if len(Sequence) == 0:
                return self.states[StateIndex].is_acceptance()

            idx_list = self.states[StateIndex].transitions().get_resulting_target_state_index_list(Sequence[0])
            for candidate in idx_list:
                # One follow-up state could match the sequence
                if dive(candidate, Sequence[1:]): return True
            # No possible follow-up state could match the sequence
            return False

        # Walk with the sequence the state machine
        return dive(self.init_state_index, UserSequence)

    def get_ending_character_set(self):
        """Returns the union of all characters that trigger to an acceptance
           state in the given state machine. This is to detect whether the
           newline or suppressor end with an indentation character (grid or space).
        """
        result = NumberSet()
        for end_state_index in self.get_acceptance_state_index_list():
            for state in self.states.values():
                if state.transitions().has_target(end_state_index) == False: continue
                result.unite_with(state.transitions().get_trigger_set_to_target(end_state_index))
        return result

    def get_only_entry_to_state(self, TargetStateIndex):
        """Checks if the given state has only one entry from another state 
           and if so it returns the state index. Otherwise, it returns None.
        """
        result = None
        for state_index, state in self.states.items():
            if state.transitions().has_target(TargetStateIndex):
                if result == None: result = state_index
                else:              return None           # More than one state trigger to target
        return result

    def is_empty(self):
        """If state machine only contains the initial state that points nowhere,
           then it is empty.
        """
        if len(self.states) != 1: return False
        return self.states[self.init_state_index].transitions().is_empty()

    def check_uniformity(self, StateIndexList):
        """Checks whether all states in the state index list have the same 
           state attributes.
        """
        assert len(StateIndexList) != 0
        prototype = self.states.get(StateIndexList[0])
        assert prototype != None
        for state_index in StateIndexList[1:]:
            state = self.states.get(state_index)
            assert state != None
            if not prototype.is_equivalent(state):
                return False
        return True

    def has_origins(self):
        for state in self.states.values():
            if not state.origins().is_empty(): return True
        return False

    def is_DFA_compliant(self):
        for state in self.states.values():
            if state.transitions().is_DFA_compliant() == False: 
                return False
        return True

    def delete_meaningless_origins(self):
        """Delete origins that do not inform about acceptance, store input position,
           post context, pre context, and the like.
        """
        for state in self.states.values():
            state.origins().delete_meaningless()

    def mark_state_origins(self, OtherStateMachineID=-1L):
        """Marks at each state that it originates from this state machine. This is
           important, when multiple patterns are combined into a single DFA and
           origins need to be traced down. In this case, each pattern (which is
           are all state machines) needs to mark the states with the state machine 
           identifier and the state inside this state machine.

           If OtherStateMachineID and StateIdx are specified other origins
              than the current state machine can be defined (useful for pre- and post-
              conditions).         

           DontMarkIfOriginsPresentF can be set to ensure that origin data structures
              are only provided for states where non is set yet. This can be unsed
              to ensure that every state has an origin structure related to it, without
              overiding existing ones.
        """
        assert type(OtherStateMachineID) == long

        if OtherStateMachineID == -1L: state_machine_id = self.__core.id()
        else:                          state_machine_id = OtherStateMachineID

        for state_idx, state in self.states.items():
            state.mark_self_as_origin(state_machine_id, state_idx)

    def create_new_init_state(self, AcceptanceF=False):

        self.init_state_index = self.create_new_state()
        return self.init_state_index

    def create_new_state(self, AcceptanceF=False, StateIdx=None):
        if StateIdx == None:
            new_state_index = state_machine_index.get()
        else:
            new_state_index = StateIdx

        self.states[new_state_index] = State(AcceptanceF)
        return new_state_index
        
    def add_transition(self, StartStateIdx, TriggerSet, TargetStateIdx = None, AcceptanceF = False):
        """Adds a transition from Start to Target based on a given Trigger.

           TriggerSet can be of different types: ... see add_transition()
           
           (see comment on 'State::add_transition)

           RETURNS: The target state index.
        """
        assert type(StartStateIdx) == long
        # NOTE: The Transition Constructor is very tolerant, so no tests on TriggerSet()
        #       assert TriggerSet.__class__.__name__ == "NumberSet"
        assert type(TargetStateIdx) == long or TargetStateIdx == None
        assert type(AcceptanceF) == bool

        # If target state is undefined (None) then a new one has to be created
        if TargetStateIdx == None:                       TargetStateIdx = state_machine_index.get()
        if self.states.has_key(StartStateIdx) == False:  self.states[StartStateIdx]  = State()        
        if self.states.has_key(TargetStateIdx) == False: self.states[TargetStateIdx] = State()
        if AcceptanceF:                                  self.states[TargetStateIdx].set_acceptance(True)

        self.states[StartStateIdx].add_transition(TriggerSet, TargetStateIdx)

        return TargetStateIdx
            
    def add_epsilon_transition(self, StartStateIdx, TargetStateIdx=None, RaiseAcceptanceF=False):
        assert TargetStateIdx == None or type(TargetStateIdx) == long

        # create new state if index does not exist
        if not self.states.has_key(StartStateIdx):
            self.states[StartStateIdx] = State()
        if TargetStateIdx == None:
            TargetStateIdx = self.create_new_state(AcceptanceF=RaiseAcceptanceF)
        elif not self.states.has_key(TargetStateIdx):
            self.states[TargetStateIdx] = State()

        # add the epsilon target state
        self.states[StartStateIdx].transitions().add_epsilon_target_state(TargetStateIdx)     
        # optionally raise the state of the target to 'acceptance'
        if RaiseAcceptanceF: self.states[TargetStateIdx].set_acceptance(True)

        return TargetStateIdx

    def mount_to_acceptance_states(self, MountedStateIdx, 
                                   CancelStartAcceptanceStateF=True,
                                   RaiseTargetAcceptanceStateF=False,
                                   LeaveStoreInputPositionsF=False):
        """Mount on any acceptance state the MountedStateIdx via epsilon transition.
        """
        for state_idx, state in self.states.items():
            # -- only consider state other than the state to be mounted
            # -- only handle only acceptance states
            if state_idx == MountedStateIdx: continue
            if not state.is_acceptance():    continue
            # add the MountedStateIdx to the list of epsilon transition targets
            state.transitions().add_epsilon_target_state(MountedStateIdx)
            # if required (e.g. for sequentialization) cancel the acceptance status
            if CancelStartAcceptanceStateF: state.set_acceptance(False, LeaveStoreInputPositionsF)

        if RaiseTargetAcceptanceStateF: 
            self.states[MountedStateIdx].set_acceptance(True, LeaveStoreInputPositionsF)

    def mount_to_initial_state(self, TargetStateIdx):
        """Adds an epsilon transition from initial state to the given 'TargetStateIdx'. 
           The initial states epsilon transition to TERMINATE is deleted."""

        assert self.states.has_key(self.init_state_index)

        self.states[self.init_state_index].transitions().add_epsilon_target_state(TargetStateIdx)

    def filter_dominated_origins(self):
        for state in self.states.values(): 
            state.origins().delete_dominated()

    def replace_pre_context_state_machine(self, NewPreContextSM):
        OldPreContextID = self.core().pre_context_sm().get_id()
        NewPreContextID = NewPreContextSM.get_id()

        # Set the new pre-context state machine
        self.core().set_pre_context_sm(NewPreContextSM)

        # Adapt all origins that depend on the old pre-context to the new context
        for state in self.states.values():
            for origin in state.origins().get_list():
                if origin.pre_context_id() != OldPreContextID: continue
                origin.set_pre_context_id(NewPreContextID)

    def transform(self, TrafoInfo):
        """RETURNS: True  transformation successful
                    False transformation failed, number set possibly in inconsistent state!
        """
        for state in self.states.values():
            if state.transform(TrafoInfo) == False: return False

        if self.__core.pre_context_sm() != None:
            for state in self.__core.pre_context_sm().values():
                if state.transform(TrafoInfo) == False: return False

        return True

    def __repr__(self):
        return self.get_string(NormalizeF=True)

    def __get_state_sequence_for_print_out(self):
        state_index_sequence = [ self.init_state_index ]

        def __dive(state):
            target_state_index_list = state.transitions().get_target_state_index_list()

            # For linear state sequences we do not recurse,
            # this is more stable in the recursion restricted python world.
            while len(target_state_index_list) == 1:
                state_index = target_state_index_list[0]
                if state_index in state_index_sequence: break
                state_index_sequence.append(state_index)
                state = self.states[state_index]
                target_state_index_list = state.transitions().get_target_state_index_list()

            # sort by 'lowest trigger'
            def cmp_by_trigger_set(A, B):
                # In case of epsilon transitions, the 'other' dominates.
                try:    trigger_set_to_A = state.transitions().get_map()[A]
                except: return -1
                try:    trigger_set_to_B = state.transitions().get_map()[B]
                except: return 1
                return cmp(trigger_set_to_A.minimum(), trigger_set_to_B.minimum())
            target_state_index_list.sort(cmp_by_trigger_set)
                                         
            for state_index in target_state_index_list:
                if state_index in state_index_sequence: continue
                state_index_sequence.append(state_index)
                __dive(self.states[state_index])

        __dive(self.states[self.init_state_index])

        # There might be 'sick' cases where there are not all states connected.
        if len(self.states.keys()) != len(state_index_sequence):
            state_index_sequence = self.states.keys()

        # DEBUG: double check that the sequence is complete
        x = self.states.keys(); x.sort()               # DEBUG
        y = deepcopy(state_index_sequence); y.sort()   # DEBUG
        assert x == y                                  # DEBUG

        return state_index_sequence

    def __get_state_index_normalization(self, NormalizeF):
        index_map         = {}
        inverse_index_map = {}

        index_sequence = self.__get_state_sequence_for_print_out()
        if NormalizeF:
            counter = -1L
            for state_i in index_sequence:
                counter += 1L
                index_map[state_i]         = counter
                inverse_index_map[counter] = state_i
        else:
            for state_i in index_sequence:
                index_map[state_i]         = state_i
                inverse_index_map[state_i] = state_i

        return index_map, inverse_index_map, index_sequence

    def get_string(self, NormalizeF=False, Option="utf8"):
        """Option is "utf8", or "hex"
        """

        # (*) normalize the state indices
        index_map, inverse_index_map, index_sequence = self.__get_state_index_normalization(NormalizeF)

        # (*) construct text 
        msg = "init-state = " + repr(index_map[self.init_state_index]) + "\n"
        for state_i in index_sequence:
            printed_state_i = index_map[state_i]
            state           = self.states[state_i]
            msg += "%05i" % printed_state_i + state.get_string(index_map, Option)
            
        if self.__core.pre_context_sm() != None:
            msg += "pre-condition inverted = "
            msg += repr(self.core().pre_context_sm())           

        return msg

    def get_graphviz_string(self, NormalizeF=False, Option="utf8"):
        assert Option in ["hex", "utf8"]

        # (*) normalize the state indices
        index_map, inverse_index_map, index_sequence = self.__get_state_index_normalization(NormalizeF)

        # (*) Border of plot block
        frame_txt = """
        digraph state_machine_%i {
	       rankdir=LR;
	       size="8,5"
	       node [shape = doublecircle]; $$ACCEPTANCE_STATES$$
           node [shape = circle];
           $$TRANSITIONS$$
        }
        """ % self.get_id()

        transition_str       = ""
        acceptance_state_str = ""
        for state_i in index_sequence:
            printed_state_i = index_map[state_i]
            state           = self.states[state_i]
            if state.is_acceptance(): 
                acceptance_state_str += "%i; " % int(printed_state_i)
            transition_str += state.get_graphviz_string(printed_state_i, index_map, Option)

        if acceptance_state_str != "": acceptance_state_str = acceptance_state_str[:-2] + ";"
        return blue_print(frame_txt, [["$$ACCEPTANCE_STATES$$", acceptance_state_str ],
                                      ["$$TRANSITIONS$$",       transition_str]])
        
    def assert_consistency(self):
        """Check: -- whether each target state in contained inside the state machine.
        """
        target_state_index_list = self.states.keys()
        for index, state in self.states.items():
            for target_state_index in state.transitions().get_target_state_index_list():
                assert target_state_index in target_state_index_list, \
                       "state machine contains target state %s that is not contained in itself." \
                       % repr(target_state_index) + "\n" \
                       "present state indices: " + repr(self.states.keys()) + "\n" + \
                       "state machine = " + self.get_string(NormalizeF=False)

