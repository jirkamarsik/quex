#! /usr/bin/env python
import os
from   copy import copy
import time

from   quex.frs_py.string_handling import blue_print
from   quex.frs_py.file_in         import get_file_content_or_die, \
                                          get_include_guard_extension, \
                                          make_safe_identifier

from   quex.DEFINITIONS import QUEX_PATH, QUEX_VERSION
import quex.lexer_mode  as     lexer_mode
from   quex.input.setup import setup as Setup
from   quex.input.setup import get_file_reference

def do(ModeDB, IndentationSupportF, BeginOfLineSupportF):
    assert lexer_mode.token_type_definition != None

    header_engine_txt, code_engine_txt = write_engine_header(ModeDB)
    header_configuration_txt           = write_configuration_header(ModeDB, 
                                                                    IndentationSupportF, 
                                                                    BeginOfLineSupportF)

    return header_engine_txt, code_engine_txt, header_configuration_txt

def write_configuration_header(ModeDB, IndentationSupportF, BeginOfLineSupportF):
    LexerClassName = Setup.analyzer_class_name
    LanguageDB     = Setup.language_db

    ConfigurationTemplateFile =(  QUEX_PATH \
                                + Setup.language_db["$code_base"] \
                                + "/analyzer/configuration/TXT").replace("//","/")

    txt = get_file_content_or_die(ConfigurationTemplateFile)

    # -- check if exit/entry handlers have to be active
    entry_handler_active_f = False
    exit_handler_active_f = False
    for mode in ModeDB.values():
        if mode.get_code_fragment_list("on_entry") != []: entry_handler_active_f = True
        if mode.get_code_fragment_list("on_exit") != []:  exit_handler_active_f = True

    # Buffer filler converter (0x0 means: no buffer filler converter)
    converter_f = False
    converter_new_str = "#   define QUEX_SETTING_BUFFER_FILLERS_CONVERTER_NEW " 
    if Setup.converter_user_new_func != "": 
        converter_new_str += Setup.converter_user_new_func + "()"
        user_defined_converter_f = True
    else: 
        converter_new_str = "/* " + converter_new_str + " */"
        user_defined_converter_f = False

    # Token repetition support
    token_repeat_test_txt = ""
    for token_id_str in lexer_mode.token_repetition_token_id_list:
        token_repeat_test_txt += "TokenID == %s || " % token_id_str
    if token_repeat_test_txt != "":
        token_repeat_test_txt = token_repeat_test_txt[:-3]
    else:
        token_repeat_test_txt = "false"

    txt = __switch(txt, "QUEX_OPTION_COLUMN_NUMBER_COUNTING",        Setup.count_column_number_f)        
    txt = __switch(txt, "QUEX_OPTION_COMPUTED_GOTOS",                False)
    txt = __switch(txt, "QUEX_OPTION_CONVERTER_ICONV",               Setup.converter_iconv_f)
    txt = __switch(txt, "QUEX_OPTION_CONVERTER_ICU",                 Setup.converter_icu_f)
    txt = __switch(txt, "QUEX_OPTION_INCLUDE_STACK",                 Setup.include_stack_support_f)
    txt = __switch(txt, "QUEX_OPTION_LINE_NUMBER_COUNTING",          Setup.count_line_number_f)      
    txt = __switch(txt, "QUEX_OPTION_POST_CATEGORIZER",              Setup.post_categorizer_f)
    txt = __switch(txt, "QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK", Setup.mode_transition_check_f)
    txt = __switch(txt, "QUEX_OPTION_STRING_ACCUMULATOR",            Setup.string_accumulator_f)
    txt = __switch(txt, "QUEX_OPTION_TOKEN_POLICY_QUEUE",            Setup.token_policy == "queue")
    txt = __switch(txt, "QUEX_OPTION_TOKEN_POLICY_SINGLE",           Setup.token_policy == "single")
    txt = __switch(txt, "QUEX_OPTION_TOKEN_REPETITION_SUPPORT",      token_repeat_test_txt != "false")
    txt = __switch(txt, "QUEX_OPTION_USER_MANAGED_TOKEN_MEMORY",     Setup.token_memory_management_by_user_f)
    txt = __switch(txt, "__QUEX_OPTION_BIG_ENDIAN",                  Setup.buffer_byte_order == "big")
    txt = __switch(txt, "__QUEX_OPTION_CONVERTER_HELPER",            Setup.converter_helper_required_f)
    txt = __switch(txt, "__QUEX_OPTION_CONVERTER",                   Setup.converter_f)
    txt = __switch(txt, "QUEX_OPTION_INDENTATION_TRIGGER",           IndentationSupportF)     
    txt = __switch(txt, "__QUEX_OPTION_LITTLE_ENDIAN",               Setup.buffer_byte_order == "little")
    txt = __switch(txt, "__QUEX_OPTION_ON_ENTRY_HANDLER_PRESENT",    entry_handler_active_f)
    txt = __switch(txt, "__QUEX_OPTION_ON_EXIT_HANDLER_PRESENT",     exit_handler_active_f)
    txt = __switch(txt, "__QUEX_OPTION_PLAIN_C",                     Setup.language.upper() == "C")
    txt = __switch(txt, "__QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION", BeginOfLineSupportF)
    txt = __switch(txt, "__QUEX_OPTION_SYSTEM_ENDIAN",               Setup.byte_order_is_that_of_current_system_f)
    txt = __switch(txt, "QUEX_OPTION_BUFFER_BASED_ANALYZIS",         Setup.buffer_based_analyzis_f)

    # -- token class related definitions
    token_descr = lexer_mode.token_type_definition
    namespace_token_str = make_safe_identifier(Setup.language_db["$namespace-ref"](token_descr.name_space))

    # -- name of the character codec
    codec_name = "unicode"
    if Setup.buffer_codec != "": 
        codec_name = make_safe_identifier(Setup.buffer_codec).lower()

    def namespace(NameSpaceList):
        result = Setup.language_db["$namespace-ref"](NameSpaceList)

        if result == "::": return ""

        assert len(result) > 2, \
               "Error while generating namespace reference '%s'" % result

        return result[:-2]

    txt = blue_print(txt, 
            [
             ["$$BUFFER_LIMIT_CODE$$",          "0x%X" % Setup.buffer_limit_code],
             ["$$CODEC_NAME$$",                 codec_name],
             ["$$INCLUDE_GUARD_EXTENSION$$",    get_include_guard_extension( Setup.language_db["$namespace-ref"](Setup.analyzer_name_space) + "__" + Setup.analyzer_class_name)],
             ["$$INITIAL_LEXER_MODE_ID$$",      "QUEX_NAME(ModeID_%s)" % lexer_mode.initial_mode.get_pure_code()],
             ["$$LEXER_BUILD_DATE$$",           time.asctime()],
             ["$$LEXER_CLASS_NAME$$",           LexerClassName],
             ["$$LEXER_CLASS_NAME_SAFE$$",      Setup.analyzer_name_safe],
             ["$$LEXER_DERIVED_CLASS_NAME$$",   Setup.analyzer_derived_class_name],
             ["$$MAX_MODE_CLASS_N$$",           repr(len(ModeDB))],
             ["$$NAMESPACE_MAIN$$",             namespace(Setup.analyzer_name_space)],
             ["$$NAMESPACE_MAIN_CLOSE$$",       Setup.language_db["$namespace-close"](Setup.analyzer_name_space).replace("\n", "\\\n")],
             ["$$NAMESPACE_MAIN_OPEN$$",        Setup.language_db["$namespace-open"](Setup.analyzer_name_space).replace("\n", "\\\n")],
             ["$$NAMESPACE_TOKEN$$",            namespace(token_descr.name_space)],
             ["$$NAMESPACE_TOKEN_CLOSE$$",      Setup.language_db["$namespace-close"](token_descr.name_space).replace("\n", "\\\n")],
             ["$$NAMESPACE_TOKEN_OPEN$$",       Setup.language_db["$namespace-open"](token_descr.name_space).replace("\n", "\\\n")],
             ["$$PATH_TERMINATION_CODE$$",      "0x%X" % Setup.path_limit_code],
             ["$$QUEX_SETTING_BUFFER_FILLERS_CONVERTER_NEW$$", converter_new_str],
             ["$$QUEX_TYPE_CHARACTER$$",        Setup.buffer_element_type],
             ["$$QUEX_VERSION$$",               QUEX_VERSION],
             ["$$TOKEN_CLASS$$",                token_descr.class_name],
             ["$$TOKEN_CLASS_NAME_SAFE$$",      token_descr.class_name_safe],
             ["$$TOKEN_COLUMN_N_TYPE$$",        token_descr.column_number_type.get_pure_code()],
             ["$$TOKEN_ID_TYPE$$",              token_descr.token_id_type.get_pure_code()],
             ["$$TOKEN_LINE_N_TYPE$$",          token_descr.line_number_type.get_pure_code()],
             ["$$TOKEN_PREFIX$$",               Setup.token_id_prefix],
             ["$$TOKEN_QUEUE_SAFETY_BORDER$$",  repr(Setup.token_queue_safety_border)],
             ["$$TOKEN_QUEUE_SIZE$$",           repr(Setup.token_queue_size)],
             ["$$TOKEN_REPEAT_TEST$$",          token_repeat_test_txt],
             ["$$USER_LEXER_VERSION$$",         Setup.user_application_version_id],
             ])

    return txt

