"""Path Compression ___________________________________________________________

   Consider the file 'core_engine/state_machine/compression/paths.py' for 
   a detailed explanation of path compression.

   Code Generation ____________________________________________________________

   Let 'path walker' be a code fragment that is able to 'walk' along a given
   path and follow a 'skeleton', i.e. a general transition map, if the current
   character is not the one of the path. As described in the above file, 
   a state is defined by a 'path walker' index and an iterator position that
   points to the position of a specific character string. Following code
   fragments need to be generated:

   (1) The pathes, i.e. array containing identified sequences, e.g.

        QUEX_CHARACTER_TYPE   path_0 = { 'o', 'r', PTC }; 
        QUEX_CHARACTER_TYPE   path_1 = { 'h', 'i', 'l', 'e', PTC }; 
        QUEX_CHARACTER_TYPE   path_2 = { 'e', 't', 'u', 'r', 'n', PTC }; 

       where PTC is the path terminating code that must be 
       different from the buffer limit code BLC.

       The init state shall usually not be a path state. It rather routes
       to paths. This is why identified pathes usually do not contain the
       first character of a related keyword. Note, however, that quex 
       may find paths that are not explicitly considered by the user.

   (2) The path walker.

       The path walker consist of a 'prolog' where the current input character
       is checked whether it belongs to the path, and the remainging trigger
       map, in case that the path is left, e.g.

         PATH_WALKER_1:
            /* Single Character Check */
            if   input == *path_iterator: ++path_iterator; goto PATH_WALKER_1
            elif *path_iterator == PTC:     goto STATE_3

            /* Common Transition Map */
            if   x < 'a': drop out
            elif x > 'z': drop out
            else:         goto STATE_4

   (3) State entries

       When pathes are keywords, then states that belong to a path are not
       entered except through 'path walk' along the character sequence.
       Theoretically, however, a state of a path might be entered from
       everywhere. Thus, at least for those states that are entered from
       somewhere, a path entry must be provided. 

       A path entry consists of: setting the path iterator and goto the
       related path walker. Additionally, state attributes, such as 
       'acceptance' and 'store_input_position' must be considered. 
       Example:

          STATE_10:
                path_iterator = path_0;
                goto PATH_WALKER_1;
          STATE_11:
                path_iterator = path_0 + 1;
                goto PATH_WALKER_1;
          ...
            
    (4) State router, this might be necessary, if states are non-uniform.
        Because, after reload the current state entry must passed by again.
        In buffer based analyzis no state router is required. Example of 
        a state router (same as for template compression):
        
        
            switch( state_index ) {
            case 2222: goto STATE_2222;
            case 3333: goto STATE_3333;
            ...
            }
"""
from   quex.core_engine.generator.state_machine_decorator import StateMachineDecorator

import quex.core_engine.generator.state_coder.core             as state_coder
import quex.core_engine.generator.state_coder.transition       as transition
import quex.core_engine.generator.state_coder.input_block      as input_block
import quex.core_engine.generator.state_coder.acceptance_info  as acceptance_info
import quex.core_engine.generator.state_coder.transition_block as transition_block
import quex.core_engine.generator.state_coder.drop_out         as drop_out
import quex.core_engine.generator.template_coder               as template_coder
from   quex.core_engine.generator.languages.address            import Address, get_label, get_address, get_label_of_address
from   quex.core_engine.generator.languages.variable_db        import variable_db
import quex.core_engine.state_machine.index                    as index
import quex.core_engine.state_machine.core                     as state_machine
import quex.core_engine.state_machine.compression.paths        as paths 
from   quex.core_engine.interval_handling                      import Interval
import quex.core_engine.utf8                                   as utf8  

from   quex.input.setup import setup as Setup

from   copy import deepcopy
import sys


LanguageDB = None # Set during call to 'do()', not earlier

def do(SMD, UniformOnlyF):
    """UniformOnlyF --> Accept only uniform states in path.
                        (This must be done by the 'analyzer module' too.)
    
       RETURNS: Array 'x'

       x[0] transition target definitions in terms of a 
            local variable database
       x[1] code for templates and state entries
       x[2] involved_state_index_list
    """
    assert isinstance(SMD, StateMachineDecorator)
          
    # (1) Find possible state combinations
    path_list = paths.do(SMD.sm(), UniformOnlyF)
    for path in path_list:
        involved_state_index_list = map(lambda info: info[0], path.sequence())

    # (2) Implement code for template combinations
    code, involved_state_index_list = _do(path_list, SMD, UniformOnlyF)

    if len(involved_state_index_list) != 0:
        variable_db.require("path_iterator")

    transition_block.format_this(code)

    return code, \
           involved_state_index_list

