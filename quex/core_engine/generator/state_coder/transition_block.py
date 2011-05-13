import quex.core_engine.generator.state_coder.transition as transition
from   quex.input.setup                                  import setup as Setup
from   quex.core_engine.interval_handling                import Interval

import sys
from   math import log
from   copy import copy

__DEBUG_CHECK_ACTIVE_F = False # Use this flag to double check that intervals are adjacent

class TriggerAction:
    def __init__(self, Code, DropOutF=False):
        assert type(DropOutF) == bool

        if type(Code) == list: self._code = Code
        else:                  self._code = [ Code ]
        self.__drop_out_f = DropOutF

    def get_code(self):
        return self._code

    def is_drop_out(self):
        return False

class TriggerActionTransition(TriggerAction):
    def __init__(self, TargetStateIndex):
        self.__target_state_index = TargetStateIndex

    def get_code(self):
        return [ transition.get_transition_to_state(self.__target_state_index) ]

class TriggerActionDropOut(TriggerAction):
    def __init__(self, CurrentStateIdx):
        self.__state_index = CurrentStateIdx

    def get_code(self):
        # The call to 'get_transition_to_drop_out()' is delayed until the code
        # is implemented. This is so, since 'get_transition_to_drop_out' causes
        # the drop-out label being entered into the 'used' list. However, it may
        # happen, that the Drop-Out Labels are optimized away. Then, it would be
        # marked as 'used' while nothing in the code refers to it.
        return [ transition.get_transition_to_drop_out(self.__state_index) ]

    def is_drop_out(self):
        return True

class TriggerActionReload(TriggerAction):
    def __init__(self, GotoReload_Str, CurrentStateIdx, DSM, ReturnToState_Str):
        self.__goto_reload_str     = GotoReload_Str
        self.__state_index         = CurrentStateIdx
        self.__dsm                 = DSM
        self.__return_to_state_str = ReturnToState_Str

    def get_code(self):

        if self.__goto_reload_str != None: 
            return [ self.__goto_reload_str ]
        else:
            return [ transition.get_transition_to_reload(self.__state_index, 
                                                         self.__dsm, 
                                                         self.__return_to_state_str) ]

def __interpret(TriggerMap, CurrentStateIdx, DSM, ReturnToState_Str, GotoReload_Str):
    """ReturnToState_Str is only required if the reload has a particular
                         procedure to return to the current state. This
                         is true for path walker and template states.

                         = None --> no special action required.
    """
    result = [None] * len(TriggerMap)
    for i, entry in enumerate(TriggerMap):
        interval = entry[0]
        target   = entry[1]

        if   target == -1:
            target = TriggerActionReload(GotoReload_Str, CurrentStateIdx, DSM, ReturnToState_Str)

        elif target == None:
            target = TriggerActionDropOut(CurrentStateIdx)

        elif type(target) in [int, long]:
            target = TriggerActionTransition(target)

        else:
            assert isinstance(target, TriggerAction) # No change necessary

        result[i] = (interval, target)
    return result

