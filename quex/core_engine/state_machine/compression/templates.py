# (C) 2010 Frank-Rene Schaefer
"""
   Template Compression _______________________________________________________

   The idea behind 'template compression' is to combine the transition maps of
   multiple similar states into a single transition map. The difference in the
   transition maps are dealt with by an adaption table. For example the three
   states

         .---- 'a' --> 2        .---- 'a' --> 2        .---- 'a' --> 2
         |                      |                      |
       ( A )-- 'e' --> 0      ( B )-- 'e' --> 1      ( C )-- 'e' --> 2
         |                      |                      |
         `---- 'x' --> 5        `---- 'x' --> 5        `---- 'y' --> 5

   can be combined into a single template state

                         .----- 'a' --> 2 
                         |               
                      ( T1 )--- 'e' --> Target0 
                         |\               
                         \  `-- 'x' --> Target1
                          \
                           `--- 'y' --> Target2

   where the targets Target0, Target1, and Target2 are adapted. If the template
   has to mimik state A then Target0 needs to be 1, Target1 is 5, and Target2
   is 'drop-out'. The adaptions can be stored in a table:

                                A     B     C
                       Target0  0     1     2
                       Target1  5     5     drop
                       Target2  drop  drop  5

   Practically, this means that a 'goto state' is transformed into a 'set state
   key' plus a 'goto template'. The state key tells which column of the table
   is to be used in the transition map. Thus, a state that is implemented in a
   template is identified by 'template index' and 'state key', i.e.

            templated state <--> (template index, state key)

   The combination of multiple states reduces memory consumption. The
   efficiency increases with the similarity of the transition maps involved.
   The less differences there are in the trigger intervals, the less additional
   intervals need to be added. The less differences there are in target states,
   the less information needs to be stored in adaption tables.

   Result ______________________________________________________________________


   The result of analyzis of template state compression is:
    
              A list of 'TemplateCombination' objects. 

   A TemplateCombination carries:
   
     -- a trigger map, i.e. a list of intervals together with target state
        lists to which they trigger. If there is only one associated target
        state, this means that all involved states trigger to the same target
        state.

     -- a list of involved states. A state at position 'i' in the list has
        the state key 'i'. It is the key into the adaption table mentioned
        above.

   Algorithm __________________________________________________________________

   Not necessarily all states can be combined efficiently with each other. The
   following algorithm finds successively best combinations and stops when no
   further useful combinations can be found. 

   Each state has a transition map, i.e. an object that tells on what character
   code intervals the analyzer jumpt to what states:

             transition map:  interval  --> target state

   The algorithm works as follows:

      (1) Compute for each combination candidate of two states the 
          expected 'gain' if they were combined. This happens by 
          comparison of the transition maps.

      (2.a) Do not consider to combine states where the 'gain' is negative.

      (2.b) Take the pair of states that provide the highest gain.
            
            Create a TemplateCombination object based on the two states.

            Enter the TemplateCombination as a normal 'state' into the database.

            Goto (1)

   Measurement of the 'Gain Value' ____________________________________________

   The 'gain' shall **represent** the amount of memory that can be spared if
   two trigger maps are combined. The number does not necessarily relate
   directly to a physical byte consumption. It is only required, that
   if a combination of (A, B) spares more than a combination of (C, D) then
   the gain value of (A, B) must be greater than the gain value for (C, D).

   The measurement of 'gain' is done in two steps:

       (1) get_metric(A, B): computes the number of borders of a
           transition map that would combine the two trigger
           maps A and B. Also, it combines the number of target
           set combinations, i.e. the number of X0, X1, X3 ...
           in the example above.

       (2) compute_combination_gain(...): computes a scalar value that indicates
           the 'gain' in terms of program space, if the two trigger
           maps are combined. This function is controlled by the
           coefficient 'CX' that indicates the ratio between the
           'normal cost' of transition and the cost of routing, i.e.
           entering the right target state according to the adapted
           trigger map.

   both functions work with normal state trigger maps and objects of class
   TemplateCombination.

   Class TemplateCombination __________________________________________________

   Combined trigger maps are stored in objects of type 'TemplateCombination'.
   As normal trigger maps they are built of a list of tuples:

              (I0, TL0),       # meaning interval I0 triggers to TL0
              (I1, TL1),       #                  I1 triggers to TL1
              .... 
              (In, TLn)        #                  In triggers to TLn

   where the intervals I0 to In are adjacent intervals starting with 

              I0.begin == - sys.maxint

   and ending with 

              In.end   == sys.maxint

   In 'normal trigger maps' the target state indices TL0 to TLn are scalar
   values. In a 'TemplateCombination' object, the 'target' can be a scalar
   value or a list. Accordingly, this means that TLk is

        a scalar, if Ik maps to the same target state for all involved 
                  states.

                  If TLk == TARGET_RECURSIVE, then all involved states
                  trigger recursively.

        a list, if Ik maps to different target states for each involved
                state. Then, Tlk[i] is the target state to which the 
                state with key 'i' triggers.  

   The state key has been mentioned above. It designates the column in the
   adaption table that is required for each state involved.

"""
import sys
from   copy import copy
from   quex.core_engine.interval_handling import Interval
import quex.core_engine.state_machine.index as index
import quex.core_engine.state_machine.core  as state_machine
from   operator import itemgetter