def __switch(txt, Name, SwitchF):
    if SwitchF: txt = txt.replace("$$SWITCH$$ %s" % Name, "#define    %s" % Name)
    else:       txt = txt.replace("$$SWITCH$$ %s" % Name, "/* #define %s */" % Name)
    return txt
    
def write_constructor_and_memento_functions(ModeDB):

    FileTemplate = os.path.normpath(QUEX_PATH
                                    + Setup.language_db["$code_base"] 
                                    + "/analyzer/TXT-Cpp.i")
    func_txt = get_file_content_or_die(FileTemplate)

    func_txt = blue_print(func_txt,
            [
                ["$$CONSTRUCTOR_EXTENSTION$$",                  lexer_mode.class_constructor_extension.get_code()],
                ["$$CONVERTER_HELPER_I$$",                      get_file_reference(Setup.output_buffer_codec_header_i)],
                ["$$CONSTRUCTOR_MODE_DB_INITIALIZATION_CODE$$", get_constructor_code(ModeDB.values())],
                ["$$MEMENTO_EXTENSIONS_PACK$$",                 lexer_mode.memento_pack_extension.get_code()],
                ["$$MEMENTO_EXTENSIONS_UNPACK$$",               lexer_mode.memento_unpack_extension.get_code()],
                ])
    return func_txt