def do(TriggerMap, StateIdx, DSM, ReturnToState_Str=None, GotoReload_Str=None):
    """Target == None           ---> Drop Out
       Target == -1             ---> Buffer Limit Code; Require Reload
                                     (this one is added by '__separate_buffer_limit_code_transition()'
       Target == Integer >= 0   ---> Transition to state with index 'Target'
       Target == string         ---> past code fragment 'Target' for given Interval
    """
    assert type(TriggerMap) == list
    assert DSM == None or DSM.__class__.__name__ == "StateMachineDecorator"
    # If a state has no transitions, no new input needs to be eaten => no reload.
    #
    # NOTE: The only case where the buffer reload is not required are empty states,
    #       AND states during backward input position detection!
    #       Empty states do not exist any longer, the backward input position is
    #       essential though for pseudo ambiguous post contexts.
    assert TriggerMap != [] # states with empty trigger maps are 'dead end states'. those
    #                       # are not to be coded at this place.
    if DSM == None: InitStateF = False
    else:           InitStateF = (StateIdx == DSM.sm().init_state_index)

    TriggerMap = __prune_trigger_map_to_character_type_domain(TriggerMap)

    # The 'buffer-limit-code' always needs to be identified separately.
    # This helps to generate the reload procedure a little more elegantly.
    __separate_buffer_limit_code_transition(TriggerMap)

    # Interpret the trigger map.
    # The actions related to intervals become code fragments (of type 'str')
    TriggerMap = __interpret(TriggerMap, StateIdx, DSM, ReturnToState_Str, GotoReload_Str)
    # __implement_switch_transitions(TriggerMap)

    if len(TriggerMap) > 1:
        # Check whether some things might be pre-checked before the big trigger map
        # starts working. This includes likelyhood and 'assembler-switch' implementations.
        # The TriggerMap has now been adapted to reflect that some transitions are
        # already implemented in the priorized_code
        code = __get_code(TriggerMap)
    else:
        # We can actually be sure, that the Buffer Limit Code is filtered
        # out, since this is the task of the regular expression parser.
        # In case of backward lexing in pseudo-ambiguous post conditions,
        # it makes absolutely sense that there is only one interval that
        # covers all characters (see the discussion there).
        # assert TriggerMap[0][0].begin == -sys.maxint
        # assert TriggerMap[0][0].end   == sys.maxint
        code = ["    "] + TriggerMap[0][1].get_code() + ["\n"]

    return format_this(code)

def format_this(txt):
    """Expects a sequence of constant strings and integers. An 
       integer is expanded to 'N*"    "' in order to implement 
       indentation.
    """
    # Replace the indentation information with real 'indentation'
    for i, elm in enumerate(txt):
        if type(elm) == int: txt[i] = "    " * elm
    return txt

def indent_this(txt):
    for i, elm in enumerate(txt):
        if type(elm) == int: txt[i] += 1
    return txt

def __get_code(TriggerMap):
    """Creates code for state transitions from this state. This function is very
       similar to the function creating code for a 'NumberSet' condition 
       (see 'interval_handling').
    
       Writes code that does a mapping according to 'binary search' by
       means of if-else-blocks.
    """
    TriggerSetN = len(TriggerMap)

    if TriggerSetN > 1 and __DEBUG_CHECK_ACTIVE_F:
        # -- check that the trigger map consist of sorted adjacent intervals 
        #    This assumption is critical because it is assumed that for any isolated
        #    interval the bordering intervals have bracketed the remaining cases!
        previous_interval = TriggerMap[0][0] 
        for interval, target_state_index in TriggerMap[1:]:
            assert interval.begin == previous_interval.end, \
                   "Non-adjacent intervals in TriggerMap\n" + \
                   "TriggerMap = " + repr(TriggerMap)
            assert interval.end > interval.begin, \
                   "Interval of size zero in TriggerMap\n" + \
                   "TriggerMap = " + repr(TriggerMap)
            previous_interval = interval

    #________________________________________________________________________________

    txt = []
    if TriggerSetN == 1 :
        # (*) Only one interval 
        #     (all boundaring cases must have been dealt with already => case is clear)
        #     If the input falls into this interval the target trigger is identified!
        __create_transition_code(txt, TriggerMap[0])
        
    else:    
        # two or more intervals => cut in the middle
        MiddleTrigger_Idx = int(TriggerSetN / 2)
        middle            = TriggerMap[MiddleTrigger_Idx]

        # input < 0 is impossible, since unicode codepoints start at 0!
        if middle[0].begin == 0: 
            txt = __get_code(TriggerMap[MiddleTrigger_Idx:]) 
        else: 
            if   __get_switch(txt, TriggerMap):    pass
            elif __get_bisection(txt, TriggerMap): pass

    # (*) indent by four spaces (nested blocks are correctly indented)
    #     delete the last newline, to prevent additional indentation
    indent_this(txt)
    return txt

