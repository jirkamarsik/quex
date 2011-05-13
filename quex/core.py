from copy import copy
import os
import sys

from   quex.frs_py.file_in import error_msg, write_safely_and_close, open_file_or_die

from   quex.input.setup                         import setup as Setup
import quex.output.cpp.source_package           as source_package
import quex.lexer_mode                          as lexer_mode

import quex.consistency_check                   as consistency_check
import quex.core_engine.generator.core          as     generator
import quex.core_engine.generator.state_coder.indentation_counter as indentation_counter
from   quex.core_engine.generator.action_info   import PatternActionInfo, \
                                                       UserCodeFragment_straighten_open_line_pragmas, \
                                                       CodeFragment
import quex.input.quex_file_parser              as quex_file_parser
import quex.output.cpp.token_id_maker           as token_id_maker
import quex.output.cpp.token_class_maker        as token_class_maker
import quex.output.cpp.core                     as quex_class_out
import quex.output.cpp.action_code_formatter    as action_code_formatter
import quex.output.cpp.codec_converter_helper   as codec_converter_helper 
import quex.output.cpp.mode_classes             as mode_classes
import quex.output.graphviz.interface           as plot_generator

def do():
    """Generates state machines for all modes. Each mode results into 
       a separate state machine that is stuck into a virtual function
       of a class derived from class 'quex_mode'.
    """
    token_id_maker.prepare_default_standard_token_ids()

    mode_db = __get_mode_db(Setup)

    IndentationSupportF = lexer_mode.requires_indentation_count(mode_db)
    BeginOfLineSupportF = lexer_mode.requires_begin_of_line_condition_support(mode_db)

    # (*) Implement the 'quex' core class from a template
    # -- do the coding of the class framework
    header_engine_txt,           \
    constructor_and_memento_txt, \
    header_configuration_txt     = quex_class_out.do(mode_db, IndentationSupportF, 
                                                     BeginOfLineSupportF)

    mode_implementation_txt  = mode_classes.do(mode_db)

    # (*) Generate the token ids
    #     (This needs to happen after the parsing of mode_db, since during that
    #      the token_id_db is developped.)
    token_id_maker.do(Setup, IndentationSupportF) 
    map_id_to_name_function_implementation_txt = token_id_maker.do_map_id_to_name_function()

    # (*) [Optional] Make a customized token class
    token_class_h, token_class_txt = token_class_maker.do()
    
    # (*) [Optional] Generate a converter helper
    codec_converter_helper.do()

    # (*) implement the lexer mode-specific analyser functions
    inheritance_info_str = ""
    analyzer_code        = ""

    # (*) Get list of modes that are actually implemented
    #     (abstract modes only serve as common base)
    mode_list      = filter(lambda mode: mode.options["inheritable"] != "only", mode_db.values())
    mode_name_list = map(lambda mode: mode.name, mode_list)

    for mode in mode_list:        

        # accumulate inheritance information for comment
        code = get_code_for_mode(mode, mode_name_list, IndentationSupportF, BeginOfLineSupportF) 
        analyzer_code += code

        if Setup.comment_mode_patterns_f:
            inheritance_info_str += mode.get_documentation()

    # Bring the info about the patterns first
    if Setup.comment_mode_patterns_f:
        analyzer_code += Setup.language_db["$ml-comment"]("BEGIN: MODE PATTERNS\n" + \
                                                          inheritance_info_str     + \
                                                          "\nEND: MODE PATTERNS")
        analyzer_code += "\n" # For safety: New content may have to start in a newline, e.g. "#ifdef ..."

    # generate frame for analyser code
    analyzer_code = generator.frame_this(analyzer_code)

    # Implementation (Potential Inline Functions)
    implemtation_txt =   constructor_and_memento_txt + "\n" \
                       + token_class_txt             + "\n" 

    # Engine (Source Code)
    source_txt =   mode_implementation_txt                    + "\n" \
                 + analyzer_code                              + "\n" \
                 + map_id_to_name_function_implementation_txt + "\n" 

    # (*) Write Files
    write_safely_and_close(Setup.output_configuration_file, header_configuration_txt)
    if Setup.language == "C":
        write_safely_and_close(Setup.output_header_file, header_engine_txt)
        write_safely_and_close(Setup.output_code_file, 
                               source_txt + implemtation_txt)
    else:
        header_txt = header_engine_txt.replace("$$ADDITIONAL_HEADER_CONTENT$$", implemtation_txt)
        write_safely_and_close(Setup.output_header_file, header_txt)
        write_safely_and_close(Setup.output_code_file, source_txt)

    if token_class_h != "":
        write_safely_and_close(lexer_mode.token_type_definition.get_file_name(), 
                               token_class_h)

    UserCodeFragment_straighten_open_line_pragmas(Setup.output_header_file, "C")
    UserCodeFragment_straighten_open_line_pragmas(Setup.output_code_file, "C")

    # assert lexer_mode.token_type_definition != None
    UserCodeFragment_straighten_open_line_pragmas(lexer_mode.token_type_definition.get_file_name(), "C")

    if Setup.source_package_directory != "":
        source_package.do()