def write_engine_header(ModeDB):

    QuexClassHeaderFileTemplate = os.path.normpath(  QUEX_PATH
                                                   + Setup.language_db["$code_base"] 
                                                   + Setup.language_db["$analyzer_template_file"]).replace("//","/")
    LexerFileStem  = Setup.output_header_file
    LexerClassName = Setup.analyzer_class_name

    quex_converter_coding_name_str = Setup.converter_ucs_coding_name

    mode_id_definition_str = "" 
    # NOTE: First mode-id needs to be '1' for compatibility with flex generated engines
    for i, info in enumerate(ModeDB.items()):
        name = info[0]
        mode = info[1]
        if mode.options["inheritable"] == "only": continue
        mode_id_definition_str += "    QUEX_NAME(ModeID_%s) = %i,\n" % (name, i)

    if mode_id_definition_str != "":
        mode_id_definition_str = mode_id_definition_str[:-2]

    # -- instances of mode classes as members of the lexer
    mode_object_members_txt,     \
    mode_specific_functions_txt, \
    friend_txt                   = get_mode_class_related_code_fragments(ModeDB.values())

    # -- define a pointer that directly has the type of the derived class
    if Setup.analyzer_derived_class_name == "":
        Setup.analyzer_derived_class_name = LexerClassName
        derived_class_type_declaration = ""
    else:
        derived_class_type_declaration = "class %s;" % Setup.analyzer_derived_class_name

    token_class_file_name = lexer_mode.token_type_definition.get_file_name()
    token_class_name      = lexer_mode.token_type_definition.class_name
    token_class_name_safe = lexer_mode.token_type_definition.class_name_safe

    template_code_txt = get_file_content_or_die(QuexClassHeaderFileTemplate)

    include_guard_ext = get_include_guard_extension(
            Setup.language_db["$namespace-ref"](Setup.analyzer_name_space) 
            + "__" + Setup.analyzer_class_name)

    function_code_txt = write_constructor_and_memento_functions(ModeDB)

    txt = blue_print(template_code_txt,
            [
                ["$$___SPACE___$$",                      " " * (len(LexerClassName) + 1)],
                ["$$CLASS_BODY_EXTENSION$$",             lexer_mode.class_body_extension.get_code()],
                ["$$CONVERTER_HELPER$$",                 get_file_reference(Setup.output_buffer_codec_header)],
                ["$$INCLUDE_GUARD_EXTENSION$$",          include_guard_ext],
                ["$$LEXER_CLASS_NAME$$",                 LexerClassName],
                ["$$LEXER_CLASS_NAME_SAFE$$",            Setup.analyzer_name_safe],
                ["$$LEXER_CONFIG_FILE$$",                get_file_reference(Setup.output_configuration_file)],
                ["$$LEXER_DERIVED_CLASS_DECL$$",         derived_class_type_declaration],
                ["$$LEXER_DERIVED_CLASS_NAME$$",         Setup.analyzer_derived_class_name],
                ["$$QUEX_MODE_ID_DEFINITIONS$$",         mode_id_definition_str],
                ["$$MEMENTO_EXTENSIONS$$",               lexer_mode.memento_class_extension.get_code()],
                ["$$MODE_CLASS_FRIENDS$$",               friend_txt],
                ["$$MODE_OBJECTS$$",                     mode_object_members_txt],
                ["$$MODE_SPECIFIC_ANALYSER_FUNCTIONS$$", mode_specific_functions_txt],
                ["$$PRETTY_INDENTATION$$",               "     " + " " * (len(LexerClassName)*2 + 2)],
                ["$$QUEX_TEMPLATE_DIR$$",                QUEX_PATH + Setup.language_db["$code_base"]],
                ["$$QUEX_VERSION$$",                     QUEX_VERSION],
                ["$$TOKEN_CLASS_DEFINITION_FILE$$",      get_file_reference(token_class_file_name)],
                ["$$TOKEN_CLASS$$",                      token_class_name],
                ["$$TOKEN_CLASS_NAME_SAFE$$",            token_class_name_safe],
                ["$$TOKEN_ID_DEFINITION_FILE$$",         get_file_reference(Setup.output_token_id_file)],
                ["$$CORE_ENGINE_CHARACTER_CODING$$",     quex_converter_coding_name_str],
                ["$$USER_DEFINED_HEADER$$",              lexer_mode.header.get_code() + "\n"],
             ])

    return txt, function_code_txt