def __get_bisection(txt, TriggerMap):
    LanguageDB = Setup.language_db

    L = len(TriggerMap)
    preferred_section_index = int(L / 2)
    section_index           = preferred_section_index

    # Make sure that no cut in the middle of a switch case
    preferred_section_index = int(L / 2)
    best_section_index      = -1
    best_dist               = L
    switch_case_range_list  = __get_switch_cases_info(TriggerMap)
    for candidate in xrange(L):
        for p, q in switch_case_range_list:
            if candidate >= p and candidate <= q: 
                break
        else:
            # No intersection happened, so index may be used
            if abs(candidate - preferred_section_index) >= best_dist: continue
            best_section_index = candidate
            best_dist          = abs(candidate - preferred_section_index)

    if best_section_index not in [-1, 0, L-1]: section_index = best_section_index
    else:                                      section_index = preferred_section_index; 

    if __get_linear_comparison_chain(txt, TriggerMap, L): return True

    middle = TriggerMap[section_index]
    lower  = TriggerMap[:section_index]
    higher = TriggerMap[section_index:]

    assert middle[0].begin >= 0, \
           "code generation: error cannot split intervals at negative code points."

    __get_bisection_code(txt, middle, lower, higher)
    return True

def __get_linear_comparison_chain(txt, TriggerMap, L):

    LanguageDB = Setup.language_db
    # 5 intervals --> 4 border checks
    if L > 5: return False
    assert L != 1

    trigger_map = TriggerMap

    _cmp_eq     = LanguageDB["$=="]
    _cmp_border = LanguageDB["$<"]
    _border     = lambda interval: interval.end

    # The buffer limit code is something extreme seldom, so make sure that it is 
    # tested at last, if it is there. This might require to reverse the trigger map.
    if     Setup.buffer_limit_code >= TriggerMap[0][0].begin \
       and Setup.buffer_limit_code < TriggerMap[-1][0].end:
        # Find the index of the buffer limit code in the list
        for i, candidate in enumerate(TriggerMap):
            if candidate[0].contains(Setup.buffer_limit_code): break
        if i < L / 2:
            trigger_map = copy(TriggerMap)
            trigger_map.reverse()
            _cmp_border = LanguageDB["$>="]
            _border     = lambda interval: interval.begin

    for i, entry in enumerate(trigger_map):
        interval, target = entry

        txt.append(0)
        if i == L - 1:
            # Drop-out 'else' can be omitted
            if not target.is_drop_out(): 
                txt.append(LanguageDB["$endif-else"])
        else:
            if i == 0: txt.append(LanguageDB["$if"])
            else:      txt.append(LanguageDB["$elseif"])

            if interval.size() == 1:
                comparison = _cmp_eq("input", "0x%X" % interval.begin)
            else:
                comparison = _cmp_border("input", "0x%X" % _border(interval))

            txt.append(comparison)
            txt.append(LanguageDB["$then"])

        if not target.is_drop_out():
            __create_transition_code(txt, entry)

    txt.append(LanguageDB["$endif"])
    return True