def do(sm, CostCoefficient):
    """
       sm:              StateMachine object containing all states

                        NOTE: The init state is **never** part of a template 
                              combination.

       CostCoefficient: Coefficient that indicates how 'costy' it is differentiate
                        between target states when it is different in states that
                        are combined into a template. Meaningful range: 0 to 3.

       RETURNS: List of template combinations.
    """
    assert isinstance(sm, state_machine.StateMachine)
    assert isinstance(CostCoefficient, (int, long, float))

    trigger_map_db = TriggerMapDB(sm, CostCoefficient)

    # Build templated combinations by finding best pairs, until there is no meaningful way to
    # build any clusters. TemplateCombinations of states also take part in the race.
    while 1 + 1 == 2:
        i, i_trigger_map_db, k, k_trigger_map_db = trigger_map_db.pop_best_matching_pair()
        if i == None: break

        # Add new element: The combined pair
        new_index = index.get()
        trigger_map_db[new_index] = get_combined_trigger_map(i_trigger_map_db, 
                                                             involved_state_list(i_trigger_map_db, i),
                                                             k_trigger_map_db, 
                                                             involved_state_list(k_trigger_map_db, k))

    result = []
    for state_index, combination in trigger_map_db.items():
        if isinstance(combination, TemplateCombination): result.append(combination)

    return result

TARGET_RECURSIVE  = -2L    # 'Normal' targets are greater than zero

class TemplateCombination:
    def __init__(self, InvolvedStateList0,  InvolvedStateList1):
        self.__trigger_map         = []
        self.__involved_state_list = InvolvedStateList0 + InvolvedStateList1

    def involved_state_list(self):
        return self.__involved_state_list

    def append(self, Begin, End, TargetStateIdxList):
        """TargetStateIdxList can be
        
            A list of (long) integers: List of targets where

                list[i] == target index of involved state number 'i'

            A scalar value:

                i)  > 0, then all involved states trigger to this same
                         target index.
                ii) == TARGET_RECURSIVE, then all involved states are 
                                         recursive.
        """
        self.__trigger_map.append([Interval(Begin, End), TargetStateIdxList])

    def __getitem__(self, Index):
        return self.__trigger_map[Index]

    def __len__(self):
        return len(self.__trigger_map)

    def __repr__(self):
        txt = []
        for trigger in self.__trigger_map:
            txt.append("[%i, %i) --> %s\n" % \
                       (trigger[0].begin, trigger[0].end, trigger[1]))
        return "".join(txt)

    def get_trigger_map(self):
        return self.__trigger_map

