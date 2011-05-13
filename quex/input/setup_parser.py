from   quex.DEFINITIONS import *
from   copy import copy, deepcopy
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
from   StringIO import StringIO

from   quex.GetPot                 import GetPot
from   quex.frs_py.file_in         import error_msg,                \
                                          verify_word_in_list,      \
                                          read_namespaced_name,     \
                                          read_integer
import quex.lexer_mode  as lexer_mode
import quex.input.codec_db            as codec_db
import quex.input.setup_validation    as validation
from   quex.output.cpp.token_id_maker import parse_token_id_file

from   quex.input.setup import setup, SETUP_INFO, LIST, FLAG,    \
                               NEGATED_FLAG, DEPRECATED, HEADER, \
                               HEADER_IMPLEMTATION, SOURCE,      \
                               global_extension_db,              \
                               global_character_type_db

from   quex.core_engine.generator.languages.core import db as quex_core_engine_generator_languages_db

from   quex.core_engine.generator.action_info import CodeFragment

class ManualTokenClassSetup:
    """Class to mimik as 'real' TokenTypeDescriptor as defined in 
       quex.input.token_type.py. Names and functions must remain
       as they are for compatibility.
    """
    def __init__(self, FileName, ClassName, NameSpace, ClassNameSafe, TokenIDType):
        
        self.__file_name       = FileName
        self.class_name        = ClassName
        self.name_space        = NameSpace
        self.class_name_safe   = ClassNameSafe

        self.column_number_type = CodeFragment("size_t")
        self.line_number_type   = CodeFragment("size_t")
        self.token_id_type      = CodeFragment(TokenIDType)

    def get_file_name(self):
        return self.__file_name

    def manually_written(self):
        return True

