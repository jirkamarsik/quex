from quex.frs_py.file_in         import is_identifier_start, is_identifier_continue
from quex.frs_py.string_handling import blue_print

import quex.core_engine.state_machine.index as index
from quex.core_engine.generator.languages.address     import *
from quex.core_engine.generator.languages.variable_db import variable_db
from quex.core_engine.interval_handling               import NumberSet
from copy     import copy
from operator import itemgetter
#

def __nice(SM_ID): 
    return repr(SM_ID).replace("L", "")

#________________________________________________________________________________
# C++
#

__header_definitions_txt = """
#include <quex/code_base/analyzer/member/basic>
#include <quex/code_base/buffer/Buffer>
#ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE
#   include <quex/code_base/token/TokenQueue>
#endif

#ifdef    CONTINUE
#   undef CONTINUE
#endif
#define   CONTINUE goto $$GOTO_START_PREPARATION$$; 

#ifdef    RETURN
#   undef RETURN
#endif

#if defined(QUEX_OPTION_TOKEN_POLICY_QUEUE)
#   define RETURN   return
#else
#   define RETURN   do { return __self_result_token_id; } while(0)
#endif
"""

def __header_definitions(LanguageDB):

    txt = __header_definitions_txt
    txt = txt.replace("$$GOTO_START_PREPARATION$$", get_label("$re-start", U=True))
    return txt

def __local_variable_definitions(VariableDB):
    if len(VariableDB) == 0: return ""

    def __group_by_condition(VariableDB):
        result = {}
        for variable in VariableDB.itervalues():

            variable_list = result.get(variable.condition)
            if variable_list == None: 
                variable_list              = [[], []]
                result[variable.condition] = variable_list

            if not variable.condition_negated_f: variable_list[0].append(variable)
            else:                                variable_list[1].append(variable)

        return result

    def __code(txt, variable):
        variable_type = variable.variable_type
        variable_init = variable.initial_value
        variable_name = variable.name

        if variable.element_n != None: 
            if variable.element_n != 0:
                variable_name += "[%s]" % repr(variable.element_n)
                if variable_type.find("QUEX_TYPE_GOTO_LABEL") != -1: 
                    variable_name = "(" + variable_name + ")"
            else:
                variable_type += "*"
                variable_init  = ["0x0"]

        if variable_init == None: 
            value = ["/* un-initilized */"]
        else:
            if type(variable_init) != list: variable_init = [ variable_init ]
            value = [" = "] + variable_init

        txt.append("    %s%s %s%s" % \
                   (variable_type, 
                    " " * (30-len(variable_type)), variable_name, 
                    " " * (30 - len(variable_name))))
        txt.extend(value)
        txt.append(";\n")

    # L   = max(map(lambda info: len(info[0]), VariableDB.keys()))
    txt       = []
    done_list = []
    for raw_name, variable in sorted(VariableDB.items()):
        if variable.priority_f == False: continue

        if variable.condition != None:
            if variable.condition_negated_f == False: 
                txt.append("#   ifdef %s\n"  % variable.condition)
            else:
                txt.append("#   ifndef %s\n" %  variable.condition)

        __code(txt, variable)

        if variable.condition != None:
            txt.append("#   endif /* %s */\n" % variable.condition)

        del VariableDB[variable.name]

    grouped_variable_list = __group_by_condition(VariableDB)
    unconditioned_name_set = set([])
    for condition, groups in sorted(grouped_variable_list.iteritems()):
        if condition != None: continue
        for variable in groups[0]:
            unconditioned_name_set.add(variable.name)

    for condition, groups in sorted(grouped_variable_list.iteritems()):

        condition_group, negated_condition_group = groups

        if condition == None:
            for variable in condition_group:
                __code(txt, variable)
        else:
            if len(condition_group) != 0:
                txt.append("#   ifdef %s\n"  % condition)

                for variable in condition_group:
                    if variable.name in unconditioned_name_set: continue
                    __code(txt, variable)

            if len(negated_condition_group) != 0:
                if len(condition_group) != 0: txt.append("#   else /* not %s */\n" % condition)
                else:                         txt.append("#   ifndef %s\n"         % condition)

                for variable in negated_condition_group:
                    if variable.name in unconditioned_name_set: continue
                    __code(txt, variable)

            txt.append("#   endif /* %s */\n" % condition)
            
    return txt
         