def _do(PathList, SMD, UniformOnlyF):
    """-- Returns generated code for all templates.
       -- Sets the template_compression_db in SMD.
    """
    global LanguageDB 

    assert type(PathList) == list
    assert isinstance(SMD, StateMachineDecorator)

    LanguageDB = Setup.language_db
    state_db   = SMD.sm().states
    SM_ID      = SMD.sm().get_id()

    def __equal(SkeletonA, SkeletonB):
        if len(SkeletonA) != len(SkeletonB): return False

        for key, trigger_set in SkeletonA.items():
            if SkeletonB.has_key(key) == False: return False
            if not trigger_set.is_equal(SkeletonB[key]): return False
        return True

    def __add_to_matching_path(path, path_db):
        assert isinstance(path, paths.CharacterPath)
        assert isinstance(path_db, dict)

        prototype_state = state_db[path.sequence()[0][0]]
        for index, path_list in path_db.items():
            # If uniformity is required, only such paths can be combined
            # where the states are uniform with each other. Assume that 
            # the states inside a path are 'uniform', so only one state
            # of each as to be checked.
            path_list_prototype_state = state_db[path_list[0].sequence()[0][0]] 
            if UniformOnlyF and not prototype_state.is_equivalent(path_list_prototype_state): 
                continue
                
            for candidate in path_list:
                # Compare the skeletons (remaining trigger maps)
                if __equal(path.skeleton(), candidate.skeleton()):
                    path_list.append(path)
                    return True
        return False

    # -- Sort the paths according their skeleton. Paths with the 
    #    same skeleton will use the same pathwalker.
    path_db                = {}
    for candidate in PathList:
        assert isinstance(candidate, paths.CharacterPath)
        # Is there a path with the same skeleton?
        if __add_to_matching_path(candidate, path_db): continue
        # If there is no equivalent path, then add a new 'prototype'
        path_walker_state_index = index.get()
        path_db[path_walker_state_index] = [ candidate ]

    # -- Create 'PathWalkerState' objects that can mimik state machine states.
    # -- Collect all indices of states involved in paths
    involved_state_index_list = set([])
    path_walker_list          = []
    for state_index, path_list in path_db.items():
        # Two Scenarios for settings at state entry (last_acceptance_position, ...)
        # 
        #   (i) All state entries are uniform: 
        #       -- Then, a representive state entry can be implemented at the 
        #          template entry. 
        #       -- Recursion happens to the template entry.
        #
        #   (ii) One or more state entry are different (non-uniform):
        #       -- The particularities of each state entry need to be implemented
        #          at state entry.
        #       -- Recursion is routed to entries of involved states.
        #      
        # The last state in sequence is the end target state, which cannot be 
        # addressed inside the pathwalker. It is the first state after the path.
        for path in path_list:
            involved_state_list = map(lambda info: info[0], path.sequence())
            involved_state_index_list.update(involved_state_list[:-1])

        # -- Determine if all involved states are uniform
        prototype = template_coder.get_uniform_prototype(SMD, involved_state_index_list)

        path_walker_list.append(PathWalkerState(path_list, SM_ID, state_index, prototype))

        for path in path_list:
            final_state_index = map(lambda info: info[0], path.sequence())[-1]
            # Allways be able to route to the end-state(?)

    # -- Generate code for:
    #      -- related variables: paths for pathwalkers
    #      -- state entries
    #      -- the pathwalkers
    code        = []
    router_code = []
    for path_walker in path_walker_list:
        __path_definition(path_walker, SMD) 
        if __state_entries(code, path_walker, SMD): 
            variable_db.require("path_end_state")
        __path_walker(code, path_walker, SMD)

    return code, involved_state_index_list

