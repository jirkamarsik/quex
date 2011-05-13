# (C) 2010 Frank-Rene Schaefer
"""
   Path Compression ___________________________________________________________

   For path compression it is necessary to identify traits of single character
   transitions while the remaining transitions of the involved states are the
   same (or covered by what is triggered by the current path element). This
   type of compression is useful in languages that contain keywords. Consider
   for example a state machine, containing the key-word 'for':


   ( 0 )-- 'f' --->( 1 )-- 'o' --->( 2 )-- 'r' -------->(( 3 ))--( [a-z] )-.
      \               \               \                                    |
       \               \               \                                   |
        `--([a-eg-z])---`--([a-np-z])---`--([a-qs-z])-->(( 4 ))<-----------'


   The states 0, 1, and 2 can be implemented by a 'path walker', that is 
   a common transition map, that is preceeded by a single character check.
   The single character check changes along a fixed path: the sequence of
   characters 'f', 'o', 'r'. This is shown in the following pseudo-code:

     PATH_WALKER_1:
        /* Single Character Check */
        if   input == *p: ++p; goto PATH_WALKER_1;
        elif *p == 0:          goto STATE_3;

        /* Common Transition Map */
        if   x < 'a': drop out
        elif x > 'z': drop out
        else:         goto STATE_4

   It is assumed that the array with the character sequence ends with a 
   terminating charater (e.g. zero, but must be different from buffer limit code).
   This way it can be detected when to trigger to the correspondent end state.

   For a state that is part of a 'path', a 'goto state' is transformed into a
   'set path_iterator' plus a 'goto path'. The path iterator determines the
   current character to be checked. The 'path' determines the reminder of the
   transition map. It holds

            path state <--> (path index, path iterator position)

   Assume that in the above example the path is the 'PATH_WALKER_1' and the 
   character sequence is given by an array:

            path_1_sequence = { 'f', 'o', 'r', 0x0 };
            
    then the three states 0, 1, 2 are identified as follows

            STATE_0  <--> (PATH_WALKER_1, path_1_sequence)
            STATE_1  <--> (PATH_WALKER_1, path_1_sequence + 1)
            STATE_2  <--> (PATH_WALKER_1, path_1_sequence + 2)

   Result ______________________________________________________________________


   The result of analyzis of path compression is:
    
                       A dictionary mapping  
                  
            start state indices <--> 'CharacterPath' objects. 

   A character path represents a single character sequence that was found in
   the state machine, together with the 'skeleton' which is the remaining
   trigger map. Concrete:

         .sequence()        --> The character sequence of the path
         .end_state_index() --> State index of the state that is
                                entered after the path is terminated.
         .skeleton()        --> Remaining trigger map, that must be
                                applied after the single char check.

   There might be multiple pathes starting from the same start state. And,
   start states might possibly appear in other paths.

   Filtering Pathes ___________________________________________________________

   First, paths that are subsets of other paths might be filtered out without
   loss.

"""
from quex.core_engine.interval_handling import NumberSet, Interval
from copy                               import deepcopy, copy


def do(SM, UniformityF):
    path_list = find_paths(SM)

    __filter_redundant_paths(path_list)

    # A state can only appear in one path, so make sure that intersecting
    # paths are avoided. Always choose the longest alternative.
    __select_longest_intersecting_paths(path_list)

    # If uniformity is required, filter non-uniform paths. The last state 
    # of a path can be non-uniform with the rest, since it is 'outside'
    # the pathwalk implementation.
    if UniformityF:
        __filter_non_uniform_paths(SM, path_list)

    # The filtering of intersecting paths implies that there are no pathes
    # that have the same initial state. Thus, at this point we are done.
    # 
    #    -- no paths appear twice.
    #    -- no state appears in two paths.
    return path_list