def __get_bisection_code(txt, middle, lower, higher):
    LanguageDB = Setup.language_db

    # Note, that an '<' does involve a subtraction. A '==' only a comparison.
    # The latter is safe to be faster (or at least equally fast) on any machine.
    txt.append(0)
    if len(higher) == 1 and higher[0][1].is_drop_out():
        
        # If the size of one interval is 1, then replace the '<' by an '=='.
        if   len(lower)  == 1 and lower[0][0].size() == 1:
            comparison = LanguageDB["$if =="]("0x%X" % lower[0][0].begin)
        elif higher[0][0].size() == 1:
            comparison = LanguageDB["$if !="]("0x%X" % higher[0][0].begin)
        else:
            comparison = LanguageDB["$if <"]("0x%X" % higher[0][0].begin)

        # No 'else' case for what comes BEHIND middle
        txt.append(comparison)
        txt.extend(__get_code(lower))

    elif len(lower) == 1 and lower[0][1].is_drop_out():
        if   lower[0][0].size() == 1:
            comparison = LanguageDB["$if !="]("0x%X" % lower[0][0].begin)
        elif len(higher) == 1 and higher[0][0].size() == 1:
            comparison = LanguageDB["$if =="]("0x%X" % higher[0][0].begin)
        else:
            comparison = LanguageDB["$if >="]("0x%X" % lower[0][0].end)

        # No 'else' case for what comes BEFORE middle
        txt.append(comparison)
        txt.extend(__get_code(higher))

    else:
        # If the size of one interval is 1, then replace the '<' by an '=='.
        if   len(lower)  == 1 and lower[0][0].size() == 1:
            comparison = LanguageDB["$if =="]("0x%X" % lower[0][0].begin)
        elif len(higher) == 1 and higher[0][0].size() == 1:
            comparison = LanguageDB["$if !="]("0x%X" % higher[0][0].begin)
        else:
            comparison = LanguageDB["$if <"]("0x%X" % middle[0].begin)

        txt.append(comparison)
        txt.extend(__get_code(lower))
        txt.append(0)
        txt.append(LanguageDB["$endif-else"])
        txt.extend(__get_code(higher))

    txt.append(0)
    txt.append(LanguageDB["$endif"])

def __create_transition_code(txt, TriggerMapEntry):
    """Creates the transition code to a given target based on the information in
       the trigger map entry.
    """
    LanguageDB = Setup.language_db
    comment_function = LanguageDB["$comment"]
    comment          = lambda interval: comment_function(interval.get_utf8_string())

    interval           = TriggerMapEntry[0]
    target_state_index = TriggerMapEntry[1]       
    #  target state != None, then the machine is still eating
    #                        => transition to subsequent state.
    #
    #  target state == None, drop into a terminal state (defined by origins).
    #
    #  for details about $transition, see the __transition() function of the
    #  respective language module.
    #
    txt.append(1)                              # indent one scope
    txt.extend(target_state_index.get_code())

    if Setup.buffer_codec == "": txt.append("    " + comment(interval) + "\n")
    else:                        txt.append("\n")

    return 

def __get_switch(txt, TriggerMap):
    LanguageDB = Setup.language_db

    drop_out_range_n = 0
    character_n      = 0
    for interval, target in TriggerMap:
        if target.is_drop_out(): drop_out_range_n += 1
        else:                    character_n      += interval.size()

    if __switch_case_heuristic(TriggerMap) == False:
        return False

    case_code_list = []
    for interval, target in TriggerMap:
        if target.is_drop_out(): continue
        target_code = target.get_code()
        for i in range(interval.begin, interval.end):
            case_code_list.append((i, target_code))

    txt.extend(LanguageDB["$switch-block"]("input", case_code_list))
    return True