__function_signature = """
__QUEX_TYPE_ANALYZER_RETURN_VALUE  
QUEX_NAME($$STATE_MACHINE_NAME$$_analyzer_function)(QUEX_TYPE_ANALYZER* me) 
{
    /* NOTE: Different modes correspond to different analyzer functions. The analyzer  
             functions are all located inside the main class as static functions. That  
             means, they are something like 'globals'. They receive a pointer to the   
             lexical analyzer, since static member do not have access to the 'this' pointer.
     */
#   if defined(QUEX_OPTION_TOKEN_POLICY_SINGLE)
    register QUEX_TYPE_TOKEN_ID __self_result_token_id 
           = (QUEX_TYPE_TOKEN_ID)__QUEX_SETTING_TOKEN_ID_UNINITIALIZED;
#   endif
#   ifdef     self
#       undef self
#   endif
#   define self (*((QUEX_TYPE_ANALYZER*)me))
"""

reload_forward_str = """
    __quex_assert_no_passage();
__RELOAD_FORWARD:
    __quex_debug("__RELOAD_FORWARD");

    __quex_assert(input == QUEX_SETTING_BUFFER_LIMIT_CODE);
    if( me->buffer._memory._end_of_file_p == 0x0 ) {
        __quex_debug_reload_before();
        QUEX_NAME(buffer_reload_forward_LA_PC)(&me->buffer, &last_acceptance_input_position,
                                               post_context_start_position, PostContextStartPositionN);
        __quex_debug_reload_after();
        QUEX_GOTO_STATE(target_state_index);
    }
    __quex_debug("reload impossible");
    QUEX_GOTO_STATE(target_state_else_index);
"""

reload_init_state_forward_str = """
    __quex_assert_no_passage();
__RELOAD_INIT_STATE:
    __quex_debug("__RELOAD_INIT_STATE");

    __quex_assert(input == QUEX_SETTING_BUFFER_LIMIT_CODE);
    if( me->buffer._memory._end_of_file_p == 0x0 ) {
        __quex_debug_reload_before();
        QUEX_NAME(buffer_reload_forward_LA_PC)(&me->buffer, &last_acceptance_input_position,
                                               post_context_start_position, PostContextStartPositionN);
        __quex_debug_reload_after();
        goto $$INIT_STATE$$; /* Init state entry */
    }
    goto $$END_OF_STREAM$$;  /* End of stream    */
"""

reload_backward_str = """
    __quex_assert_no_passage();
__RELOAD_BACKWARD:
    __quex_debug("__RELOAD_BACKWARD");
    __quex_assert(input == QUEX_SETTING_BUFFER_LIMIT_CODE);
    if( QUEX_NAME(Buffer_is_begin_of_file)(&me->buffer) == false ) {
        __quex_debug_reload_before();
        QUEX_NAME(buffer_reload_backward)(&me->buffer);
        __quex_debug_reload_after();
        QUEX_GOTO_STATE(target_state_index);
    }
    __quex_debug("reload impossible");
    QUEX_GOTO_STATE(target_state_else_index);
"""

comment_on_post_context_position_init_str = """
    /* Post context positions do not have to be reset or initialized. If a state
     * is reached which is associated with 'end of post context' it is clear what
     * post context is meant. This results from the ways the state machine is 
     * constructed. A post context positions live time looks like the following:
     *
     * (1)   unitialized (don't care)
     * (1.b) on buffer reload it may, or may not be adapted (don't care)
     * (2)   when a post context begin state is passed, the it is **SET** (now: take care)
     * (2.b) on buffer reload it **is adapted**.
     * (3)   when a terminal state of the post context is reached (which can only be reached
     *       for that particular post context, then the post context position is used
     *       to reset the input position.                                              */
"""

def __reload_definitions(InitialStateIndex):
    txt = []
    txt.append(Address("$reload-FORWARD", None, reload_forward_str))
    txt.append(blue_print(reload_init_state_forward_str,
                          [["$$INIT_STATE$$",    get_label("$entry", InitialStateIndex, U=True)],
                           ["$$END_OF_STREAM$$", get_label("$terminal-EOF", U=True)]]))
    # Append empty references to make sure that the addresses are implemented.
    txt.append(Address("$reload-BACKWARD", None, reload_backward_str))
    return txt