def __prepare_end_of_stream_action(Mode, IndentationSupportF):
    if not Mode.has_code_fragment_list("on_end_of_stream"):
        # We cannot make any assumptions about the token class, i.e. whether
        # it can take a lexeme or not. Thus, no passing of lexeme here.
        txt  = "self_send(__QUEX_SETTING_TOKEN_ID_TERMINATION);\n"
        txt += "RETURN;\n"

        Mode.set_code_fragment_list("on_end_of_stream", CodeFragment(txt))

    if IndentationSupportF:
        if Mode.default_indentation_handler_sufficient():
            code = "QUEX_NAME(on_indentation)(me, /*Indentation*/0, LexemeNull);\n"
        else:
            code = "QUEX_NAME(%s_on_indentation)(me, /*Indentation*/0, LexemeNull);\n" % Mode.name

        code_fragment = CodeFragment(code)
        Mode.insert_code_fragment_at_front("on_end_of_stream", code_fragment)

    # RETURNS: end_of_stream_action, db 
    return action_code_formatter.do(Mode, Mode.get_code_fragment_list("on_end_of_stream"), 
                                    "on_end_of_stream", None, EOF_ActionF=True)

def __prepare_on_failure_action(Mode):
    if not Mode.has_code_fragment_list("on_failure"):
        txt  = "QUEX_ERROR_EXIT(\"\\n    Match failure in mode '%s'.\\n\"\n" % Mode.name 
        txt += "                \"    No 'on_failure' section provided for this mode.\\n\"\n"
        txt += "                \"    Proposal: Define 'on_failure' and analyze 'Lexeme'.\\n\");\n"
        Mode.set_code_fragment_list("on_failure", CodeFragment(txt))

    # RETURNS: on_failure_action, db 
    return action_code_formatter.do(Mode, Mode.get_code_fragment_list("on_failure"), 
                                    "on_failure", None, Default_ActionF=True) 

def get_code_for_mode(Mode, ModeNameList, IndentationSupportF, BeginOfLineSupportF):
    required_local_variables_db = {}
   
    # -- some modes only define event handlers that are inherited
    if len(Mode.get_pattern_action_pair_list()) == 0: return "", ""

    # -- 'end of stream' action
    end_of_stream_action, db = __prepare_end_of_stream_action(Mode, IndentationSupportF)
    required_local_variables_db.update(db)

    # -- 'on failure' action (on the event that nothing matched)
    on_failure_action, db = __prepare_on_failure_action(Mode)
    required_local_variables_db.update(db)

    # -- adapt pattern-action pair information so that it can be treated
    #    by the code generator.
    pattern_action_pair_list, db = get_generator_input(Mode, IndentationSupportF)
    required_local_variables_db.update(db)

    analyzer_code = generator.do(pattern_action_pair_list, 
                                 OnFailureAction                = PatternActionInfo(None, on_failure_action), 
                                 EndOfStreamAction              = PatternActionInfo(None, end_of_stream_action),
                                 StateMachineName               = Mode.name,
                                 AnalyserStateClassName         = Setup.analyzer_class_name,
                                 StandAloneAnalyserF            = False, 
                                 QuexEngineHeaderDefinitionFile = Setup.output_header_file,
                                 ModeNameList                   = ModeNameList,
                                 RequiredLocalVariablesDB       = required_local_variables_db, 
                                 SupportBeginOfLineF            = BeginOfLineSupportF)

    return "".join(analyzer_code)