def __implement_switch_transitions(trigger_map):
    """Transitions of characters that lie close to each other can be very efficiently
       be identified by a switch statement. For example:

           switch( Value ) {
           case 1: ..
           case 2: ..
           ...
           case 100: ..
           }

       Is implemented by the very few lines in assembler (i386): 

           sall    $2, %eax
           movl    .L13(%eax), %eax
           jmp     *%eax

       where 'jmp *%eax' jumps immediately to the correct switch case.
    
       It is therefore of vital interest that those regions are **identified** and
       **not split** by a bisection. To achieve this, such regions are made a 
       transition for themselves based on the character range that they cover.
    """
    LanguageDB = Setup.language_db
    Tiny      = 20
    MinExtend = 4
    i = 0
    L = len(trigger_map)
    while i != L:
        interval, target = trigger_map[i]

        if interval.size() > Tiny: 
            i += 1
            continue

        # Collect 'tiny neighbours'
        k                     = i
        switch_case_code_list = []
        candidate_extend      = 0
        while 1 + 1 == 2:
            if not target.is_drop_out(): 
                target_code = target.get_code()
                for p in xrange(interval.begin, interval.end):
                    switch_case_code_list.append((p, target_code))
            candidate_extend += interval.size()

            k += 1
            if k == L: break 

            interval, target = trigger_map[k]
            if interval.size() > Tiny: break

        if candidate_extend < MinExtend: 
            i = k 
            continue

        # trigger_map[i][0].begin to trigger_map[k-1][0].end all becomes
        # switch case transition.
        switch_case_transition_code = LanguageDB["$switch-block"]("input", switch_case_code_list)

        trigger_map[i] = (Interval(trigger_map[i][0].begin, trigger_map[k-1][0].end),
                          TriggerAction(switch_case_transition_code))
        if k - i != 1:
            del trigger_map[i+1:k]
            L -= (k - i - 1)
            # assert L == len(trigger_map)
        i += 1

    return

def __get_switch_cases_info(TriggerMap):
    L = len(TriggerMap)
    sum_interval_size          = [0] * (L+1)
    sum_drop_out_interval_size = [0] * (L+1)
    i = 0
    for interval, target in TriggerMap:
        i += 1
        sum_interval_size[i]          = sum_interval_size[i-1]
        sum_drop_out_interval_size[i] = sum_drop_out_interval_size[i-1]
        if target.is_drop_out(): sum_drop_out_interval_size[i] += interval.size()
        else:                    sum_interval_size[i]          += interval.size()

    switch_case_range_list = []
    p = 0
    while p < L:
        # Count from the back, so the longest is treated first.
        # Thus, if there is a 'p' for a given 'q' where the criteria
        # holds for a switch case, then the 'p' is the best one, in the
        # sense that it is the largest interval.
        q_found = None
        for q in xrange(L-1, p, -1):
            if __switch_case_heuristic(TriggerMap[p:q+1], 
                                       size_all_intervals          = sum_interval_size[q]          - sum_interval_size[p],
                                       size_all_drop_out_intervals = sum_drop_out_interval_size[q] - sum_drop_out_interval_size[p]):
                switch_case_range_list.append((p, q))
                q_found = q
                break
        # If there was a switch case range, that step over it to the next
        if q_found: p = q_found
        p += 1
    return switch_case_range_list

def __switch_case_heuristic(TriggerMap, 
                            size_all_intervals=None, 
                            size_all_drop_out_intervals=None):
    """Let P be the preferably of a switch statement over bisection or linear if-else
       blocks. The following heuristics may be applied:
    
       -- The more ranges are involved in a trigger map, the more 'if-else' we need,
          thus:
                   P increases with len(trigger_map)

          Since only for bisection only log2(N) comparisons are necessary (and if linear
          if-else blocks are used, then only if N/2 < log2(N)), it may be assumed that

              (1)  P increases with log2(len(trigger_map))            

       -- The look-up tables used for switches can potentially grow large, so that

                   P decreases with size(trigger_map)

          where size(trigger_map) = all characters minus the ones that 'drop-out', thus
           
              (2)  P decreases with size(all intervals) - size(all drop out intervals)
               

       The following heuristic is proposed:

              P = log2(len(trigger_map)) / sum(all interval) - sum(drop_out_intervals) 
    """
    if size_all_intervals == None:
        size_all_intervals          = 0
        size_all_drop_out_intervals = 0
        for interval, target in TriggerMap:
            if target.is_drop_out(): size_all_drop_out_intervals += interval.size()
            size_all_intervals += interval.size()

    if size_all_intervals - size_all_drop_out_intervals == 0:
        return False

    p = log(len(TriggerMap), 2) / (size_all_intervals - size_all_drop_out_intervals)

    return p > 0.03