def compute_combination_gain(SizeA, SizeB, N, CombinedBorderN, TargetCombinationN, CX=1):
    """SizeA, SizeB       = number of borders in target map A and B
       N                  = total number of combined states.
       CombinedBorderN    = number of borders in the combined map.
       TargetCombinationN = number of different target state combinations.

       CX = the calculation coefficient as explained below:
    
    
       BEFORE: 
                Cost0 = (SizeA + SizeB) * CI

                where CI is the average 'identification cost', i.e. the
                cost for branching through the 'if/else' statements of 
                the transition map, plus the cost for a goto.

       AFTER:
                Cost1 =   SameTargetN * CI
                        + TargetCombinationN * N * CR

                where SameTargetN = CombinedBorderN - TargetCombinationN
                                    the number of intervals that trigger to
                                    the same target in both maps.
                      CR is the cost for routing, i.e. jumping to
                         the correct target state depending on template.
                      N the number of involved states must be multiplied because
                        for each state there must be a 'switch case'.

       THUS:    
                Delta = Cost0 - Cost1

                      = (SizeA + SizeB - (CombinedBorderN - TargetCombinationN)) * CI
                         - TargetCombinationN * N * CR

                Delta shall be a 'measure', so there is no loss of 
                information if we devide by a constant, e.g. CI. Thus

                .-------------------------------------------------------------------.
                | Delta =   (SizeA + SizeB - CombinedBorderN + TargetCombinationN)  |
                |         - CX * TargetCombinationN * N                             |
                '-------------------------------------------------------------------'

                Where CX = CR/CI. A big CX means that target state routing is
                expensive, a low CX means, that it is cheap. The constants CI
                and CR where used to express an estimated proportional
                relationship without having a concrete 'physical'
                interpretation.  Now, CI and CR can be replaced by a single
                heuristic value CX.

    """
    return (SizeA + SizeB - CombinedBorderN + TargetCombinationN) - CX * TargetCombinationN * N