quex_mode_init_call_str = """
     QUEX_NAME($$MN$$).id   = QUEX_NAME(ModeID_$$MN$$);
     QUEX_NAME($$MN$$).name = "$$MN$$";
     QUEX_NAME($$MN$$).analyzer_function = $analyzer_function;
#    if      defined(QUEX_OPTION_INDENTATION_TRIGGER) \\
        && ! defined(QUEX_OPTION_INDENTATION_DEFAULT_HANDLER)
     QUEX_NAME($$MN$$).on_indentation = $on_indentation;
#    endif
     QUEX_NAME($$MN$$).on_entry       = $on_entry;
     QUEX_NAME($$MN$$).on_exit        = $on_exit;
#    if      defined(QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK)
     QUEX_NAME($$MN$$).has_base       = $has_base;
     QUEX_NAME($$MN$$).has_entry_from = $has_entry_from;
     QUEX_NAME($$MN$$).has_exit_to    = $has_exit_to;
#    endif
"""

def __get_mode_init_call(mode):
    
    analyzer_function = "QUEX_NAME(%s_analyzer_function)" % mode.name
    on_indentation    = "QUEX_NAME(%s_on_indentation)"    % mode.name
    on_entry          = "QUEX_NAME(%s_on_entry)"          % mode.name
    on_exit           = "QUEX_NAME(%s_on_exit)"           % mode.name
    has_base          = "QUEX_NAME(%s_has_base)"          % mode.name
    has_entry_from    = "QUEX_NAME(%s_has_entry_from)"    % mode.name
    has_exit_to       = "QUEX_NAME(%s_has_exit_to)"       % mode.name

    if mode.options["inheritable"] == "only": 
        analyzer_function = "QUEX_NAME(Mode_uncallable_analyzer_function)"

    if mode.get_code_fragment_list("on_entry") == []:
        on_entry = "QUEX_NAME(Mode_on_entry_exit_null_function)"

    if mode.get_code_fragment_list("on_exit") == []:
        on_exit = "QUEX_NAME(Mode_on_entry_exit_null_function)"

    if mode.get_code_fragment_list("on_indentation") == []:
        on_indentation = "QUEX_NAME(Mode_on_indentation_null_function)"

    txt = blue_print(quex_mode_init_call_str,
                [["$$MN$$",             mode.name],
                 ["$analyzer_function", analyzer_function],
                 ["$on_indentation",    on_indentation],
                 ["$on_entry",          on_entry],
                 ["$on_exit",           on_exit],
                 ["$has_base",          has_base],
                 ["$has_entry_from",    has_entry_from],
                 ["$has_exit_to",       has_exit_to]])

    return txt