def __separate_buffer_limit_code_transition(TriggerMap):
    """This function ensures, that the buffer limit code is separated 
       into a single value interval. Thus the transition map can 
       transit immediate to the reload procedure.
    """
    for i, entry in enumerate(TriggerMap):
        interval, target_index = entry

        if   target_index == -1:   
            assert interval.contains_only(Setup.buffer_limit_code) 
            # Transition 'buffer limit code --> -1' has been setup already
            return

        elif target_index != None: 
            continue

        elif not interval.contains(Setup.buffer_limit_code): 
            continue

        # Found the interval that contains the buffer limit code.
        # If the interval's size is alread 1, then there is nothing to be done
        if interval.size() == 1: return

        before_begin = interval.begin
        before_end   = Setup.buffer_limit_code 
        after_begin  = Setup.buffer_limit_code + 1
        after_end    = interval.end

        # Replace Entry with (max.) three intervals: before, buffer limit code, after
        del TriggerMap[i]

        if after_end > after_begin:
            TriggerMap.insert(i, (Interval(after_begin, after_end), None))

        # "Target == - 1" ==> Buffer Limit Code
        TriggerMap.insert(i, (Interval(Setup.buffer_limit_code, Setup.buffer_limit_code + 1), -1))

        if before_end > before_begin and before_end > 0:
            TriggerMap.insert(i, (Interval(before_begin, before_end), None))

        return

    # It is conceivable, that the transition does not contain a 'None' transition
    # on buffer limit code. This happens for example, during backward detection
    # where it is safe to assume that the buffer limit code may not occur.
    return