def __local_variable_definition(PostContextID_List, PreContextID_List, LanguageDB):
    PostContextN = len(PostContextID_List)

    variable_db.require("last_acceptance", 
                        Initial="QUEX_LABEL(%i)" % get_address("$terminal-FAILURE"))
    variable_db.require("last_acceptance_input_position") 
    variable_db.require_array("post_context_start_position",    
                              ElementN = PostContextN, 
                              Initial  = "{ " + ("0, " * (PostContextN - 1) + "0") + "}")
    variable_db.require("PostContextStartPositionN", 
                        Initial = "(size_t)" + repr(PostContextN))
    variable_db.require("input") 
              
    # -- pre-condition fulfillment flags                
    for sm_id in PreContextID_List:
        variable_db.require("pre_context_%i_fulfilled_f", Index = sm_id)

    return LanguageDB["$local-variable-defs"](variable_db.get())

def __analyzer_function(StateMachineName, EngineClassName, StandAloneEngineF,
                        variable_definitions, function_body, ModeNameList=[], LanguageDB=None):
    """EngineClassName = name of the structure that contains the engine state.
                         if a mode of a complete quex environment is created, this
                         is the mode name. otherwise, any name can be chosen. 
       StandAloneEngineF = False if a mode for a quex engine is to be created. True
                           if a stand-alone lexical engine is required (without the
                           complete mode-handling framework of quex).
    """              
    txt = [
            "#include <quex/code_base/temporary_macros_on>\n",
            __function_signature.replace("$$STATE_MACHINE_NAME$$", StateMachineName),
    ]

    txt.extend(variable_definitions)

    if not StandAloneEngineF: 
        L = max(map(lambda name: len(name), ModeNameList))
        for name in ModeNameList:
            txt.append("#   define %s%s    (QUEX_NAME(%s))\n" % (name, " " * (L- len(name)), name))

    txt.extend([
        comment_on_post_context_position_init_str,
        "#   if    defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE) \\\n",
        "       || defined(QUEX_OPTION_ASSERTS)\n",
        "    me->DEBUG_analyzer_function_at_entry = me->current_analyzer_function;\n",
        "#   endif\n",
    ])

    txt.append(get_label("$start") + ":\n")

    # -- entry to the actual function body
    txt.append("    " + LanguageDB["$mark-lexeme-start"] + "\n")
    txt.append("    QUEX_LEXEME_TERMINATING_ZERO_UNDO(&me->buffer);\n")
    
    txt.extend(function_body)

    # -- prevent the warning 'unused variable'
    txt.append( 
        "\n"                                                                                              \
        "    /* Prevent compiler warning 'unused variable': use variables once in a part of the code*/\n" \
        "    /* that is never reached (and deleted by the compiler anyway).*/\n")

    # Mode Names are defined as macros, so the following is not necessary.
    # for mode_name in ModeNameList:
    #    txt.append("    (void)%s;\n" % mode_name)

    txt.append(                                                             \
        "    (void)QUEX_NAME(LexemeNullObject);\n"                          \
        "    (void)QUEX_NAME_TOKEN(DumpedTokenIdObject);\n"                 \
        "    QUEX_ERROR_EXIT(\"Unreachable code has been reached.\\n\");\n") 

    ## This was once we did not know ... if there was a goto to the initial state or not.
    ## txt += "        goto %s;\n" % label.get(StateMachineName, InitialStateIndex)
    if not StandAloneEngineF: 
        L = max(map(lambda name: len(name), ModeNameList))
        for name in ModeNameList:
            txt.append("#   undef %s\n" % name)

    txt.append("#   undef self\n")
    txt.append("}\n")

    txt.append("#include <quex/code_base/temporary_macros_off>\n")
    return txt