def do(argv):
    """RETURN:  True, if process needs to be started.
                False, if job is done.
    """
    global setup

    # (*) Interpret Command Line (A) _____________________________________________________
    command_line = GetPot(argv)

    if command_line.search("--version", "-v"):
        print "Quex - Fast Universal Lexical Analyzer Generator"
        print "Version " + QUEX_VERSION
        print "(C) 2006-2010 Frank-Rene Schaefer"
        print "ABSOLUTELY NO WARRANTY"
        return False

    if command_line.search("--help", "-h"):
        print "Quex - Fast Universal Lexical Analyzer Generator"
        print "Please, consult the quex documentation for further help, or"
        print "visit http://quex.org"
        print "(C) 2006-2010 Frank-Rene Schaefer"
        print "ABSOLUTELY NO WARRANTY"
        return False

    if command_line.search("--plot-format-list"):
        print quex.output.graphviz.interface.get_supported_graphic_format_description()
        return False

    for variable_name, info in SETUP_INFO.items():
        # Some parameters are not set on the command line. Their entry is not associated
        # with a description list.
        if type(info) != list: continue

        if info[1] == FLAG:
            setup.__dict__[variable_name] = command_line.search(info[0])        

        elif info[1] == NEGATED_FLAG:
            setup.__dict__[variable_name] = not command_line.search(info[0])        

        elif info[1] == LIST:
            if not command_line.search(info[0]):
                setup.__dict__[variable_name] = []
            else:
                the_list = command_line.nominus_followers(info[0])
                if the_list == []:
                    error_msg("Option %s\nnot followed by anything." % repr(info[0])[1:-1])

                if setup.__dict__.has_key(variable_name):
                    setup.__dict__[variable_name].extend(the_list)        
                else:
                    setup.__dict__[variable_name] = the_list

        elif command_line.search(info[0]):
            if not command_line.search(info[0]):
                setup.__dict__[variable_name] = info[1]
            else:
                value = command_line.follow("--EMPTY--", info[0])
                if value == "--EMPTY--":
                    error_msg("Option %s\nnot followed by anything." % repr(info[0])[1:-1])
                setup.__dict__[variable_name] = value

    # (*) Classes and their namespace
    setup.analyzer_class_name, \
    setup.analyzer_name_space, \
    setup.analyzer_name_safe   = \
         read_namespaced_name(setup.analyzer_class_name, 
                              "analyzer engine (options -o, --engine, --analyzer-class)")

    setup.analyzer_derived_class_name,       \
    setup.analyzer_derived_class_name_space, \
    setup.analyzer_derived_class_name_safe = \
         read_namespaced_name(setup.analyzer_derived_class_name, 
                              "derived analyzer class (options --derived-class, --dc)",
                              AllowEmptyF=True)

    if setup.analyzer_name_space == []:
        setup.analyzer_name_space = ["quex"]

    if setup.token_class_name == "":
        setup.token_class_name = "%s::Token" % reduce(lambda a, b: a + "::" + b, setup.analyzer_name_space)

    # Token classes and derived classes have the freedom not to open a namespace,
    # thus no check 'if namespace == []'.
    setup.token_class_name,       \
    setup.token_class_name_space, \
    setup.token_class_name_safe = \
         read_namespaced_name(setup.token_class_name, 
                              "token class (options --token-class, --tc)")

    if setup.token_class_file != "":
        lexer_mode.token_type_definition = \
                ManualTokenClassSetup(setup.token_class_file,
                                      setup.token_class_name,
                                      setup.token_class_name_space,
                                      setup.token_class_name_safe,
                                      setup.token_id_type)

    if setup.token_class_name_space == []:
        setup.token_class_name_space = deepcopy(setup.analyzer_name_space)

    setup.token_id_prefix_plain,      \
    setup.token_id_prefix_name_space, \
    dummy                           = \
         read_namespaced_name(setup.token_id_prefix, 
                              "token prefix (options --token-prefix)")

    if len(setup.token_id_prefix_name_space) != 0 and setup.language.upper() == "C":
         error_msg("Token id prefix cannot contain a namespaces if '--language' is set to 'C'.")

    # (*) Output programming language        
    setup.language = setup.language.upper()
    verify_word_in_list(setup.language,
                        quex_core_engine_generator_languages_db.keys(),
                        "Programming language '%s' is not supported." % setup.language)
    setup.language_db = quex_core_engine_generator_languages_db[setup.language]
    setup.extension_db = global_extension_db[setup.language]

    # Is the output file naming scheme provided by the extension database
    # (Validation must happen immediately)
    if setup.extension_db.has_key(setup.output_file_naming_scheme) == False:
        error_msg("File extension scheme '%s' is not provided for language '%s'.\n" \
                  % (setup.output_file_naming_scheme, setup.language) + \
                  "Available schemes are: %s." % repr(setup.extension_db.keys())[1:-1])

    # Before file names can be prepared, determine the output directory
    # If 'source packaging' is enabled and no output directory is specified
    # then take the directory of the source packaging.
    if setup.source_package_directory != "" and setup.output_directory == "":
        setup.output_directory = setup.source_package_directory

    # (*) Output files
    prepare_file_names(setup)

    if setup.buffer_byte_order == "<system>": 
        setup.buffer_byte_order = sys.byteorder 
        setup.byte_order_is_that_of_current_system_f = True
    else:
        setup.byte_order_is_that_of_current_system_f = False

    if setup.buffer_element_size == "wchar_t":
        error_msg("Since Quex version 0.53.5, 'wchar_t' can no longer be specified\n"
                  "with option '--buffer-element-size' or '-bes'. Please, specify\n"
                  "'--buffer-element-type wchar_t' or '--bet'.")

    if setup.buffer_element_type == "wchar_t":
        setup.converter_ucs_coding_name = "WCHAR_T"

    if setup.buffer_codec != "":
        setup.buffer_element_size_irrelevant = True
    
    make_numbers(setup)

    # (*) Determine buffer element type and size (in bytes)
    if setup.buffer_element_size == -1:
        if global_character_type_db.has_key(setup.buffer_element_type):
            setup.buffer_element_size = global_character_type_db[setup.buffer_element_type][3]
        elif setup.buffer_element_type == "":
            setup.buffer_element_size = 1
        else:
            # If the buffer element type is defined, then here we know that it is 'unknown'
            # and Quex cannot know its size on its own.
            setup.buffer_element_size = -1

    if setup.buffer_element_type == "":
        if setup.buffer_element_size in [1, 2, 4]:
            setup.buffer_element_type = { 
                1: "uint8_t", 2: "uint16_t", 4: "uint32_t",
            }[setup.buffer_element_size]
        elif setup.buffer_element_size == -1:
            pass
        else:
            error_msg("Buffer element type cannot be determined for size '%i' which\n" \
                      % setup.buffer_element_size + 
                      "has been specified by '-b' or '--buffer-element-size'.")

    if setup.buffer_codec in ["utf8", "utf16"]:
        setup.buffer_codec_transformation_info = setup.buffer_codec + "-state-split"
    elif setup.buffer_codec != "":
        setup.buffer_codec_transformation_info = codec_db.get_codec_transformation_info(setup.buffer_codec)

    setup.converter_f = False
    if setup.converter_iconv_f or setup.converter_icu_f:
        setup.converter_f = True

    # The only case where no converter helper is required is where ASCII 
    # (Unicode restricted to [0, FF] is used.
    setup.converter_helper_required_f = True
    if setup.converter_f == False and setup.buffer_element_size == 1 and setup.buffer_codec == "":
        setup.converter_helper_required_f = False

    validation.do(setup, command_line, argv)

    if setup.converter_ucs_coding_name == "": 
        if global_character_type_db.has_key(setup.buffer_element_type):
            if setup.buffer_byte_order == "little": index = 1
            else:                                   index = 2
            setup.converter_ucs_coding_name = global_character_type_db[setup.buffer_element_type][index]

    if setup.token_id_foreign_definition_file != "": 
        CommentDelimiterList = [["//", "\n"], ["/*", "*/"]]
        # Regular expression to find '#include <something>' and extract the 'something'
        # in a 'group'. Note that '(' ')' cause the storage of parts of the match.
        IncludeRE            = "#[ \t]*include[ \t]*[\"<]([^\">]+)[\">]"
        #
        parse_token_id_file(setup.token_id_foreign_definition_file, 
                            setup.token_id_prefix, 
                            CommentDelimiterList, IncludeRE)
        if setup.token_id_prefix_plain != setup.token_id_prefix:
            # The 'plain' name space less token indices are also supported
            parse_token_id_file(setup.token_id_foreign_definition_file, 
                                setup.token_id_prefix_plain, 
                                CommentDelimiterList, IncludeRE)


    # (*) return setup ___________________________________________________________________
    return True