#__likely_char_list = [ ord(' ') ]
#def __get_priorized_code(trigger_map, info):
#    """-- Write code to trigger on likely characters.
#       -- Use that fact that assemblers can do 'switch-case indexing'
#          which is much faster than N comparisons.
#    """
#    LanguageDB = Setup.language_db
#
#    if len(trigger_map) <= 1: return ""
#
#    # -- Very likely characters
#    result  = []
#    first_f = True
#    for character_code in __likely_char_list:
#        first_f, txt = __extract_likely_character(trigger_map, character_code, first_f, info)
#        result.extend(txt)
#    if len(result) != 0: 
#        result.append(LanguageDB["$endif"])
#
#    # -- Adjacent tiny domains --> Assembler might use fast indexing.
#    #    Setup 'TinyNeighborTransitions' objects as targets so that transition
#    #    code generator can generate 'switch' statements.
#    tiny_neighbour_list = __filter_tiny_neighours(trigger_map)
#
#    if len(tiny_neighbour_list):
#        result.append("    ")
#        result.append(LanguageDB["$switch"]("input"))
#        for entry in tiny_neighbour_list:
#            result.extend(__tiny_neighbour_transitions(entry, info.state_index, info.dsm))
#        result.append("    ")
#        result.append(LanguageDB["$switchend"])
#        result.append("\n")
#
#    return "".join(result)
#
#def __tiny_neighbour_transitions(Info, CurrentStateIdx, DSM):
#    LanguageDB = Setup.language_db
#    assert Info.__class__.__name__ == "TinyNeighborTransitions"
#
#    result = []
#    for number, target in Info.get_mapping():
#        assert target.__class__.__name__ != "TinyNeighborTransitions"
#        result.append("       ")
#        result.append(LanguageDB["$case"]("0x%X" % number))
#        result.append(target.get_code())
#        result.append("\n")
#
#    return result
#    
#class TinyNeighborTransitions:
#    def __init__(self):
#        self.__list = []
#
#    def append(self, Interval, Target):
#        self.__list.append((Interval, Target))
#
#    def get_mapping(self):
#        mapping = []
#        for interval, target in self.__list:
#            for i in range(interval.begin, interval.end):
#                mapping.append((i, target))
#        return mapping
#
#def __filter_tiny_neighours(trigger_map):
#    result    = []
#
#    Tiny      = 20
#    MinExtend = 4
#    i = 0
#    L = len(trigger_map)
#    while i != L:
#        interval, target = trigger_map[i]
#
#        if interval.size() > Tiny: 
#            i += 1
#            continue
#
#        # Collect tiny neighbours
#        k                = i
#        candidate        = TinyNeighborTransitions()
#        candidate_extend = 0
#        while 1 + 1 == 2:
#            assert target.__class__ != TinyNeighborTransitions
#
#            candidate.append(interval, target)
#            candidate_extend += interval.size()
#
#            k += 1
#            if k == L: break 
#
#            interval, target = trigger_map[k]
#            if interval.size() > Tiny: break
#
#        if candidate_extend < MinExtend: 
#            i = k 
#            continue
#
#        else:
#            # User trigger_map[i], adapt it to reflect that from
#            # trigger_map[i][0].begin to trigger_map[k-1][0].end all becomes
#            # a 'tiny neighbour region'.
#            Begin = trigger_map[i][0].begin
#            End   = trigger_map[k-1][0].end
#            result.append(candidate)
#            del trigger_map[i:k] # Delete (k - i) elements
#            if i != 0: trigger_map[i][0].begin = trigger_map[i-1][0].end
#            else:      trigger_map[i][0].begin = - sys.maxint
#            L -= (k - i)
#            if i == L: break
#
#    return result
#
#def code_this(result, Letter, Target, first_f, info):
#    LanguageDB = Setup.language_db
#
#    if first_f: result += LanguageDB["$if =="]("0x%X" % Letter)    
#    else:       result += LanguageDB["$elseif =="]("0x%X" % Letter)
#    result.append("    ")
#    result.append(transition.do(Target, info.state_index, Interval(Letter), info.dsm))
#    result.append("\n")
#
#def __extract_likely_character(trigger_map, CharacterCode, first_f, info):
#    LanguageDB = Setup.language_db
#
#    i      = 0
#    L      = len(trigger_map)
#    result = []
#    while i != L:
#        interval, target = trigger_map[i]
#
#        if not interval.contains(CharacterCode): 
#            i += 1
#            continue
#
#        elif interval.size() != 1: 
#            # (0.a) size(Interval) != 1
#            #       => no need to adapt the trigger map.
#            # 
#            #     x[     ]   --> trigger map catches on 'x' even
#            #                    though, it has been catched on the
#            #                    priorized map --> no harm.
#            #     [  x   ]   --> same
#            #     [     ]x   --> same
#            code_this(result, CharacterCode, target, first_f, info)
#            first_f = False
#            i += 1
#            continue
#
#        elif L == 1:
#            # (0.b) If there's only one transition remaining (which
#            #       is of size 1, see above). Then no preference needs
#            #       to be given to the likely character.
#            break   # We are actually done!
#
#        else:
#            # (1) size(Interval) == 1
#            #     => replace trigger with adjacent transition
#            code_this(result, CharacterCode, target, first_f, info)
#            first_f = False
#        
#            del trigger_map[i]
#            # Intervals **must** be adjacent
#            assert trigger_map[i][0].begin == CharacterCode + 1
#            trigger_map[i][0].begin = CharacterCode
#            # Once the letter has been found, we are done
#            break
#
#    return first_f, result

def __prune_trigger_map_to_character_type_domain(trigger_map):

    UpperLimit = Setup.get_character_value_limit()
    LowerLimit = 0

    if UpperLimit == -1: return trigger_map

    new_trigger_map = []
    for entry in trigger_map:
        interval, target = entry

        if interval.end <= LowerLimit: 
            # No character can have a value below zero
            continue
        elif interval.begin > UpperLimit:
            break
        elif interval.end < UpperLimit:
            new_trigger_map.append(entry)
        else:
            # Interval overlaps the end. Thus it is the last and
            # does not need to be checked.
            new_trigger_map.append([Interval(interval.begin, UpperLimit), target])
    return new_trigger_map