__terminal_router_prolog_str = """
#   if defined(QUEX_OPTION_COMPUTED_GOTOS)
    __quex_assert_no_passage();
    /* Scenario: -- QUEX_GOTO_TERMINAL(last_acceptance) defined
     *              => required __TERMINAL_ROUTER
     *           -- all last_acceptance are 'failure' 
     *              => no routing.
     *           -- Compilation with 'QUEX_OPTION_COMPUTED_GOTOS'.
     *              => no state router required.                     
     * Then: There is no 'goto' to __TERMINAL_ROUTER and the compiler
     *       would complain about an unreferenced label. Avoid this by
     *       putting an explicit, never reached 'goto' here.               */
    goto __TERMINAL_ROUTER;
#   endif
    __quex_assert_no_passage();
__TERMINAL_ROUTER:
    __quex_debug("terminal router");
    /*  if last_acceptance => goto correspondent acceptance terminal state */
    /*  else               => execute defaul action                        */
    if( last_acceptance == $$TERMINAL_FAILURE-REF$$ ) {
        goto $$TERMINAL_FAILURE$$; /* TERMINAL: FAILURE */
    }
    /* When a terminal router is used, the terminal is determined dynamically,
     * thus the last_acceptance_input_position **must** be set. 
     * Exception: Template States, where acceptance states of post conditions
     *            do not set the acceptance position (because its retrieved
     *            anyway from post_context_start_position[i]).               */
    if(last_acceptance_input_position != 0x0) {
        $$RESTORE_LAST_ACCEPTANCE_POS$$
    }
#   ifdef  QUEX_OPTION_COMPUTED_GOTOS
    goto *last_acceptance;
#   else
    target_state_index = last_acceptance;
    goto """

__terminal_router_epilog_str = """
#   endif /* QUEX_OPTION_COMPUTED_GOTOS */
"""
__terminal_state_prolog  = """
    /* (*) Terminal states _______________________________________________________
     *
     * States that implement actions of the 'winner patterns.                     */

    /* Lexeme setup: 
     *
     * There is a temporary zero stored at the end of each lexeme, if the action 
     * references to the 'Lexeme'. 'LexemeNull' provides a reference to an empty
     * zero terminated string.                                                    */

#if defined(QUEX_OPTION_ASSERTS)
#   define Lexeme       QUEX_NAME(access_Lexeme)((const char*)__FILE__, (size_t)__LINE__, &me->buffer)
#   define LexemeBegin  QUEX_NAME(access_Lexeme)((const char*)__FILE__, (size_t)__LINE__, &me->buffer)
#   define LexemeL      QUEX_NAME(access_LexemeL)((const char*)__FILE__, (size_t)__LINE__, &me->buffer)
#   define LexemeEnd    QUEX_NAME(access_LexemeEnd)((const char*)__FILE__, (size_t)__LINE__, &me->buffer)
#else
#   define Lexeme       (me->buffer._lexeme_start_p)
#   define LexemeBegin  (me->buffer._lexeme_start_p)
#   define LexemeL      ((size_t)(me->buffer._input_p - me->buffer._lexeme_start_p))
#   define LexemeEnd    (me->buffer._input_p)
#endif

#define LexemeNull      (&QUEX_NAME(LexemeNullObject))
"""

__terminal_state_epilog = """
$$TERMINAL_END_OF_STREAM-DEF$$: /* TERMINAL: END_OF_STREAM */
$$END_OF_STREAM_ACTION$$
     /* End of Stream causes a return from the lexical analyzer, so that no
      * tokens can be filled after the termination token.                    */
     RETURN;          

$$TERMINAL_FAILURE-DEF$$: /* TERMINAL: FAILURE */
$$FAILURE_ACTION$$
     goto $$GOTO_START_PREPARATION$$;

#undef Lexeme
#undef LexemeBegin
#undef LexemeEnd
#undef LexemeNull
#undef LexemeL
"""


__on_continue_reentry_preparation_str = """
$$REENTRY_PREPARATION$$:
    /* (*) Common point for **restarting** lexical analysis.
     *     at each time when CONTINUE is called at the end of a pattern. */
    
#   ifndef __QUEX_OPTION_PLAIN_ANALYZER_OBJECT
#   ifdef  QUEX_OPTION_TOKEN_POLICY_QUEUE
    if( QUEX_NAME(TokenQueue_is_full)(&self._token_queue) ) RETURN;
#   else
    if( self_token_get_id() != __QUEX_SETTING_TOKEN_ID_UNINITIALIZED) RETURN;
#   endif
#   endif

    last_acceptance = $$TERMINAL_FAILURE-REF$$; /* TERMINAL: FAILURE */
$$DELETE_PRE_CONDITION_FULLFILLED_FLAGS$$
$$COMMENT_ON_POST_CONTEXT_INITIALIZATION$$
    /*  If a mode change happened, then the function must first return and
     *  indicate that another mode function is to be called. At this point, 
     *  we to force a 'return' on a mode change. 
     *
     *  Pseudo Code: if( previous_mode != current_mode ) {
     *                   return 0;
     *               }
     *
     *  When the analyzer returns, the caller function has to watch if a mode change
     *  occured. If not it can call this function again.                               */
#   if    defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE) \
       || defined(QUEX_OPTION_ASSERTS)
    if( me->DEBUG_analyzer_function_at_entry != me->current_analyzer_function ) 
#   endif
    { 
#       if defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE)
        self_token_set_id(__QUEX_SETTING_TOKEN_ID_UNINITIALIZED);
        RETURN;
#       elif defined(QUEX_OPTION_ASSERTS)
        QUEX_ERROR_EXIT("Mode change without immediate return from the lexical analyzer.");
#       endif
    }

    goto $$GOTO_START$$;
"""