class PathWalkerState(state_machine.State):
    """Implementation of a Path Walker that is able to play the role of a state
       machine state. It is constructed on the basis of a CharacterPath object
       that is create by module
       
                state_machine.compression.paths

       Goal of this definition is to have a state that is able to comply the
       requirements of 'state_coder.core'. Thus, the path walker generation can
       rely on the same procedure as all state machine states.  
    """

    def __init__(self, PathList, StateMachineID, StateIndex, RepresentiveState):
        """Path contains all information about the states of a path and the
                path walker.
           
           PathList is the list of paths that use the same 'pathwalker', i.e.
                    they have the same skeleton trigger map.

           StateIndex is the state index that is assigned to the path walker.

           RepresentiveState is a state that can represent all states in
                             the path. If all states of a path are
                             equivalent, so any of them can do.

                             If == None, then it means that state entries
                             differ and there is no representive state.
        """
        assert type(PathList) == list
        assert isinstance(RepresentiveState, state_machine.State) or RepresentiveState == None
        assert type(StateIndex) == long

        # (0) Components required to be a 'State'
        if RepresentiveState != None:
            self.__uniform_state_entries_f = True
            core        = deepcopy(RepresentiveState.core())
            origin_list = deepcopy(RepresentiveState.origins())
        else:
            self.__uniform_state_entries_f = False
            # Empty core and origins, since the particularities are handled at individual 
            # state entries.
            core        = state_machine.StateCoreInfo(StateMachineID, StateIndex, 
                                                      AcceptanceF=False)   
            origin_list = state_machine.StateOriginList()          

        # All paths must have the same skeleton, so just use the first best: PathList[0]
        state_machine.State._set(self, core, origin_list, PathList[0].skeleton()) 

        state_machine.State.core(self).state_index = StateIndex

        # (1) Template related information
        self.__path_list = PathList

    def uniform_state_entries_f(self):
        return self.__uniform_state_entries_f

    def path_list(self):
        return self.__path_list

    def skeleton(self):
        # All skeletons must be the same, so the first one can do the job.
        return self.__path_list[0].skeleton()

def __path_definition(PathWalker, SMD):
    """Defines the transition targets for each involved state.
    """
    PathWalkerID = PathWalker.core().state_index
    PathList     = PathWalker.path_list()
    PathN        = len(PathList)

    def __get_state_list():
        result = []
        for path in PathList:
            Sequence = path.sequence()
            for state_index, dummy in Sequence[:-1]:
                result.append("QUEX_LABEL(%i), " % get_address("$entry", state_index, R=True, U=True))

            end_state_index = Sequence[-1][0]
            # If 'end_state_index' belongs to a non-implemented dead-end-state
            # => 'get_real_address()' returns address of immediately entered terminal
            end_state_label = "QUEX_LABEL(%i), " % get_address("$entry", end_state_index, R=True, U=True)
            result.append(end_state_label)
        return result

    memory       = ["\n"]
    memory_index = 0
    for path in PathList:
        Sequence = path.sequence()
        L        = len(Sequence)

        # Last element of sequence contains only the 'end state'.
        memory.append("    ")
        sequence_str = []
        for state_index, character in Sequence[:-1]:
            memory.append("%i, " % character)
            sequence_str.append(Interval(character).get_utf8_string())
        memory.append("QUEX_SETTING_PATH_TERMINATION_CODE, ")
        memory.append(LanguageDB["$comment"]("".join(sequence_str)) + "\n")

        variable_db.require("path_%i", 
                            Initial = "path_walker_%i_base + %i" % (PathWalkerID, memory_index), 
                            Index   = path.index())

        memory_index += L

    # (*) Path Walker Basis
    # The 'base' must be defined before all --> PriorityF (see table in variable_db)
    variable_db.require_array("path_walker_%i_base", 
                              ElementN = memory_index + 1,
                              Initial  = ["{"] + memory + ["\n    }"],
                              Index    = PathWalkerID)
    
    # (*) The State Information for each path step
    if not PathWalker.uniform_state_entries_f():
        state_list = __get_state_list()
        variable_db.require_array("path_walker_%i_state", 
                                  ElementN = len(state_list), 
                                  Initial  = ["{"] + state_list + ["}"], 
                                  Index    = PathWalkerID)