class TriggerMapDB:
    def __init__(self, SM, CostCoefficient):
        assert isinstance(SM, state_machine.StateMachine)

        # (1) Get the trigger maps of all states of the state machine
        self.__db = {}
        for state_index, state in SM.states.items():
            trigger_map = state.transitions().get_trigger_map()
            # Dead ends, cannot be part of the code generation
            if trigger_map == []: continue
            self.__db[state_index] = trigger_map

        self.__cost_coefficient = float(CostCoefficient)

        self.__init_state_index = SM.init_state_index

        self.__combination_gain_list = self.__initial_combination_gain()

    def __initial_combination_gain(self):
        item_list  = self.__db.items()
        L          = len(item_list)

        # Pre-allocate the result array to avoid frequent allocations
        #
        # NOTE: L * (L - 1) is always even, i.e. dividable by 2.
        #       (a) L even = k * 2:     -> k * 2 ( k * 2 - 1 )            = k * k * 4 - k * 2
        #                                = even - even = even
        #       (b) L odd  = k * 2 + 1: -> (k * 2 + 1) * ( k * 2 + 1 - 1) = k * k * 4 + k * 2
        #                                = even + even = even
        #       => division by two without remainder 
        MaxSize = (L * (L - 1)) / 2
        result  = [None] * MaxSize
        n       = 0
        for i, info in enumerate(item_list):
            a_state_index, a_trigger_map = info
            if a_state_index == self.__init_state_index: continue

            for b_state_index, b_trigger_map in item_list[i+1:]:
                if b_state_index == self.__init_state_index: continue

                combination_gain = self.__get_combination_gain(a_state_index, a_trigger_map, [a_state_index],
                                                               b_state_index, b_trigger_map, [b_state_index])
                if combination_gain > 0:
                    result[n] = (combination_gain, a_state_index, b_state_index)
                    n += 1

        if n != MaxSize:
            del result[n:]

        # Sort according to delta cost
        result.sort(key=itemgetter(0))
        return result

    def __adapt_combination_gain(self, NewStateIndex, NewTriggerMap):
        """Adapt the delta cost list **before** adding the trigger map to __db!"""
        assert isinstance(NewTriggerMap, TemplateCombination)

        InvolvedStateListB = involved_state_list(NewTriggerMap, NewStateIndex)

        # Avoid extensive 'appends' by single allocation (see initial computation)
        MaxIncrease = (len(self.__db) - 1)
        n           = len(self.__combination_gain_list)
        MaxSize     = len(self.__combination_gain_list) + MaxIncrease
        self.__combination_gain_list.extend([None] * MaxIncrease)

        for state_index, trigger_map in self.__db.items():
            if state_index == self.__init_state_index: continue

            InvolvedStateListA = involved_state_list(trigger_map, state_index)
            combination_gain = self.__get_combination_gain(state_index,   trigger_map,   InvolvedStateListA,
                                                           NewStateIndex, NewTriggerMap, InvolvedStateListB)
            if combination_gain > 0:
                self.__combination_gain_list[n] = (combination_gain, state_index, NewStateIndex)
                n += 1

        if n != MaxSize:
            del self.__combination_gain_list[n:]

        self.__combination_gain_list.sort(key=itemgetter(0))

    def __get_combination_gain(self, 
                               StateIndexA, TriggerMapA, InvolvedStateListA, 
                               StateIndexB, TriggerMapB, InvolvedStateListB):

        # Get border_n    = number of borders of combined map
        #     eq_target_n = number of equivalent targets, i.e. number of 
        #                   target combinations that need to be routed.
        border_n, eq_target_list = get_metric(TriggerMapA, InvolvedStateListA, 
                                              TriggerMapB, InvolvedStateListB)
        eq_target_n      = len(eq_target_list)
        combined_state_n = len(InvolvedStateListA) + len(InvolvedStateListB)

        return compute_combination_gain(len(TriggerMapA), len(TriggerMapB), 
                                        combined_state_n, border_n, eq_target_n, 
                                        CX=self.__cost_coefficient)

    def pop_best_matching_pair(self):
        """Determines the two trigger maps that are closest to each
           other. The consideration includes the trigger maps of
           combined trigger maps. Thus this function supports the
           clustering of the best trigger maps into combined trigger
           maps.

           If no pair can be found with a gain > 0, then this function
           returns 'None, None'.
        """
        if len(self.__combination_gain_list) == 0: return (None, None, None, None)

        # (0) The entry with the highest gain is at the tail of the list.
        #     Element 0 contains the combination gain.
        #     Element 1 and 2 contain the state indices of the states to be combined
        info = self.__combination_gain_list.pop()
        i    = info[1]          # State Index A
        i_tm = self.__db[i]     # Trigger map of State A
        k    = info[2]          # State Index B
        k_tm = self.__db[k]     # Trigger map of State B

        # (1) Delete both states from the database: state-index  --> trigger_map
        del self.__db[i]
        del self.__db[k]

        # (2) Delete all entries from the 'combination gain' list that relate
        #     to the states 'i' and 'k'. They are no longer available.
        X = (i, k)
        L = len(self.__combination_gain_list)
        p = 0
        while p < L:
            entry = self.__combination_gain_list[p]
            # Does entry contain 'i' or 'k'? If so the subsequent entries are 
            # likely to contain them two. Combine the 'del' for the chunk of
            # adjacent entries.
            if entry[1] in X or entry[2] in X:
                # Determine the end of the region to be deleted
                q = p + 1
                while q < L:
                    entry = self.__combination_gain_list[q]
                    if entry[1] not in X and entry[2] not in X: break
                    q += 1
                del self.__combination_gain_list[p:q]
                L -= (q - p)
            else:
                p += 1

        return i, i_tm, k, k_tm

    def __len__(self):
        return len(self.__db)

    def __getitem__(self, Key):
        assert type(Key) == long
        return self.__db[Key]

    def __setitem__(self, Key, Value):
        assert type(Key) == long
        assert isinstance(Value, TemplateCombination)
        self.__adapt_combination_gain(Key, Value)
        self.__db[Key] = Value

    def items(self):
        return self.__db.items()

def involved_state_list(TM, DefaultIfTriggerMapIsNotACombination):
    if isinstance(TM, TemplateCombination):
        return TM.involved_state_list()
    else:
        return [ DefaultIfTriggerMapIsNotACombination ]