def __filter_redundant_paths(path_list):
    """Due to the search algorithm, it is not safe to assume that there are
       no paths which are sub-pathes of others. Those pathes are identified.
       Pathes that are sub-pathes of others are deleted.

       Function modifies 'path_list'.
    """
    size = len(path_list)
    i    = 0
    while i < size: 
        i_path = path_list[i]
        # k = i, does not make sense; a path covers itself, so what!?
        k = i + 1
        while k < size: 
            k_path = path_list[k]

            if k_path.covers(i_path):
                # if 'i' is a subpath of something => delete, no further considerations
                del path_list[i]
                size -= 1
                # No change to 'i' since the elements are shifted
                break

            elif i_path.covers(k_path):
                del path_list[k]
                size -= 1
                # No break, 'i' is greater than 'k' so just continue analyzis.

            else:
                k += 1
        else:
            # If the loop is not left by break (element 'i' was deleted), then ...
            i += 1

    # Content of path_list is changed
    return

def __select_longest_intersecting_paths(path_list):
    """The desribed paths may have intersections, but a state can only
       appear in one single path. From each set of intersecting pathes 
       choose only the longest one.

       Function modifies 'path_list'.
    """
    # The intersection db maps: intersection state --> involved path indices
    intersection_db = {}
    for i, path_i in enumerate(path_list):
        k = i # is incremented to 'i+1' in the first iteration
        for path_k in path_list[i + 1:]:
            k += 1
            intersection_state_list = path_i.get_intersections(path_k)
            for state_index in intersection_state_list:
                intersection_db.setdefault(state_index, []).extend([i, k])

    return filter_longest_options(path_list, intersection_db)

def __filter_non_uniform_paths(SM, path_list):
    """Filter-out those paths which are not uniform. The last state can
       be non-uniform, because it is not implemented via 'pathwalk'.
    """
    i = 0
    size = len(path_list)
    while i < size:
        path = path_list[i]
        # Again, the last state does not have to be uniform
        involved_state_list = map(lambda x: x[0], path.sequence()[:-1])
        if not SM.check_uniformity(involved_state_list):
            del path_list[i]
            size -= 1
        else:
            i += 1

def filter_longest_options(path_list, equivalence_db):
    def __longest_path(PathIndexList):
        max_i      = -1
        max_length = -1
        for path_index in PathIndexList:
            length = len(path_list[path_index])
            if length > max_length: 
                max_i      = path_index
                max_length = length
        return max_i

    # Determine the list of states to be deleted
    delete_list = set([])
    for intersection_state, path_index_list in equivalence_db.items():
        i = __longest_path(path_index_list)
        delete_list.update(filter(lambda index: index != i, path_index_list))

    # Now, delete
    offset = 0
    for i in delete_list:
        del path_list[i - offset]
        offset += 1

    # Content of path_list is changed
    return