def __get_float(MemberName):
    ValueStr = setup.__dict__[MemberName]
    if type(ValueStr) == float: return ValueStr
    try:
        return float(ValueStr)
    except:
        option_name = repr(SETUP_INFO[MemberName][0])[1:-1]
        error_msg("Cannot convert '%s' into an floating point number for '%s'" % (ValueStr, option_name))

def prepare_file_names(setup):
    setup.output_file_stem = ""
    if setup.analyzer_name_space != ["quex"]:
        for name in setup.analyzer_name_space:
            setup.output_file_stem += name + "_"
    setup.output_file_stem += setup.analyzer_class_name

    setup.output_code_file          = __prepare_file_name("", SOURCE) # 
    setup.output_header_file        = __prepare_file_name("", HEADER)
    setup.output_configuration_file = __prepare_file_name("-configuration", HEADER)
    setup.output_token_id_file      = __prepare_file_name("-token_ids", HEADER)
    setup.output_token_class_file                = __prepare_file_name("-token", HEADER)
    setup.output_token_class_file_implementation = __prepare_file_name("-token", HEADER_IMPLEMTATION)

    if setup.buffer_codec == "utf8":
        setup.output_buffer_codec_header   = "quex/code_base/converter_helper/utf8"
        setup.output_buffer_codec_header_i = "quex/code_base/converter_helper/utf8.i"

    elif setup.buffer_codec == "utf16":
        setup.output_buffer_codec_header   = "quex/code_base/converter_helper/utf16"
        setup.output_buffer_codec_header_i = "quex/code_base/converter_helper/utf16.i"

    elif setup.buffer_codec != "":
        # Note, that the name may be set to 'None' if the conversion is utf8 or utf16
        # See Internal engine character encoding'
        setup.output_buffer_codec_header = \
            __prepare_file_name("-converter-%s" % setup.buffer_codec, HEADER)
        setup.output_buffer_codec_header_i = \
            __prepare_file_name("-converter-%s" % setup.buffer_codec, HEADER_IMPLEMTATION)
    else:
        setup.output_buffer_codec_header   = "quex/code_base/converter_helper/unicode"
        setup.output_buffer_codec_header_i = "quex/code_base/converter_helper/unicode.i"

def make_numbers(setup):
    setup.compression_template_coef  = __get_float("compression_template_coef")
    setup.buffer_limit_code          = __get_integer("buffer_limit_code")
    setup.path_limit_code            = __get_integer("path_limit_code")

    setup.token_id_counter_offset    = __get_integer("token_id_counter_offset")
    setup.token_queue_size           = __get_integer("token_queue_size")
    setup.token_queue_safety_border  = __get_integer("token_queue_safety_border")
    setup.buffer_element_size   = __get_integer("buffer_element_size")

def __get_integer(MemberName):
    ValueStr = setup.__dict__[MemberName]
    if type(ValueStr) == int: return ValueStr
    result = read_integer(StringIO(ValueStr))
    if result == None:
        option_name = repr(SETUP_INFO[MemberName][0])[1:-1]
        error_msg("Cannot convert '%s' into an integer for '%s'.\n" % (ValueStr, option_name) + \
                  "Use prefix '0x' for hexadecimal numbers.\n" + \
                  "           '0o' for octal numbers.\n"       + \
                  "           '0b' for binary numbers.\n"      + \
                  "           '0r' for roman numbers.\n"      + \
                  "           and no prefix for decimal numbers.")
    return result

def __prepare_file_name(Suffix, ContentType):
    global SOURCE
    global HEADER_IMPLEMTATION
    global HEADER
    global setup

    assert ContentType in [SOURCE, HEADER, HEADER_IMPLEMTATION]

    # Language + Extenstion Scheme + ContentType --> name of extension
    ext = setup.extension_db[setup.output_file_naming_scheme][ContentType]

    file_name = setup.output_file_stem + Suffix + ext

    if setup.output_directory == "": return file_name
    else:                            return os.path.normpath(setup.output_directory + "/" + file_name)