def get_metric(TriggerMap0, InvolvedStateList0, TriggerMap1, InvolvedStateList1):
    """Assume that interval list 0 and 1 are sorted.
       
       RETURNS: -- Number of new borders if both maps are combined.
                -- Number of transitions that trigger to the same 
                   target state on the same interval in both maps.

       The result of this function is later used to feed 'combination_gain' that
       estimates the 'gain' of combining the two maps. 

       If both trigger maps trigger to itself, then this counted as a 
       'same target' since there is no change needed and the template
       triggers to itself.
    """
    # Count the number of additional intervals if list 0 is combined with list 1
    # Each intersection requires the setup of new intervals, e.g.
    #
    #          |----------------|
    #               |---------------|
    #
    # Requires to setup three intervals in order to cover all cases propperly: 
    #
    #          |----|-----------|---|
    #
    assert TriggerMap0[0][0].begin == -sys.maxint
    assert TriggerMap1[0][0].begin == -sys.maxint
    assert TriggerMap0[-1][0].end  == sys.maxint
    assert TriggerMap1[-1][0].end  == sys.maxint

    equivalent_target_list = []
    def __check_targets(T0, T1):
        """T0 and T1 are targets (being a single state or a 'state list') of two targets 
           that belong to the same interval. 

                    Interval --> T0   for trigger map 0
                    Interval --> T1   for trigger map 1

           Both can be either a scalar or a list. Let T be T0 or T1, then

             T == list    Means that the trigger map is a TemplateCombination. The
                          template needs to trigger on the given interval to T[i] 
                          if it represents state 'i'.

             T == scalar  Means that either:

                          -- the trigger map belong to a 'pure state' which triggers 
                             on an interval to a single target state. 
                          -- or, it may be a TemplateCombination where all related states
                             trigger on the given interval to the same target state.
        """
        # (0) Both trigger to the same target --> no adaption required
        if T0 == T1: return

        # (1) Recursion?
        # Both trigger to itself --> no adaption required.
        recursion_n = 0
        # IS RECURSIVE ?
        # -- In a 'normal trigger map' the target needs to be equal to the
        #   state that it contains.
        # -- In a trigger map combination, the recursive target is 
        #    identifier by the value 'TARGET_RECURSIVE'.
        if (len(InvolvedStateList0) == 1 and T0 == InvolvedStateList0[0]) or T0 == TARGET_RECURSIVE:
            T0 = InvolvedStateList0
            if len(T0) == 1: T0 = T0[0]
            recursion_n += 1
        if (len(InvolvedStateList1) == 1 and T1 == InvolvedStateList1[0]) or T1 == TARGET_RECURSIVE:
            T1 = InvolvedStateList1
            if len(T1) == 1: T1 = T1[0]
            recursion_n += 1
        if recursion_n == 2: return

        # (2) Add the combination to the list 
        #     (later we will determine the 'unique entries')
        # T = list   -> target state depends on template instantiation (T0[i] for state i)
        # T = scalar -> same target state for TargetCombinationN in all cases.
        if type(T0) == list: 
            if type(T1) == list: combination = T0 + T1
            else:                combination = T0 + [T1]
        else:
            if type(T1) == list: combination = [T0] + T1
            else:                combination = [T0, T1]

        if combination not in equivalent_target_list:
            equivalent_target_list.append(combination)

    def __check_pure_targets(T0, T1):
        """Simple '__check_targets' for pure states--without template combinations.
           ** CURRENTLY NOT USED **
        """
        if   T0 == T1: return
        elif T0 == PureStateIndex0 and T1 == PureStateIndex1: # Recursion on both
            return
        combination = (T0, T1)
        if combination not in equivalent_target_list:
            equivalent_target_list.append(combination)

    # if PureStateIndex0 != None and PureStateIndex1 != None: __check = __check_pure_targets
    # else: __check = __check_targets

    i = 0 # iterator over interval list 0
    k = 0 # iterator over interval list 1
    Li = len(TriggerMap0)
    Lk = len(TriggerMap1)
    # Intervals in trigger map are always adjacent, so the '.begin'
    # member is not required.
    border_count_n = 0
    while not (i == Li-1 and k == Lk-1):
        i_trigger = TriggerMap0[i]
        i_end     = i_trigger[0].end
        i_target  = i_trigger[1]

        k_trigger = TriggerMap1[k]
        k_end     = k_trigger[0].end
        k_target  = k_trigger[1]

        __check_targets(i_target, k_target)

        # Step to the next *lowest* border, i.e. increment the 
        # interval line index with the lowest '.end'. For example:
        # 
        #         0   1 2  3 4 5  6   7
        #     i   |     |      |  |   |
        #     k   |   |    | |        |
        #         :   : :  : : :  :   :   (6 intervals, 6 borders)
        #
        #                         i_end:     k_end:
        # Does:  (1) ++i, ++k -->    2            1
        #        (2) ++k      -->    2            3
        #        (3) ++i      -->    5            3
        #        (4) ++k      -->    5            4
        #        (5) ++k      -->    5            6
        #        (6) ++i      -->    6            7
        #        (6) ++i      -->    7            7
        if   i_end == k_end:  i += 1; k += 1;
        elif i_end < k_end:   i += 1;
        else:                 k += 1;

        border_count_n += 1

    # Treat the last trigger interval
    __check_targets(TriggerMap0[-1][1], TriggerMap1[-1][1])

    return border_count_n, equivalent_target_list

