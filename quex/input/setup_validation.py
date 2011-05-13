import os.path
from   quex.DEFINITIONS    import QUEX_PATH
from   quex.input.setup    import SETUP_INFO, DEPRECATED, global_character_type_db
import quex.input.codec_db as     codec_db
import quex.input.query    as     query
from   quex.frs_py.file_in import is_identifier, \
                                  error_msg, \
                                  verify_word_in_list, \
                                  error_msg_file_not_found

def do(setup, command_line, argv):
    """Does a consistency check for setup and the command line.
    """

    setup.output_directory = os.path.normpath(setup.output_directory)
    if setup.output_directory != "":
        # Check, if the output directory exists
        if os.access(setup.output_directory, os.F_OK) == False:
            error_msg("The directory %s was specified for output, but does not exists." % setup.output_directory)
        if os.access(setup.output_directory, os.W_OK) == False:
            error_msg("The directory %s was specified for output, but is not writeable." % setup.output_directory)

    # if the mode is 'plotting', then check wether a graphic format is speicified
    for plot_option in SETUP_INFO["plot_graphic_format"][0]:
        if plot_option in argv and setup.plot_graphic_format == "":
            error_msg("Option '%s' must be followed by a graphic format specifier (bmp, svg, jpg, ...)" % \
                      plot_option)

    if setup.plot_character_display not in ["hex", "utf8"]:
        error_msg("Plot character display must be either 'hex' or 'utf8'.\nFound: '%s'" % 
                  setup.plot_character_display)

    # ensure that options are not specified twice
    for parameter, info in SETUP_INFO.items():
        if type(info) != list: continue
        occurence_n = 0 
        for option in info[0]:
            occurence_n += argv.count(option)
        if occurence_n > 1:
            error_msg("Received more than one of the following options:\n" + \
                      "%s" % repr(info[0])[1:-1])

    # (*) Check for 'Depraceted' Options ___________________________________________________
    for name, info in DEPRECATED.items():
        command_line_options = SETUP_INFO[name][0]
        comment                   = info[0]
        depreciated_since_version = info[1]
        for option in command_line_options:
            if command_line.search(option):
                error_msg("Command line option '%s' is ignored.\n" % option + \
                          comment + "\n" + \
                          "Last version of Quex supporting this option is version %s. Please, visit\n" % \
                          depreciated_since_version + \
                          "http://quex.org for further information.")
                          
    # (*) Check for 'Straying' Options ___________________________________________________
    options = []
    for key, info in SETUP_INFO.items():
        if type(info) != list: continue
        if key in DEPRECATED: continue
        if info[1] != None: options.extend(info[0])
    options.sort(lambda a,b: cmp(a.replace("-",""), b.replace("-","")))

    ufos = command_line.unidentified_options(options)
    if ufos != []:
        error_msg("Unidentified option(s) = " +  repr(ufos) + "\n" + \
                  __get_supported_command_line_option_description(options))

    if setup.analyzer_derived_class_name != "" and \
       setup.analyzer_derived_class_file == "":
            error_msg("Specified derived class '%s' on command line, but it was not\n" % \
                      setup.analyzer_derived_class_name + \
                      "specified which file contains the definition of it.\n" + \
                      "use command line option '--derived-class-file'.\n")

    if setup.buffer_element_size not in [-1, 1, 2, 4]:
        error_msg("The setting of '--buffer-element-size' (or '-b') can only be\n" 
                  "1, 2, or 4 (found %s)." % repr(setup.buffer_element_size))

    if setup.buffer_byte_order not in ["<system>", "little", "big"]:
        error_msg("Byte order (option --endian) must be 'little', 'big', or '<system>'.\n" + \
                  "Note, that this option is only interesting for cross plattform development.\n" + \
                  "By default, quex automatically chooses the endian type of your system.")

    # Manually written token class requires token class name to be specified
    if setup.token_class_file != "" and command_line.search("--token-class", "--tc") == False:
        error_msg("The use of a manually written token class requires that the name of the class\n"
                  "is specified on the command line via the '--token-class' option.")
    
    # Token queue
    if setup.token_policy != "queue" and command_line.search("--token-queue-size"):
        error_msg("Option --token-queue-size determines a fixed token queue size. This makes\n" + \
                  "only sense in conjunction with '--token-policy queue'.\n")
    if setup.token_queue_size <= setup.token_queue_safety_border + 1:
        if setup.token_queue_size == setup.token_queue_safety_border: cmp_str = "equal to"
        else:                                                         cmp_str = "less than"
        error_msg("Token queue size is %i is %s token queue safety border %i + 1.\n" % \
                  (setup.token_queue_size, cmp_str, setup.token_queue_safety_border) + 
                  "Set appropriate values with --token-queue-size and --token-queue-safety-border.")

    # Check that names are valid identifiers
    __check_identifier(setup, "token_id_prefix_plain",    "Token prefix")
    __check_identifier(setup, "analyzer_class_name", "Engine name")
    if setup.analyzer_derived_class_name != "": 
        __check_identifier(setup, "analyzer_derived_class_name", "Derived class name")
    
    __check_file_name(setup, "token_class_file",            "file containing token class definition")
    __check_file_name(setup, "analyzer_derived_class_file", "file containing user derived lexer class")
    __check_file_name(setup, "token_id_foreign_definition_file", "file containing user token ids")
    __check_file_name(setup, "input_mode_files", "quex source file")

    # Check that not more than one converter is specified
    converter_n = 0
    if setup.converter_iconv_f:             converter_n += 1
    if setup.converter_icu_f:               converter_n += 1 
    if setup.converter_user_new_func != "": converter_n += 1
    if converter_n > 1:
        error_msg("More than one character converter has been specified. Note, that the\n" + \
                  "options '--icu', '--iconv', and '--converter-new' (or '--cn') are\n"    + \
                  "to be used mutually exclusively.")
    if converter_n == 1 and setup.buffer_codec != "":  
        error_msg("An engine that is to be generated for a specific codec cannot rely\n"      + \
                  "on converters. Do no use '--codec' together with '--icu', '--iconv', or\n" + \
                  "`--converter-new`.")

    # If a user defined type is specified for 'engine character type' and 
    # a converter, then the name of the target type must be specified explicitly.
    if         setup.buffer_element_type != "" \
       and not global_character_type_db.has_key(setup.buffer_element_type) \
       and     setup.converter_ucs_coding_name == "" \
       and     converter_n != 0:
        tc = setup.buffer_element_type
        error_msg("A character code converter has been specified. It is supposed to convert\n" + \
                  "incoming data into an internal buffer of unicode characters. The size of\n" + \
                  "each character is determined by '%s' which is a user defined type.\n" % tc  + \
                  "\n" + \
                  "Quex cannot determine automatically the name that the converter requires\n" +      \
                  "to produce unicode characters for type '%s'. It must be specified by the\n" % tc + \
                  "command line option '--converter-ucs-coding-name' or '--cucn'.")

    # Token transmission policy
    token_policy_list = ["queue", "single", "users_token", "users_queue"]
    if setup.token_policy not in token_policy_list:
        error_msg("Token policy '%s' not supported. Use one of the following:\n" % setup.token_policy + \
                  repr(token_policy_list)[1:-1])
    elif setup.token_policy == "users_token":
        error_msg("Token policy 'users_queue' has be deprecated since 0.49.1. Use\n"
                  "equivalent policy 'single'.")
    elif setup.token_policy == "users_queue":
        error_msg("Token policy 'users_queue' has be deprecated since 0.49.1\n")

    # Internal engine character encoding
    def __codec_vs_buffer_element_size(CodecName, RequiredBufferElementSize):
        if   setup.buffer_codec        != CodecName:                 return
        elif setup.buffer_element_size == RequiredBufferElementSize: return

        if setup.buffer_element_size == -1: 
            msg_str = "undetermined (found type '%s')" % setup.buffer_element_type
        else:
            msg_str = "is not %i (found %i)" % (RequiredBufferElementSize, setup.buffer_element_size)

        error_msg("Using codec '%s' while buffer element size %s.\n" % (CodecName, msg_str) + 
                  "Consult command line argument '--buffer-element-size'.")

    if setup.buffer_codec != "":
        verify_word_in_list(setup.buffer_codec,
                            codec_db.get_supported_codec_list() + ["utf8", "utf16"],
                            "Codec '%s' is not supported." % setup.buffer_codec)
        __codec_vs_buffer_element_size("utf8", 1)
        __codec_vs_buffer_element_size("utf16", 2)

    # Path Compression
    if setup.compression_path_uniform_f and setup.compression_path_f:
        error_msg("Both flags for path compression were set: '--path-compression' and\n" 
                  "'--path-compression-uniform'. Please, choose only one!")