def __get_indentation_counter_terminal_index(PatterActionPairList):
    """Under some circumstances a terminal code need to jump to the indentation
       counter directly. Thus, it must be known in what terminal it is actually 
       located.

        RETURNS: None, if no indentation counter is involved.
                 > 0,  terminal id of the terminal that contains the indentation
                       counter.
    """
    for info in PatterActionPairList:
        action = info.action()
        if   action.__class__.__name__ != "GeneratedCode": continue
        elif action.function != indentation_counter.do:    continue
        return info.pattern_state_machine().get_id()
    return None

def get_generator_input(Mode, IndentationSupportF):
    """The module 'quex.core_engine.generator.core' produces the code for the 
       state machine. However, it requires a certain data format. This function
       adapts the mode information to this format. Additional code is added 

       -- for counting newlines and column numbers. This happens inside
          the function ACTION_ENTRY().
       -- (optional) for a virtual function call 'on_action_entry()'.
       -- (optional) for debug output that tells the line number and column number.
    """
    assert isinstance(Mode, lexer_mode.Mode)
    variable_db              = {}
    pattern_action_pair_list = Mode.get_pattern_action_pair_list()

    indentation_counter_terminal_id = __get_indentation_counter_terminal_index(pattern_action_pair_list)

    # Assume pattern-action pairs (matches) are sorted and their pattern state
    # machine ids reflect the sequence of pattern precedence.

    for pattern_info in pattern_action_pair_list:
        safe_pattern_str      = pattern_info.pattern.replace("\"", "\\\"")
        pattern_state_machine = pattern_info.pattern_state_machine()

        # Prepare the action code for the analyzer engine. For this purpose several things
        # are be added to the user's code.
        action                      = pattern_info.action()
        self_line_column_counting_f = False

        # Generated code fragments may rely on some information about the generator
        if hasattr(action, "data") and type(action.data) == dict:   
            action.data["indentation_counter_terminal_id"] = indentation_counter_terminal_id

        prepared_action, db = action_code_formatter.do(Mode, action, safe_pattern_str,
                                                       pattern_state_machine, 
                                                       SelfCountingActionF=self_line_column_counting_f)
        variable_db.update(db)

        pattern_info.set_action(prepared_action)
    
    return pattern_action_pair_list, variable_db

def __get_post_context_n(match_info_list):
    n = 0
    for info in MatchInfoList:
        if info.pattern_state_machine().core().post_context_id() != -1L:
            n += 1
    return n

def do_plot():

    mode_db             = __get_mode_db(Setup)
    IndentationSupportF = lexer_mode.requires_indentation_count(mode_db)

    for mode in mode_db.values():        
        # -- some modes only define event handlers that are inherited
        if len(mode.get_pattern_action_pair_list()) == 0: continue

        # -- adapt pattern-action pair information so that it can be treated
        #    by the code generator.
        pattern_action_pair_list, variable_db = get_generator_input(mode, IndentationSupportF)

        plotter = plot_generator.Generator(pattern_action_pair_list, 
                                           StateMachineName = mode.name,
                                           GraphicFormat    = Setup.plot_graphic_format)
        plotter.do(Option=Setup.plot_character_display)

def __get_mode_db(Setup):
    # (0) check basic assumptions
    if Setup.input_mode_files == []: error_msg("No input files.")
    
    # (1) input: do the pattern analysis, in case exact counting of newlines is required
    #            (this might speed up the lexer, but nobody might care ...)
    #            pattern_db = analyse_patterns.do(pattern_file)    
    mode_description_db = quex_file_parser.do(Setup.input_mode_files)

    # (*) Translate each mode description int a 'real' mode
    for mode_name, mode_descr in mode_description_db.items():
        lexer_mode.mode_db[mode_name] = lexer_mode.Mode(mode_descr)

    # (*) perform consistency check 
    consistency_check.do(lexer_mode.mode_db)

    return lexer_mode.mode_db

#########################################################################################
# Allow to check wether the exception handlers are all in place
def _exception_checker():
    if       len(sys.argv) != 3: return
    elif     sys.argv[1] != "<<TEST:Exceptions/function>>" \
         and sys.argv[1] != "<<TEST:Exceptions/on-import>>":   return

    exception = sys.argv[2]
    if   exception == "KeyboardInterrupt": raise KeyboardInterrupt()
    elif exception == "AssertionError":    raise AssertionError()
    elif exception == "Exception":         raise Exception()

# Double check wether exception handlers are in place:
if len(sys.argv) == 3 and sys.argv[1] == "<<TEST:Exceptions/on-import>>":
    _exception_checker()

