from quex.core_engine.interval_handling import Interval, NumberSet

# Distance Database: Store the distance from state (given by index)
#                    to the acceptance state, i.e. map:
# 
#                       state_index --> distance to acceptance state
__distance_db = {}

def get_newline_n(state_machine):   
    """
       Counts the number of newlines that appear until the acceptance state. 
       The part of the post condition is omitted. 

       RETURNS:  0      if statemachine / pattern does not contain the newline
                        character at all.
                 N > 0  number of newlines that are **always** required in order to
                        reach an acceptance state.
                 -1     the number of newlines cannot be determined, because of 
                        recursion or because there are different pathes to acceptance
                        with different numbers of newlines occuring.

       NOTE: Only the core pattern is concerned---not the pre- or post-condition.
    """
    global __distance_db

    # State machine shall not have pre or post conditions
    assert state_machine.core().pre_context_sm_id() == -1
    assert state_machine.core().post_context_id() == -1

    __distance_db.clear()
    result = __dive(state_machine, state_machine.init_state_index, 0, [], CharacterToCount=ord('\n'))
    if result == None: return -1
    else:              return result

def get_character_n(state_machine):
    """
       Counts the number of characters that appear until the acceptance state. 
       The part of the post condition is omitted. 

       RETURNS:  0      if statemachine / pattern does not contain the newline
                        character at all.
                 N > 0  number of newlines that are **always** required in order to
                        reach an acceptance state.
                 -1     the number of newlines cannot be determined, because of 
                        recursion or because there are different pathes to acceptance
                        with different numbers of newlines occuring.

       NOTE: Only the core pattern is concerned---not the pre- or post-condition.
    """
    global __distance_db

    # State machine shall not have pre or post conditions
    assert state_machine.core().pre_context_sm_id() == -1
    assert state_machine.core().post_context_id() == -1

    __distance_db.clear()
    result = __dive(state_machine, state_machine.init_state_index, 0, [], CharacterToCount=-1)
    if result == None: return -1
    else:              return result

def __recursion_contains_critical_character(state_machine, Path, TargetStateIdx, Character):
    """Path      = list of state indices
       Character = character code of concern.
                   -1 => any character.
       
       RETURNS:  True = the path contains the TargetStateIdx and on the path
                        there is the critical character.
                 False = the path does either not contain the TargetStateIdx,
                         i.e. there will be no recursion, or the recursion
                         path does not contain the critical character and 
                         therefore is not dangerous.

       NOTE: This function is required to judge wether a recursion occurs
             that effects the number of characters to be counted. If so,
             then the recursion signifies that the number of characters
             to be matched cannot be determined directly from the state machine.
             They have to be computed after a match has happend.
    """
    assert TargetStateIdx in Path 
    # If all characters are relevant (Character == -1), then any recursion is critical
    if Character == -1: return True

    # -- recursion detected!
    #    did the critical character occur in the path?
    occurence_idx = Path.index(TargetStateIdx)
    prev_idx      = TargetStateIdx
    for idx in Path[occurence_idx+1:] + [TargetStateIdx]:
        # does transition from prev_state to state contain newline?
        trigger_set = state_machine.states[prev_idx].transitions().get_trigger_set_to_target(idx)
        if trigger_set.contains(Character):
            return True                       # YES! recursion with critical character
        prev_idx = idx

    # -- no critical character in recursion --> OK, no problem
    # -- state has been already handled, no further treatment required
    return False

def __dive(state_machine, state_index, character_n, passed_state_list, CharacterToCount):
    """Once the distance to the acceptance state is determined, we store it in a cache database.
       Note, that the distance is only stored after all possible pathes starting from the state
       have been investigated. Note also, that the distance to the acceptance state can be 
       '-1' meaning that there are multiple pathes of different length, i.e. it cannot be
       determined from the pattern how many characters appear in the lexeme that matches.
    """
    global __distance_db
    if __distance_db.has_key(state_index): 
        # Total distance:   distance from current state to acceptance state
        #                 + distance from start         to current state
        return __distance_db[state_index] + character_n

    # Dive to determine total path length from start to acceptance state
    total_path_length = ____dive(state_machine, state_index, character_n, 
                                 passed_state_list, CharacterToCount)

    if total_path_length != None:
        if state_index not in passed_state_list:
            # Distance to acceptance:   total path length from start to acceptance state 
            #                         - path length       from start to current state
            __distance_db[state_index] = total_path_length - character_n

    return total_path_length

def ____dive(state_machine, state_index, character_n, passed_state_list, CharacterToCount):
    ##print "##>>", state_index, passed_state_list, character_n
    state = state_machine.states[state_index]

    new_passed_state_list = passed_state_list + [ state_index ]

    prev_characters_found_n = None
    if state.is_acceptance(): prev_characters_found_n = character_n

    # trigger_map[target_state_index] = set that triggers to target state index
    trigger_dict = state.transitions().get_map()

    # Treat linear state transitions inside a loop, this is faster
    # and less prone to blow the call stack of python for large patterns.
    while len(trigger_dict) == 1:
        follow_state_index, trigger_set = trigger_dict.items()[0]

        # -- Recursion:
        if follow_state_index in new_passed_state_list: 
            if __recursion_contains_critical_character(state_machine, new_passed_state_list, 
                                                       follow_state_index, CharacterToCount):
                return -1
            break

        # -- Increment
        increment = __get_increment(trigger_set, CharacterToCount)
        if increment == -1: return -1

        state = state_machine.states[follow_state_index]
        new_passed_state_list.append(follow_state_index)
        character_n += increment

        if state.is_acceptance(): 
            if prev_characters_found_n == None:          prev_characters_found_n = character_n
            elif prev_characters_found_n != character_n: return -1

        trigger_dict = state.transitions().get_map()

    
    if len(trigger_dict) == 0: return prev_characters_found_n

    for follow_state_index, trigger_set in trigger_dict.items():

        # -- Recursion:
        if follow_state_index in new_passed_state_list: 
            # Relevant character in recursive path => occurency number undetermined. 
            if __recursion_contains_critical_character(state_machine, new_passed_state_list, 
                                                       follow_state_index, CharacterToCount):
                return -1
            # If no influence of recursion to character count --> just ignore it.
            continue
            
        # -- Increment of character count
        increment = __get_increment(trigger_set, CharacterToCount)
        if increment == -1: return -1

        # --diving deeper into the tree
        characters_found_n = __dive(state_machine, follow_state_index, 
                                    character_n + increment, 
                                    new_passed_state_list, CharacterToCount)

        if   characters_found_n      == -1:                 return -1
        elif prev_characters_found_n == None:               prev_characters_found_n = characters_found_n
        elif prev_characters_found_n != characters_found_n: return -1

    if prev_characters_found_n == None: return -1
    else:                               return prev_characters_found_n

def __get_increment(trigger_set, CharacterToCount):
        
    if CharacterToCount == -1:
        # (1.1) We are counting all characters, so we increment always.
        return 1

    elif not trigger_set.contains(CharacterToCount):
        # (2.1) The trigger set does not contain the character to be counted at all
        #       Thus the number of occurences is deterministic and **no increment occurence counter**.
        return 0

    elif trigger_set.has_only_this_element(CharacterToCount):
        # (2.2) The trigger set contains only the character to be counted.
        #       Thus the number of occurences is deterministic and **increment occurence counter**.
        return 1

    else:
        # (2.3) The trigger set contains the character to be counted and also others. This
        #       means that for the transition the number of occurences (zero or one) is not
        #       determined by the pattern. Thus the number of occurences not deterministic.
        return -1