def __adorn_action_code(action_info, SMD, SupportBeginOfLineF): 

    result = action_info.action().get_code()
    assert type(result) != tuple
    code_str = result

    if code_str == "": return ""

    txt = "\n"
    # TODO: There could be a differenciation between a pattern that contains
    #       newline at the end, and those that do not. Then, there need not
    #       be a conditional question.
    if SupportBeginOfLineF:
        txt += "    me->buffer._character_before_lexeme_start = *(me->buffer._input_p - 1);\n"

    if action_info.action().require_terminating_zero_f():
        txt += "    QUEX_LEXEME_TERMINATING_ZERO_SET(&me->buffer);\n"

    txt += code_str

    return txt

def get_terminal_code(state_machine_id, SMD, pattern_action_info, SupportBeginOfLineF, LanguageDB):
    state_machine                  = SMD.sm()
    DirectlyReachedTerminalID_List = SMD.directly_reached_terminal_id_list()

    state_machine_id_str = __nice(state_machine_id)
    state_machine        = pattern_action_info.pattern_state_machine()
    #
    action_code = __adorn_action_code(pattern_action_info, SMD, SupportBeginOfLineF)
        
    # (*) The 'normal' terminal state can also be reached by the terminal
    #     router and, thus, **must** restore the acceptance input position. This is so, 
    #     because when the 'goto last_acceptance' is triggered the 'last_acceptance'
    #     may lay backwards and needs to be restored.
    safe_pattern = pattern_action_info.pattern.replace('"', 'double-quote')
    safe_pattern = safe_pattern.replace("\\n", "\\\\n")
    safe_pattern = safe_pattern.replace("\\t", "\\\\t")
    safe_pattern = safe_pattern.replace("\\r", "\\\\r")
    safe_pattern = safe_pattern.replace("\\a", "\\\\a")
    safe_pattern = safe_pattern.replace("\\v", "\\\\v")
    txt = [
            Address("$terminal", state_machine_id,
                      "%s:\n" % get_label("$terminal", state_machine_id)                                \
                    + "    __quex_debug(\"pre-terminal %i: %s\");\n" % (state_machine_id, safe_pattern) \
                    + "    " + LanguageDB["$input/increment"] + "\n"),
            Address("$terminal-direct", state_machine_id), 
            "    __quex_debug(\"* terminal %i:   %s\");\n" % (state_machine_id, safe_pattern),
    ]

    # (1) Retrieving the input position for the next run
    #     -- Terminal states can be reached directly, so that the input position
    #        is already set correctly, or via the terminal router because the
    #        acceptance was 'trailing'. Example two patterns A:'for' and B:'forest'.
    #        If the input is 'for' than the pattern A triggers acceptance, but
    #        the lexer still continue trying for B. If the input is 'fortune', 
    #        then the input position must be after 'for' because B was not matched.
    #        The right terminal is reached via the terminal router, and the
    #        terminal router also resets the input position to 'last_acceptance_position'.
    if state_machine.core().post_context_backward_input_position_detector_sm() != None:
        # Pseudo Ambiguous Post Contexts:
        # -- require that the end of the core pattern is to be searched! One 
        #    cannot simply restore some stored input position.
        # -- The pseudo-ambiguous post condition is translated into a 'normal'
        #    pattern. However, after a match a backward detection of the end
        #    of the core pattern is done. Here, we first need to go to the point
        #    where the 'normal' pattern ended, then we can do a backward detection.
        txt.append("    PAPC_input_postion_backward_detector_%s(me);\n" % \
                   __nice(state_machine.core().post_context_backward_input_position_detector_sm_id()))

    elif state_machine.core().post_context_id() != -1L: 
        post_condition_index = SMD.get_post_context_index(state_machine_id)
        # Post Contexted Patterns:
        # -- have a dedicated register from where they store the end of the core pattern.
        txt.append("    __quex_debug(\"post context %s: reset position\");\n" % __nice(state_machine_id))
        variable = "post_context_start_position[%s]" % __nice(post_condition_index) 
        txt.append("    " + LanguageDB["$input/seek_position"](variable))
        txt.append("\n")

    else:
        # Normal Acceptance:
        pass

    # -- paste the action code that corresponds to the pattern   
    txt.append(action_code)
    txt.append("\n")
    txt.append("    ")
    txt.append("goto %s;\n" % get_label("$re-start", U=True))

    return txt