def get_combined_trigger_map(TriggerMap0, InvolvedStateList0, TriggerMap1, InvolvedStateList1):
    InvolvedStateN0 = len(InvolvedStateList0)
    InvolvedStateN1 = len(InvolvedStateList1)

    def __asserts(TM):
        """-- first border at - sys.maxint
           -- all intervals are adjacent (current begin == previous end)
           -- last border at  + sys.maxint
        """
        prev_end = -sys.maxint
        for x in TM:
            assert x[0].begin == prev_end
            prev_end = x[0].end
        assert TM[-1][0].end  == sys.maxint

    __asserts(TriggerMap0)
    __asserts(TriggerMap1)

    def __get_target(T0, T1):
        """In the 'TemplateCombination' trigger map, a transition to the same
           target for all involved states is coded as a scalar value.
           Other combined transitions are coded as list while 

                    list[i] = target index of involved state 'i'

           As soon as the single transition is over, the scalar value
           needs to be expanded, so that the above consensus holds.
        """
        recursion_n = 0
        # IS RECURSIVE ?
        # -- In a 'normal trigger map' the target needs to be equal to the
        #   state that it contains.
        # -- In a trigger map combination, the recursive target is 
        #    identifier by the value 'TARGET_RECURSIVE'.
        if (len(InvolvedStateList0) == 1 and T0 == InvolvedStateList0[0]) or T0 == TARGET_RECURSIVE:
            T0 = InvolvedStateList0
            if len(T0) == 1: T0 = T0[0]
            recursion_n += 1
        if (len(InvolvedStateList1) == 1 and T1 == InvolvedStateList1[0]) or T1 == TARGET_RECURSIVE:
            T1 = InvolvedStateList1
            if len(T1) == 1: T1 = T1[0]
            recursion_n += 1

        # If both transitions are recursive, then the template will
        # contain only a 'recursion flag'. 
        if recursion_n == 2: return TARGET_RECURSIVE

        # T = list   -> combination is a 'involved state list'.
        # T = scalar -> same target state for TargetCombinationN in all cases.
        if type(T0) == list:
            if type(T1) == list: return T0 + T1
            else:                return T0 + [T1] * InvolvedStateN1
        else:
            if type(T1) == list: return [T0] * InvolvedStateN0 + T1
            elif T0 != T1:       return [T0] * InvolvedStateN0 + [T1] * InvolvedStateN1
            else:                return T0                      # Same Target => Scalar Value

    i  = 0 # iterator over interval list 0
    k  = 0 # iterator over interval list 1
    Li = len(TriggerMap0)
    Lk = len(TriggerMap1)

    # Intervals in trigger map are always adjacent, so the '.begin'
    # member is not required.
    result = TemplateCombination(InvolvedStateList0, InvolvedStateList1)
    prev_end = - sys.maxint
    while not (i == Li-1 and k == Lk-1):
        i_trigger = TriggerMap0[i]
        i_end     = i_trigger[0].end
        i_target  = i_trigger[1]

        k_trigger = TriggerMap1[k]
        k_end     = k_trigger[0].end
        k_target  = k_trigger[1]

        target    = __get_target(i_target, k_target)
        end       = min(i_end, k_end)
        result.append(prev_end, min(i_end, k_end), target)
        prev_end  = end

        if   i_end == k_end:  i += 1; k += 1;
        elif i_end < k_end:   i += 1;
        else:                 k += 1;

    # Treat the last trigger interval
    target = __get_target(TriggerMap0[-1][1], TriggerMap1[-1][1])
    result.append(prev_end, sys.maxint, target)

    return result