def __state_entries(txt, PathWalker, SMD):
    """Defines the entries of the path's states, so that the state key
       for the template is set, before the jump into the template. E.g.

            STATE_4711: 
               path_iterator = path_23 + 0; goto PATHWALKER_23;
            STATE_3123: 
               path_iterator = path_23 + 1; goto PATHWALKER_23;
            STATE_8912: 
               path_iterator = path_23 + 2; goto PATHWALKER_23;
    """
    sm = SMD.sm()

    PathN = len(PathWalker.path_list())
    require_path_end_state_variable_f = False
    txt.append("\n")
    for path in PathWalker.path_list():
        prev_state_index = None
        # Last state of sequence is not in the path, it is the first state after.
        for i, info in enumerate(path.sequence()[:-1]):
            state_index = info[0]
            # No need for state router if:
            #   (i) PathWalker is uniform, because then even after reload no dedicated
            #       state entry is required.
            #   (ii) The state is not entered from any other state except the predecessor
            #        on the path.
            # But:
            #   The first state always needs an entry.
            if prev_state_index != None:
                candidate = sm.get_only_entry_to_state(state_index)
                if PathWalker.uniform_state_entries_f() and prev_state_index == candidate:
                    prev_state_index = state_index
                    continue

            state = SMD.sm().states[state_index]

            entry_txt = []
            if PathWalker.uniform_state_entries_f():
                # If all state entries are uniform, the entry handling happens uniformly at
                # the entrance of the template, not each state.
                label_str = get_label("$entry", state_index) + ":\n"
                if state_index != SMD.sm().init_state_index:
                    label_str = "    __quex_assert_no_passage();\n" + label_str

                entry_txt.append(label_str)
                entry_txt.append("    ")
                entry_txt.append(LanguageDB["$debug-state"](state_index, SMD.forward_lexing_f()))
            else:
                entry_txt.extend(input_block.do(state_index, False, SMD))
                entry_txt.extend(acceptance_info.do(state, state_index, SMD, ForceSaveLastAcceptanceF=True))

            if PathWalker.uniform_state_entries_f() and PathN != 1:
                require_path_end_state_variable_f = True
                end_state_index = path.sequence()[-1][0]
                entry_txt.append("    path_end_state                 = QUEX_LABEL(%i);\n" \
                                 % get_address("$entry", end_state_index, U=True, R=True))
                
            entry_txt.append("    ")
            entry_txt.append(LanguageDB["$assignment"](
                                       "path_iterator                 ", 
                                       "path_%i + %i" % (path.index(), i)))
            entry_txt.append("goto %s;\n\n" % get_label_of_address(PathWalker.core().state_index, U=True))

            txt.append(Address("$entry", state_index, Code=entry_txt))
            prev_state_index = state_index

    return require_path_end_state_variable_f

def __path_walker(txt, PathWalker, SMD):
    """Generates the path walker, that walks along the character sequence.
    """
    PathList     = PathWalker.path_list()
    Skeleton     = PathList[0].skeleton()
    PathWalkerID = PathWalker.core().state_index

    if PathWalker.uniform_state_entries_f():
        # (1) Input Block (get the new character)
        txt.extend(input_block.do(PathWalkerID, False, SMD))
        # (2) Acceptance information/Store Input positions
        txt.extend(acceptance_info.do(PathWalker, PathWalkerID, SMD, ForceSaveLastAcceptanceF=True))

    else:
        txt.append("    __quex_assert_no_passage();\n")
        txt.append(get_label("$entry", PathWalkerID) + ":\n")
        txt.append("    __quex_debug(\"path walker %i\");\n" % PathWalkerID)

    # (3) Transition Map

    # (3.1) The comparison with the path's current character
    #       If terminating zero is reached, the path's end state is entered.
    if PathWalker.uniform_state_entries_f():
        next_state = [ "goto %s;\n" % get_label_of_address(PathWalkerID, U=True) ]
        end_state = __end_state_router(PathWalker, SMD)
    else:
        next_state = [ __state_router(PathWalker, SMD) ]
        end_state  = ["        "] + next_state

    txt.append("    ")
    txt.append(LanguageDB["$if =="]("*path_iterator"))
    txt.append("        ")
    txt.append(LanguageDB["$increment"]("path_iterator"))
    txt.append("\n")
    txt.append("        ")
    txt.extend(next_state)
    txt.append("    ")
    txt.append(LanguageDB["$elseif"] \
               + LanguageDB["$=="]("*path_iterator", "QUEX_SETTING_PATH_TERMINATION_CODE") \
               + LanguageDB["$then"])
    txt.extend(end_state)
    txt.append("    ")
    txt.append(LanguageDB["$endif"])
    txt.append("\n")

    # (3.2) Transition map of the 'skeleton'        
    trigger_map = PathWalker.transitions().get_trigger_map()
    if len(trigger_map) == 0:
        # (This happens, for example, if there are only keywords and no 
        #  'overlaying' identifier pattern.)

        # Even if the skeleton/trigger map is empty there must be something
        # that catches the 'buffer limit code'. 
        # => Define an 'all drop out' trigger_map and then,
        # => Adapt the trigger map, so that the 'buffer limit' is an 
        #    isolated single interval.
        trigger_map = [ (Interval(-sys.maxint, sys.maxint), None) ]

    state_index_str = None
    if not PathWalker.uniform_state_entries_f():
        state_index_str = "path_walker_%i_state[path_iterator - path_walker_%i_base]" % (PathWalkerID, PathWalkerID)

    txt.extend(transition_block.do(trigger_map, PathWalkerID, SMD, ReturnToState_Str=state_index_str))

    # (4) The drop out (nothing matched)
    #     (Path iterator has not been increased yet)

    txt.extend(drop_out.do(PathWalker, PathWalkerID, SMD))

    return 

