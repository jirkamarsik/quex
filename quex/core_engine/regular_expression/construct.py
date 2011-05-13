from   quex.core_engine.state_machine.core                    import SideInfo
from   quex.core_engine.interval_handling                     import UnicodeInterval, Interval
import quex.core_engine.state_machine.character_counter       as character_counter
import quex.core_engine.state_machine.setup_post_context      as setup_post_context
import quex.core_engine.state_machine.setup_pre_context       as setup_pre_context
import quex.core_engine.state_machine.setup_border_conditions as setup_border_conditions
#
import quex.core_engine.state_machine.nfa_to_dfa              as nfa_to_dfa
import quex.core_engine.state_machine.hopcroft_minimization   as hopcroft
#
from   quex.input.setup                                       import setup as Setup
from   quex.frs_py.file_in  import *


def do(core_sm, 
       begin_of_line_f=False, pre_context=None, 
       end_of_line_f=False,   post_context=None, 
       fh=-1, 
       DOS_CarriageReturnNewlineF=True, 
       AllowNothingIsNecessaryF=False):

    assert type(begin_of_line_f) == bool
    assert type(end_of_line_f) == bool
    assert type(DOS_CarriageReturnNewlineF) == bool
    assert type(AllowNothingIsNecessaryF) == bool

    # Detect orphan states in the 'raw' state machines --> error in sm-building
    for sm in [pre_context, core_sm, post_context]:
        __detect_initial_orphaned_states(sm, fh)

    # Delete state transitions on signal characters (such as 'buffer limit code')
    # and cut ranges outside the unicode interval.
    for sm in [pre_context, core_sm, post_context]:
        __delete_forbidden_transitions(sm, fh)

    # Now, possibly new orphan states evolved. This must be, at least, a warning.
    # But, in any case they can be cut out without loss.
    for sm in [pre_context, core_sm, post_context]:
        __delete_orphaned_states(sm, fh)

    # Detect the 'Nothing is Necessary' error in a pattern.
    # (*) 'Nothing is necessary' cannot be accepted. See the discussion in the 
    #     module "quex.core_engine.generator.core.py"
    if not AllowNothingIsNecessaryF:
        post_context_f = (post_context != None)
        __detect_path_of_nothing_is_necessary(pre_context,  "pre context",  post_context_f, fh)
        __detect_path_of_nothing_is_necessary(core_sm,      "core pattern", post_context_f, fh)
        __detect_path_of_nothing_is_necessary(post_context, "post context", post_context_f, fh)

    # Determine newline and character count for matching lexemes
    # of the core pattern.
    newline_n    = character_counter.get_newline_n(core_sm)
    character_n  = character_counter.get_character_n(core_sm)

    side_info    = SideInfo(newline_n, character_n)

    if   pre_context == None and post_context == None:
        result = core_sm
        # -- can't get more beautiful ...
    
    elif pre_context == None and post_context != None:
        result = setup_post_context.do(core_sm, post_context, fh=fh)
        result = beautify(result)

    elif pre_context != None and post_context == None:
        result = setup_pre_context.do(core_sm, pre_context)
        result = beautify(result)

    elif pre_context != None and post_context != None:
        # NOTE: pre-condition needs to be setup **after** post condition, because
        #       post condition deletes all origins!
        #       (is this still so? 07y7m6d fschaef)
        result = setup_post_context.do(core_sm, post_context, fh=fh)
        result = setup_pre_context.do(result, pre_context)
        result = beautify(result)

    # -- set begin of line/end of line conditions
    if begin_of_line_f or end_of_line_f: 
        result = setup_border_conditions.do(result, begin_of_line_f, end_of_line_f,
                                            DOS_CarriageReturnNewlineF)
        result = beautify(result)

    result.side_info = side_info

    return __validate(result, fh)

def beautify(the_state_machine):
    ## assert the_state_machine.get_orphaned_state_index_list() == [], \
    ##       "before conversion to DFA: orphaned states " + repr(the_state_machine)
    result = nfa_to_dfa.do(the_state_machine)
    ## assert the_state_machine.get_orphaned_state_index_list() == [], \
    ##       "after conversion to DFA: orphaned states " + repr(the_state_machine)
    result = hopcroft.do(result, CreateNewStateMachineF=False)
    ## assert the_state_machine.get_orphaned_state_index_list() == [], \
    ##       "after hopcroft minimization: orphaned states " + repr(the_state_machine)

    return result
  
def __detect_initial_orphaned_states(sm, fh):

    if sm == None: return

    if sm.has_orphaned_states() == False: return

    error_msg("Orphaned state(s) detected in regular expression (optimization lack).\n" + \
              "Please, log a defect at the projects website quex.sourceforge.net.\n"    + \
              "Orphan state(s) = " + repr(sm.get_orphan_state_list()), 
              fh, DontExitF=True)