class CharacterPath:
    def __init__(self, StartStateIndex, Skeleton, StartCharacter):
        """Skeleton = Transition map of the states in the path, i.e. a map

                      target state index ---> trigger set
        """
        assert isinstance(StartStateIndex, long)
        assert isinstance(Skeleton, dict)
        self.__start_state_index = StartStateIndex
        self.__sequence          = [ (StartStateIndex, StartCharacter) ]

        self.__skeleton          = Skeleton
        self.__skeleton_key_set  = set(Skeleton.keys())
        # Character that may trigger to any state. This character is
        # adapted when the first character of the path is different
        # from the wildcard character. Then it must trigger to whatever
        # the correspondent state triggers.
        self.__wildcard          = StartCharacter

    def sequence(self):
        return self.__sequence

    def index(self):
        # Path index = index of the first state in the path
        try:    
            return self.__sequence[0][0]
        except: 
            assert False, \
                   "Character with either no sequence or wrong setup sequence element."

    def skeleton(self):
        assert isinstance(self.__skeleton, dict)
        return self.__skeleton

    def end_state_index(self):
        if len(self.__sequence) == 0: return -1
        return self.__sequence[-1][0]

    def set_end_state_index(self, StateIndex):
        self.__sequence.append((StateIndex, None))

    def append(self, StateIndex, Char):
        self.__sequence.append((StateIndex, Char))

    def contains(self, StateIndex):
        for state_idx, char in self.__sequence:
            if state_idx == StateIndex: return True
        return False

    def covers(self, Other):
        assert isinstance(Other, CharacterPath)
        assert len(self.__sequence) >= 2
        assert len(Other.__sequence) >= 2
        ## print "##covers:", self.__sequence, Other.__sequence

        def __find(StateIndex):
            for i, x in enumerate(self.__sequence):
                if x[0] == StateIndex: return i
            return -1

        # Sequences should not be empty, but if (for some weird reason) it happens
        # make sure it is deleted by __filter_redundant_paths()
        if len(Other.__sequence) == 0: return False

        start_state_index = Other.__sequence[0][0]
        i = __find(start_state_index)
        ## print "##i", start_state_index, i
        if i == -1: return False

        # Do the remaining indices fit?
        L = len(self.__sequence)
        for state_index, char in Other.__sequence[1:]:
            i += 1
            if i >= L: 
                ##print "##out on ", self.__sequence, state_index; 
                return False
            if self.__sequence[i][0] != state_index: 
                return False

        return True

    def get_intersections(self, Other):
        """Determines the state at which the sequences intersect. This
           is mathematically simple the 'intersection' of both sets.
        """

        # The end states are not considered 'intersections'. They are the target
        # states that are transitted after the path is terminated. There is no
        # harm in entering a path after exiting another.
        set_a = set(map(lambda x: x[0], self.__sequence[:-1]))
        set_b = set(map(lambda x: x[0], Other.__sequence[:-1]))

        return set_a.intersection(set_b)

    def match_skeleton(self, TransitionMap, TargetIdx, TriggerCharToTarget):
        """A single character transition 

                        TriggerCharToTarget --> TargetIdx

           has been detected. The question is, if the remaining transitions of
           the state match the skeleton of the current path. There might be a
           wildcard, that is the character that is overlayed by the first
           single character transition.  As long as a transition map is differs
           only by this single character, the wildcard is plugged into the
           position.

           RETURNS: 
                    int > 0, the character that the wildcard shall take so
                             that the skeleton matches the TransitionMap.

                        - 1, if skeleton and TransitionMap match anyway and
                             no wildcard plug is necessary.

                       None, if there is no way that the skeleton and the
                             TransitionMap could match.
        """
        ## ?? The element of a path cannot be triggered by the skeleton! ??
        ## ?? if self.__skeleton.has_key(TargetIdx): return False        ?? 
        ## ?? Why would it not? (fschaef9: 10y04m11d)

        if self.__wildcard != None: wildcard_plug = None # unused
        else:                       wildcard_plug = -1   # used before

        transition_map_key_set = set(TransitionMap.keys())
        # (1) Target States In TransitionMap and Not in Skeleton
        #
        #     All target states of TransitionMap must be in Skeleton,
        #     except:
        #
        #      (1.1) The single char transition target TargetIdx.
        #      (1.2) Maybe, one that is reached by a single char
        #            transition of wildcard.
        delta_set  = transition_map_key_set - self.__skeleton_key_set
        delta_size = len(delta_set)
        if delta_size > 2: return None

        for target_idx in delta_set:
            if   target_idx == TargetIdx:    continue # (1.1)
            elif wildcard_plug != None:                                        return None
            elif not TransitionMap[target_idx].contains_only(self.__wildcard): return None
            wildcard_plug = target_idx                # (1.2)

        # (2) Target States In Skeleton and Not in TransitionMap
        #
        #     All target states of Skeleton must be in TransitionMap,
        #     except:
        #
        #      (2.1) Transition to the target index in skeleton
        #            is covered by current single transition.
        delta_set  = self.__skeleton_key_set - transition_map_key_set
        delta_size = len(delta_set)
        if delta_size > 1: return None
        if delta_size == 1:
            for target_idx in delta_set:
                if not self.__skeleton[target_idx].contains_only(TriggerCharToTarget): return None
            # (2.1) OK, single char covers the transition in skeleton.

        # (3) Target States in both, Skeleton and Transition Map
        #
        #     All correspondent trigger sets must be equal, except:
        #
        #      (3.1) single char transition covers the hole, i.e.
        #            trigger set in transition map + single char ==
        #            trigger set in skeleton. (check this first,
        #            don't waste wildcard).
        #      (3.2) trigger set in skeleton + wildcard == trigger set 
        #            in transition map.
        #       
        common_set = self.__skeleton_key_set & transition_map_key_set
        for target_idx in common_set:
            sk_trigger_set = self.__skeleton[target_idx]
            tm_trigger_set = TransitionMap[target_idx]

            if sk_trigger_set.is_equal(tm_trigger_set): continue

            # (3.1) Maybe the current single transition covers the 'hole'.
            #       (check this first, we do not want to waste the wilcard)
            if can_plug_to_equal(tm_trigger_set, TriggerCharToTarget, sk_trigger_set):
                continue

            elif wildcard_plug == None:
                # (3.2) Can difference between trigger sets be plugged by the wildcard?
                if can_plug_to_equal(sk_trigger_set, self.__wildcard, tm_trigger_set): 
                    wildcard_plug = target_idx
                    continue
                # (3.3) A set extended by wilcard may have only a 'hole' of the
                #       size of the single transition char.
                if can_plug_to_equal(tm_trigger_set, 
                                     TriggerCharToTarget,
                                     sk_trigger_set.union(NumberSet(self.__wildcard))): 
                    wildcard_plug = target_idx
                    continue

            # Trigger sets differ and no wildcard or single transition can
            # 'explain' that => skeleton does not fit.
            return None

        if wildcard_plug == None: return -1 # No plugging necessary
        return wildcard_plug

    def plug_wildcard(self, WildcardPlug):
        assert isinstance(WildcardPlug, (int, long))

        # Finally, if there is a plugging to be performed, then do it.
        if WildcardPlug == -1: return
        
        if self.__skeleton.has_key(WildcardPlug):
            self.__skeleton[WildcardPlug].unite_with(NumberSet(self.__wildcard))
        else:
            self.__skeleton[WildcardPlug] = NumberSet(self.__wildcard)
        self.__skeleton_key_set.add(WildcardPlug)
        self.__wildcard = None # There is no more wildcard now
        
        return 

    def __repr__(self):
        skeleton_txt = ""
        for target_idx, trigger_set in self.__skeleton.items():
            skeleton_txt += "(%i) by " % target_idx
            skeleton_txt += trigger_set.get_utf8_string()
            skeleton_txt += "; "

        sequence_txt = ""
        for state_idx, char in self.__sequence[:-1]:
            sequence_txt += "(%i)--'%s'-->" % (state_idx, chr(char))
        sequence_txt += "[%i]" % self.__sequence[-1][0]

        return "".join(["start    = %i;\n" % self.__start_state_index,
                        "path     = %s;\n" % sequence_txt,
                        "skeleton = %s\n"  % skeleton_txt, 
                        "wildcard = %s;\n" % repr(self.__wildcard != None)])

    def __len__(self):
        return len(self.__sequence)