def __state_router(PathWalker, SMD):
    """Create code that allows to jump to a state based on the path_iterator.

       NOTE: Paths cannot be recursive. Also, path transitions are linear, i.e.
             target states are either subsequent path states or the path
             is left. 

             The current state is identified by the 'path_iterator'

             (1) determine to what path the path_iterator belongs.
             (2) 'path_iterator - path_begin' gives an integer that identifies
                 the particular state of the path.

       NOTE: In the case of non-uniform path state elements, the state router
             takes care of the detection of the end-state, thus it has not
             to be determined in the '*path_iterator == PTC' section.
    """
    assert not PathWalker.uniform_state_entries_f()

    PathWalkerID = PathWalker.core().state_index

    # Make sure that the state router is implemented, add reference:
    get_label("$state-router", U=True)
    return "QUEX_GOTO_STATE(path_walker_%i_state[path_iterator - path_walker_%i_base]);\n" % (PathWalkerID, PathWalkerID)

def __end_state_router(PathWalker, SMD):
    """After the last transition of the path, transit into the 'end state',
       i.e. the first state after the path. If the pathwalker contains multiple
       path, this might include state routing.  
    """
    assert PathWalker.uniform_state_entries_f()

    PathList     = PathWalker.path_list()
    PathN        = len(PathList)

    txt = []
    txt.append("        ")
    txt.append(LanguageDB["$input/decrement"] + "\n")
    txt.append("\n        ")

    # -- Transition to the first state after the path:
    if PathN == 1:
        # (i) There is only one path for the pathwalker, then there is only
        #     one terminal and it is determined at compilation time.
        txt.append(transition.get_transition_to_state(PathList[0].end_state_index()))
    else:
        # (ii) There are multiple paths for the pathwalker, then the terminal
        #      must be determined at run time.
        #   -- At the end of the path, path_iterator == path_end, thus we can identify
        #      the path by comparing simply against all path_ends.
        
        get_label("$state-router", U=True) # Make sure, that state router is referenced
        txt.append("QUEX_GOTO_STATE(path_end_state);")

    txt.append("\n")
    txt.append("    ")
    return txt

def __switch_case_state_router(txt, SMD, PathWalker, StateIndexList=None):
    PathWalkerID = PathWalker.core().state_index
    
    txt.append("            ")
    value_txt = "(int)(path_iterator - path_walker_%i_base)" % PathWalkerID
    memory_index = 0
    case_code_list = []
    for path in PathWalker.path_list():
        for info in path.sequence():
            if StateIndexList == None or info[0] in StateIndexList:
                case_code_list.append((memory_index, 
                                       transition.get_transition_to_state(info[0], SMD)))
            memory_index += 1

    txt.extend(LanguageDB["$switch-block"](value_txt, case_code_list))
    txt.append("QUEX_ERROR_EXIT(\"Pathwalker: path_iterator on inadmissible position.\");\n")

def __path_specific_action(txt, PathList, get_comparison, get_action):
    PathN = len(PathList)

    first_f = True
    for path in PathList:
        # if path_iterator >= path[i].begin and path_iterator < path[i].end:
        #      action of action_list[i]
        #    }
        sequence   = path.sequence()
        path_index = path.index()
        txt.append("        ")
        if PathN != 1:
            if first_f: 
                first_f = False
                txt.append(LanguageDB["$if"])
            else:
                txt.append(LanguageDB["$elseif"])

            # The comparison to identify the path 
            get_comparison(txt, path.index())

            txt.append(LanguageDB["$then"])
        
        # Enter the path specific action
        get_action(txt, path)

    if PathN != 1:
        txt.append("        ")
        txt.append(LanguageDB["$endif-else"])
        txt.append("        QUEX_ERROR_EXIT(\"Pathwalker: path_iterator on in admissible position.\");\n")
        txt.append("        ")
        txt.append(LanguageDB["$endif"])
    return