def __terminal_on_failure_prolog(LanguageDB):
    return [
        "me->buffer._input_p = me->buffer._lexeme_start_p;\n",
        LanguageDB["$if"], LanguageDB["$EOF"], LanguageDB["$then"], "\n",
        "    ", LanguageDB["$comment"]("Next increment will stop on EOF character."), "\n",
        LanguageDB["$endif"], "\n",
        LanguageDB["$else"], "\n",
        "    ", LanguageDB["$comment"]("Step over nomatching character"), "\n",
        "    ", LanguageDB["$input/increment"], "\n",
        LanguageDB["$endif"], "\n",
    ]

def __terminal_states(SMD, action_db, OnFailureAction, EndOfStreamAction, 
                      SupportBeginOfLineF, PreConditionIDList, LanguageDB):
    """NOTE: During backward-lexing, for a pre-condition, there is not need for terminal
             states, since only the flag 'pre-condition fulfilled is raised.
    """      
    assert SMD.__class__.__name__ == "StateMachineDecorator"
    sm = SMD.sm()
    PostConditionedStateMachineID_List = SMD.post_contexted_sm_id_list()
    DirectlyReachedTerminalID_List     = SMD.directly_reached_terminal_id_list()

    # (*) specific terminal states of patterns (entered from acceptance states)
    specific_terminal_states = []
    for state_machine_id, pattern_action_info in action_db.items():
        code = get_terminal_code(state_machine_id, SMD, pattern_action_info, SupportBeginOfLineF, LanguageDB)

        specific_terminal_states.extend(code)

    # If there is at least a single terminal, the the 're-entry' preparation must be accomplished
    if len(action_db) != 0: get_label("$re-start", U=True)

    # (*) preparation of the reentry without return:
    #     delete all pre-condition fullfilled flags
    delete_pre_context_flags = []
    for pre_context_sm_id in PreConditionIDList:
        delete_pre_context_flags.append("    ")
        delete_pre_context_flags.append(LanguageDB["$assignment"]("pre_context_%s_fulfilled_f" % __nice(pre_context_sm_id), 0))

    #  -- execute 'on_failure' pattern action 
    #  -- goto initial state    
    end_of_stream_code_action_str = __adorn_action_code(EndOfStreamAction, SMD, SupportBeginOfLineF)

    # -- FAILURE ACTION: Under 'normal' circumstances the on_failure action is simply to be executed
    #                    since the 'get_forward()' incremented the 'current' pointer.
    #                    HOWEVER, when end of file has been reached the 'current' pointer has to
    #                    be reset so that the initial state can drop out on the buffer limit code
    #                    and then transit to the end of file action.
    # NOTE: It is possible that 'miss' happens after a chain of characters appeared. In any case the input
    #       pointer must be setup right after the lexeme start. This way, the lexer becomes a new chance as
    #       soon as possible.
    on_failure = __terminal_on_failure_prolog(LanguageDB)
    msg        = __adorn_action_code(OnFailureAction, SMD, SupportBeginOfLineF)

    on_failure.append(msg)

    if PreConditionIDList == []: precondition_involved_f = "0"
    else:                        precondition_involved_f = "1"

    prolog = __terminal_state_prolog  

    router = Address("$terminal-router", None,
                  [
                      blue_print(__terminal_router_prolog_str,
                      [
                       ["$$RESTORE_LAST_ACCEPTANCE_POS$$",  LanguageDB["$input/seek_position"]("last_acceptance_input_position")],
                       ["$$TERMINAL_FAILURE-REF$$",         "QUEX_LABEL(%i)" % get_address("$terminal-FAILURE")],
                       ["$$TERMINAL_FAILURE$$",             get_label("$terminal-FAILURE")],
                      ]),
                      # DO NOT 'U=True' for the state router. This is done automatically if 
                      # 'goto reload' is used. 
                      get_label("$state-router"), ";",
                      __terminal_router_epilog_str, 
                  ])
                     
    epilog = blue_print(__terminal_state_epilog, 
             [
              ["$$FAILURE_ACTION$$",             "".join(on_failure)],
              ["$$END_OF_STREAM_ACTION$$",       end_of_stream_code_action_str],
              ["$$TERMINAL_END_OF_STREAM-DEF$$", get_label("$terminal-EOF")],
              ["$$TERMINAL_FAILURE-DEF$$",       get_label("$terminal-FAILURE")],
              ["$$STATE_MACHINE_NAME$$",         SMD.name()],
              ["$$GOTO_START_PREPARATION$$",     get_label("$re-start", U=True)],
             ])

    reentry_preparation = blue_print(__on_continue_reentry_preparation_str,
                          [["$$REENTRY_PREPARATION$$",                    get_label("$re-start")],
                           ["$$DELETE_PRE_CONDITION_FULLFILLED_FLAGS$$",  "".join(delete_pre_context_flags)],
                           ["$$GOTO_START$$",                             get_label("$start", U=True)],
                           ["$$COMMENT_ON_POST_CONTEXT_INITIALIZATION$$", comment_on_post_context_position_init_str],
                           ["$$TERMINAL_FAILURE-REF$$",                   "QUEX_LABEL(%i)" % get_address("$terminal-FAILURE")],
                          ])

    txt = []
    txt.append(router)
    txt.append(prolog)
    txt.extend(specific_terminal_states)
    txt.append(epilog)
    txt.append(reentry_preparation)

    return txt
    