def find_paths(SM):
    """SM = state machine of analyzer.

       Try to identify 'pathes' that is state transitions in the state machine
       so that a sequence of states can be combined into a single state of the
       shape:

           /* Pre-Test for walking on the path */
           if( input == path_element ) {
               ++path_element;
               if( *path_element == PATH_TERMINATING_CHARACTER ) goto terminal_of_path;
           }
           /* Skeleton (transitions that are common for all elements of path) */
    """
    return __find_begin(SM, SM.init_state_index, SM.init_state_index)

__find_begin_touched_state_idx_list = {}
def __find_begin(sm, StateIndex, InitStateIndex):
    """Searches for the beginning of a path, i.e. a single character 
       transition to a subsequent state. If such a transition is found,
       a 'skeleton' is computed in the 'CharacterPath' object. With this
       object a continuation of the path is searched starting from the
       transitions target state. 
       
       In any case, it is tried to find a path begin in the target state.
       Even if the target state is part of a path, it might have non-path
       targets that lead to pathes. Thus,

       IT CANNOT BE AVOIDED THAT THE RESULT CONTAINS PATHES WHICH ARE 
                           SUB-PATHES OF OTHERS.
    """
    global __find_begin_touched_state_idx_list

    State       = sm.states[StateIndex]
    result_list = []

    transition_map = State.transitions().get_map()
    single_char_transition_found_f = False
    for target_idx, trigger_set in transition_map.items():
        if __find_begin_touched_state_idx_list.has_key(target_idx): continue
        __find_begin_touched_state_idx_list[target_idx] = True

        # IN ANY CASE: Check for paths in the subsequent state
        result_list.extend(__find_begin(sm, target_idx, InitStateIndex))

        # Never allow the init state to be part of the path
        if StateIndex == InitStateIndex: continue

        # Only single character transitions can be element of a path.
        path_char = trigger_set.get_the_only_element()
        if path_char == None: continue

        # A new path begins, find the 'skeleton'.
        # The 'skeleton' is the transition map without the single transition
        skeleton = copy(transition_map) # Shallow copy, i.e. copy references
        # The skeleton is possibly changed in __find_continuation(), but then
        # a 'deepcopy' is applied to disconnect it, see __find_continuation().
        del skeleton[target_idx]        # Delete reference to 'target_idx->trigger_set'

        path = CharacterPath(StateIndex, skeleton, path_char)
            
        result_list.extend(__find_continuation(sm, target_idx, path))

    return result_list