def __get_mode_function_declaration(Modes, FriendF=False):

    if FriendF: prolog = "    friend "
    else:       prolog = "extern "

    def __mode_functions(Prolog, ReturnType, NameList, ArgList):
        txt = ""
        for name in NameList:
            function_signature = "%s QUEX_NAME(%s_%s)(%s);" % \
                     (ReturnType, mode.name, name, ArgList)
            txt += "%s" % Prolog + "    " + function_signature + "\n"

        return txt

    txt = ""
    on_indentation_txt = ""
    for mode in Modes:
        if mode.options["inheritable"] == "only": continue

        txt += __mode_functions(prolog, "__QUEX_TYPE_ANALYZER_RETURN_VALUE", 
                                ["analyzer_function"],
                                "QUEX_TYPE_ANALYZER*")

        # If one of the following events is specified, then we need an 'on_indentation' handler
        for event_name in ["on_indentation"]:
            if not mode.has_code_fragment_list(event_name): continue
            on_indentation_txt = __mode_functions(prolog, "void", ["on_indentation"], 
                                 "QUEX_TYPE_ANALYZER*, QUEX_TYPE_INDENTATION, QUEX_TYPE_CHARACTER*")

        for event_name in ["on_exit", "on_entry"]:
            if not mode.has_code_fragment_list(event_name): continue
            txt += __mode_functions(prolog, "void", [event_name], 
                                    "QUEX_TYPE_ANALYZER*, const QUEX_NAME(Mode)*")

        txt += "#ifdef QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK\n"
        txt += __mode_functions(prolog, "bool", ["has_base", "has_entry_from", "has_exit_to"], 
                                "const QUEX_NAME(Mode)*")
        txt += "#endif\n"

    txt += on_indentation_txt
    txt += "\n"

    return txt

def get_constructor_code(Modes):
    L = max(map(lambda m: len(m.name), Modes))

    txt = ""
    for mode in Modes:
        if mode.options["inheritable"] == "only": continue
        txt += "    __quex_assert(QUEX_NAME(ModeID_%s) %s< %i);\n" % \
               (mode.name, " " * (L-len(mode.name)), len(Modes))

    for mode in Modes:
        if mode.options["inheritable"] == "only": continue
        txt += __get_mode_init_call(mode)

    for mode in Modes:
        if mode.options["inheritable"] == "only": continue
        txt += "        me->mode_db[QUEX_NAME(ModeID_%s)]%s = &(QUEX_NAME(%s));\n" % \
               (mode.name, " " * (L-len(mode.name)), mode.name)
    return txt

def get_mode_class_related_code_fragments(Modes):
    """
       RETURNS:  -- members of the lexical analyzer class for the mode classes
                 -- static member functions declaring the analyzer functions for he mode classes 
                 -- constructor init expressions (before '{'),       
                 -- constructor text to be executed at construction time 
                 -- friend declarations for the mode classes/functions

    """
    L = max(map(lambda m: len(m.name), Modes))

    members_txt = ""    
    for mode in Modes:
        if mode.options["inheritable"] == "only": continue
        members_txt += "        extern QUEX_NAME(Mode)  QUEX_NAME(%s);\n" % mode.name

    mode_functions_txt = __get_mode_function_declaration(Modes, FriendF=False)
    friends_txt        = __get_mode_function_declaration(Modes, FriendF=True)

    return members_txt,        \
           mode_functions_txt, \
           friends_txt