def __frame_of_all(Code, Setup):
    LanguageDB = Setup.language_db
    namespace_open  = LanguageDB["$namespace-open"](Setup.analyzer_name_space)
    namespace_close = LanguageDB["$namespace-close"](Setup.analyzer_name_space)
    # namespace_ref   = LanguageDB["$namespace-ref"](Setup.analyzer_name_space)
    # if len(namespace_ref) > 2 and namespace_ref[:2] == "::":  namespace_ref = namespace_ref[2:]
    # if len(namespace_ref) > 2 and namespace_ref[-2:] == "::": namespace_ref = namespace_ref[:-2]
    # "using namespace " + namespace_ref + ";\n"       + \

    implementation_header_str = ""
    if Setup.language == "C":
        implementation_header_str += "#if defined(__QUEX_OPTION_CONVERTER_HELPER)\n"
        implementation_header_str += "#   include \"%s\"\n" % Setup.get_file_reference(Setup.output_buffer_codec_header_i)
        implementation_header_str += "#endif\n"
        implementation_header_str += "#include <quex/code_base/analyzer/headers.i>\n"
        implementation_header_str += "#include <quex/code_base/analyzer/C-adaptions.h>\n"

    return "".join(["/* #include \"%s\"*/\n" % Setup.get_file_reference(Setup.output_header_file),
                    implementation_header_str,
                    "QUEX_NAMESPACE_MAIN_OPEN\n",
                    "QUEX_TYPE_CHARACTER  QUEX_NAME(LexemeNullObject) = (QUEX_TYPE_CHARACTER)0;\n",
                    Code,
                    "QUEX_NAMESPACE_MAIN_CLOSE\n"])                     

def __get_if_in_character_set(ValueList):
    assert type(ValueList) == list
    assert len(ValueList) > 0
    txt = "if( "
    for value in ValueList:
        txt += "input == %i || " % value

    txt = txt[:-3] + ") {\n"
    return txt

def __get_if_in_interval(TriggerSet):
    assert TriggerSet.__class__.__name__ == "Interval"
    assert TriggerSet.size() >= 2

    if TriggerSet.size() == 2:
        return "if( input == %i || input == %i ) {\n" % (TriggerSet.begin, TriggerSet.end - 1)
    else:
        return "if( input >= %i && input < %i ) {\n" % (TriggerSet.begin, TriggerSet.end)