def __find_continuation(sm, StateIndex, the_path):
    """A basic skeleton of the path and the remaining trigger map is given. Now,
       try to find a subsequent path step.
    """
    State       = sm.states[StateIndex]
    result_list = []

    transition_map = State.transitions().get_map()

    single_char_transition_found_f = False
    for target_idx, trigger_set in transition_map.items():

        # Only consider single character transitions can be element of a path.
        path_char = trigger_set.get_the_only_element()
        if path_char == None: continue

        # A recursion cannot be covered by a 'path state'. We cannot extract a
        # state that contains recursions and replace it with a skeleton plus a
        # 'character string position'. Omit this path!
        if the_path.contains(target_idx): continue # Recursion ahead! Don't go!

        # Does the rest of the transitions fit the 'skeleton'?
        plug = the_path.match_skeleton(transition_map, target_idx, path_char)
        if plug == None: continue # No possible match

        # Deepcopy is required to completely isolate the transition map that
        # may now be changed by the wildcard plug.
        path = deepcopy(the_path)
        if plug != -1: path.plug_wildcard(plug)

        # Find a continuation of the path
        single_char_transition_found_f = True
        path.append(StateIndex, path_char)
        result_list.extend(__find_continuation(sm, target_idx, path))

    if not single_char_transition_found_f and len(the_path) != 1:
        the_path.set_end_state_index(StateIndex)
        result_list.append(the_path)

    return result_list

def can_plug_to_equal(Set0, Char, Set1):
    """Determine whether the character 'Char' can be plugged
       to Set0 to make both sets equal.

       (1) If Set0 contains elements that are not in Set1, then 
           this is impossible.
       (2) If Set1 contains elements that are not in Set0, then
           it is possible, if the difference is a single character.

       NOTE:
                Set subtraction: A - B != empty, 
                                 A contains elements that are not in B.
    """
    # If interval number differs more than one, then no single
    # character can do the job.
    if Set1.interval_number() - Set0.interval_number() > 1: return False
    # It is possible that Set0 has more intervals than Set1, e.g.
    # Set0 = {[1,2], [4]}, and Set1={[1,4]}. In this example, '3'
    # can plug Set0 to be equal to Set1. A difference > 1 is impossible,
    # because, one character can plug at max. one 'hole'.
    if Set0.interval_number() - Set1.interval_number() > 1: return False

    # Does Set0 contain elements that are not in Set1?
    # if not Set0.difference(Set1).is_empty(): return False
    if not Set1.is_superset(Set0): return False

    # If there is no difference to make up for, then no plugging possible.
    # if Set1.difference(Set0).is_empty(): return False
    if Set0.is_superset(Set1): return False

    delta = Set1.difference(Set0)
    return delta.contains_only(Char)