def __detect_path_of_nothing_is_necessary(sm, Name, PostContextPresentF, fh):
    assert Name in ["core pattern", "pre context", "post context"]

    if sm == None: return

    msg = "The %s contains in a 'nothing is necessary' path in the state machine.\n"   \
          % Name                                                                     + \
          "This means, that without reading a character the analyzer drops into\n"   + \
          "an acceptance state. "

    init_state = sm.get_init_state()

    if not init_state.core().is_acceptance(): return

    msg += { 
        "core pattern":
            "The analyzer would then stall.",

        "pre context":
            "E.g., pattern 'x*/y/' means that zero or more 'x' are a pre-\n"             + \
            "condition for 'y'. If zero appearances of 'x' are enough, then obviously\n" + \
            "there is no pre-condition for 'y'! Most likely the author intended 'x+/y/'.",

        "post context":
            "A post context where nothing is necessary is superfluous.",
    }[Name]

    if Name != "post context" and PostContextPresentF:
        msg += "\n"                                                          \
               "Note: A post context does not change anything to that fact." 

    error_msg(msg, fh)

def __delete_forbidden_transitions(sm, fh):
    # !! Let the orphaned state check NOT happen before this, because states
    # !! may become orphan in the frame of the following procedure.
    if sm == None: return

    # (*) The buffer limit code has to appear absolutely nowhere!
    if Setup.buffer_limit_code != -1: __delete_forbidden_character(sm, Setup.buffer_limit_code)
    if Setup.path_limit_code != -1:   __delete_forbidden_character(sm, Setup.path_limit_code)

    # (*) Delete transitions that make practically no sense
    __delete_forbidden_ranges(sm, fh)

def __delete_forbidden_character(sm, BLC):
    """The buffer limit code is something that **needs** to cause a drop out.
       In the drop out handling, the buffer is reloaded.

       Critical character is allowed at end of post context.

       NOTE: This operation might result in orphaned states that have to 
             be deleted.
    """
    for state in sm.states.values():
        for target_state_index, trigger_set in state.transitions().get_map().items():

            if trigger_set.contains(BLC):
                trigger_set.cut_interval(Interval(BLC, BLC+1))

            # If the operation resulted in cutting the path to the target state, then delete it.
            if trigger_set.is_empty():
                state.transitions().delete_transitions_to_target(target_state_index)

def __delete_forbidden_ranges(sm, fh):
    """Unicode does define all code points >= 0. Thus there can be no code points
       below zero as it might result from some number set operations.

       NOTE: This operation might result in orphaned states that have to 
             be deleted.
    """
    global Setup

    character_value_limit = Setup.get_character_value_limit()
    for state in sm.states.values():

        for target_state_index, trigger_set in state.transitions().get_map().items():

            # Make sure, all transitions lie inside the unicode code range 
            if trigger_set.minimum() < UnicodeInterval.begin or trigger_set.supremum() >= UnicodeInterval.end:
                trigger_set.intersect_with(UnicodeInterval)

            if trigger_set.supremum() > character_value_limit:
                error_msg("Pattern contains character beyond the scope of the buffer element size (%s)\n" \
                          % Setup.get_character_value_limit_str() + \
                          "Please, cut the character range of the regular expression,\n"
                          "adapt \"--buffer-element-size\" or \"--buffer-element-type\",\n"       + \
                          "or specify '--buffer-element-size-irrelevant' to ignore the issue.", fh)

            if Setup.buffer_codec in ["utf16-le", "utf16-be"]:
                # Delete the forbidden interval: D800-DFFF
                if trigger_set.has_intersection(ForbiddenRange):
                    error_msg("Pattern contains characters in unicode range 0xD800-0xDFFF.\n"
                              "This range is not covered by UTF16. Cutting Interval.", fh, DontExitF=True)
                    trigger_set.cut_interval(ForbiddenRange)
            
            # If the operation resulted in cutting the path to the target state, then delete it.
            if trigger_set.is_empty():
                state.transitions().delete_transitions_to_target(target_state_index)

def __delete_orphaned_states(sm, fh):
    if sm == None: return

    new_orhpan_state_list = sm.get_orphaned_state_index_list()
    if new_orhpan_state_list == []: return

    error_msg("Pattern contained solely forbidden characters in a state transition.\n"
              "The resulting target state is deleted since no other state triggered to it.", 
              fh, DontExitF=True, WarningF=True)

    for state_index in new_orhpan_state_list:
        del sm.states[state_index]


def __validate(sm, fh):
    # Anything produced by the parser must contain side information about
    assert sm == None or sm.side_info != None, \
           "Missing side info in " + repr(sm)

    # (*) It is essential that state machines defined as patterns do not 
    #     have origins.
    if sm.has_origins():
        error_msg("Regular expression parsing resulted in state machine with origins.\n" + \
                  "Please, log a defect at the projects website quex.sourceforge.net.\n", fh)

    # (*) Acceptance states shall not store the input position when they are 'normally'
    #     post-conditioned. Post-conditioning via the backward search is a different 
    #     ball-game.
    acceptance_f = False
    for state in sm.states.values():
        if state.core().is_acceptance(): acceptance_f = True

        if     state.core().is_end_of_post_contexted_core_pattern() \
           and state.core().is_acceptance():
            error_msg("Pattern with post-context: An irregularity occurred.\n" + \
                      "(end of normal post-contexted core pattern is an acceptance state)\n" 
                      "Please, log a defect at the projects website quex.sourceforge.net.", fh)

    if acceptance_f == False:
        error_msg("Pattern has no acceptance state and can never match.\n" + \
                  "Aborting generation process.", fh)
        
    return sm