def __require_terminating_zero_preparation(LanguageDB, CodeStr):
    CommentDelimiterList = LanguageDB["$comment-delimiters"]
    assert type(CommentDelimiterList) == list
    ObjectName = "Lexeme"

    for delimiter_info in CommentDelimiterList:
        assert type(delimiter_info) == list, "Argument 'CommentDelimiters' must be of type [[]]"
        assert len(delimiter_info) == 3, \
               "Elements of argument CommentDelimiters must be arrays with three elements:\n" + \
               "start of comment, end of comment, replacement string for comment.\n" + \
               "received: " + repr(delimiter_info)

    txt = CodeStr
    L       = len(txt)
    LO      = len(ObjectName)
    found_i = -1
    while 1 + 1 == 2:
        # TODO: Implement the skip_whitespace() function for more general treatment of Comment
        #       delimiters. Quotes for strings '"" shall then also be treate like comments.
        found_i = txt.find(ObjectName, found_i + 1)

        if found_i == -1: return False

        # Note: The variable must be named 'exactly' like the given name. 'xLexeme' or 'Lexemey'
        #       shall not trigger a treatment of 'Lexeme'.
        if     (found_i == 0      or not is_identifier_start(txt[found_i - 1]))     \
           and (found_i == L - LO or not is_identifier_continue(txt[found_i + LO])): 
               return True

def __condition(txt, CharSet):
    first_f = True
    for interval in CharSet.get_intervals(PromiseToTreatWellF=True):
        if first_f: first_f = False
        else:       txt.append(" || ")

        if interval.end - interval.begin == 1:
            txt.append("(C) == 0x%X"                % interval.begin)
        elif interval.end - interval.begin == 2:
            txt.append("(C) == 0x%X || (C) == 0x%X" % (interval.begin, interval.end - 1))
        else:
            txt.append("(C) <= 0x%X && (C) < 0x%X" % (interval.begin, interval.end))

def __indentation_add(Info):
    # (0) If all involved counts are single spaces, the 'counting' can be done
    #     easily by subtracting 'end - begin', no adaption.
    indent_txt = " " * 16
    if Info.has_only_single_spaces():
        return ""

    def __do(txt, CharSet, Operation):
        txt.append(indent_txt + "if( ")
        __condition(txt, CharSet)
        txt.append(" ) { ")
        txt.append(Operation)
        txt.append(" }\\\n")

    txt       = []
    spaces_db = {} # Sort same space counts together
    grid_db   = {} # Sort same grid counts together
    for name, count_parameter in Info.count_db.items():
        count         = count_parameter.get()
        character_set = Info.character_set_db[name].get()
        if count == "bad": continue
        # grid counts are indicated by negative integer for count.
        if count >= 0:
            spaces_db.setdefault(count, NumberSet()).unite_with(character_set)
        else:
            grid_db.setdefault(count, NumberSet()).unite_with(character_set)

    for count, character_set in spaces_db.items():
        __do(txt, character_set, "(I) += %i;" % count)

    for count, character_set in grid_db.items():
        __do(txt, character_set, "(I) += (%i - ((I) %% %i));" % (abs(count), abs(count)))

    return "".join(txt)

def __indentation_check_whitespace(Info):
    all_character_list = map(lambda x: x.get(), Info.character_set_db.values())
    assert len(all_character_list) != 0

    number_set = all_character_list[0]
    for character_set in all_character_list[1:]:
        number_set.unite_with(character_set)

    txt = []
    __condition(txt, number_set)
    return "".join(txt)

def __get_switch_block(VariableName, CaseCodePairList):
    txt = [0, "switch( %s ) {\n" % VariableName]
    next_i = 0
    L = len(CaseCodePairList)
    CaseCodePairList.sort(key=itemgetter(0))
    for case, code in CaseCodePairList: 
        next_i += 1
        txt.append(1)
        case_label = "0x%X" % case
        txt.append("case %s: " % case_label)
        txt.append(" " * (7 - len(case_label)))
        if next_i != L and CaseCodePairList[next_i][1] == code:
            txt.append("\n")
        else:
            if type(code) == list: txt.extend(code)
            else:                  txt.append(code)
            txt.append("\n")
            
    txt.append(0)
    txt.append("}\n")
    return txt