def __check_identifier(setup, Candidate, Name):
    value = setup.__dict__[Candidate]
    if is_identifier(value): return

    CommandLineOption = SETUP_INFO[Candidate][0]

    error_msg("%s must be a valid identifier (%s).\n" % (Name, repr(CommandLineOption)[1:-1]) + \
              "Received: '%s'" % value)

def __get_supported_command_line_option_description(NormalModeOptions):
    txt = "OPTIONS:\n"
    for option in NormalModeOptions:
        txt += "    " + option + "\n"

    txt += "\nOPTIONS FOR QUERY MODE:\n"
    txt += query.get_supported_command_line_option_description()
    return txt

def __check_file_name(setup, Candidate, Name):
    value             = setup.__dict__[Candidate]
    CommandLineOption = SETUP_INFO[Candidate][0]

    if value == "": return

    if type(value) == list:
        for name in value:
            if name != "" and name[0] == "-": 
                error_msg("Quex refuses to work with file names that start with '-' (minus).\n"  + \
                          "Received '%s' for %s (%s)" % (value, name, repr(CommandLineOption)[1:-1]))
            if os.access(name, os.F_OK) == False:
                # error_msg("File %s (%s)\ncannot be found." % (name, Name))
                error_msg_file_not_found(name, Name)
    else:
        if value == "" or value[0] == "-":              return
        if os.access(value, os.F_OK):                   return
        if os.access(QUEX_PATH + "/" + value, os.F_OK): return
        if     os.access(os.path.dirname(value), os.F_OK) == False \
           and os.access(QUEX_PATH + "/" + os.path.dirname(value), os.F_OK) == False:
            error_msg("File '%s' is supposed to be located in directory '%s' or\n" % \
                      (os.path.basename(value), os.path.dirname(value)) + \
                      "'%s'. No such directories exist." % \
                      (QUEX_PATH + "/" + os.path.dirname(value)))
        error_msg_file_not_found(value, Name)

