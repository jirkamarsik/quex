import sys

from   quex.frs_py.file_in import error_msg, verify_word_in_list
import quex.lexer_mode     as     lexer_mode
from   quex.core_engine.generator.action_info             import CodeFragment
import quex.core_engine.state_machine.commonality_checker as     commonality_checker
import quex.core_engine.state_machine.subset_checker      as     subset_checker


def do(ModeDB):
    """Consistency check of mode database

       -- Are there applicable modes?
       -- Start mode:
          -- specified (more than one applicable mode req. explicit specification)?
          -- is defined as mode?
          -- start mode is not inheritable only?
       -- Entry/Exit transitions are allows?
    """
    if len(ModeDB) == 0:
        error_msg("No single mode defined - bailing out", Prefix="consistency check")

    mode_name_list            = map(lambda mode:        mode.name, ModeDB.values())
    mode_name_list.sort()
    applicable_mode_name_list = map(lambda mode:        mode.name, 
                                    filter(lambda mode: mode.options["inheritable"] != "only",
                                           ModeDB.values()))
    applicable_mode_name_list.sort()

    # (*) Is there a mode that is applicable?
    #     That is: is there a more that is not only inheritable?
    if len(applicable_mode_name_list) == 0:
        error_msg("There is no mode that can be applied---all existing modes are 'inheritable only'.\n" + \
                  "modes are = " + repr(mode_name_list)[1:-1],
                  Prefix="consistency check")

    # (*) Start mode specified?
    __start_mode(applicable_mode_name_list, mode_name_list)

    # (*) Modes that are inherited must allow to be inherited
    for mode in ModeDB.values():
        for base_mode in mode.get_base_mode_sequence()[:-1]:
            if base_mode.options["inheritable"] == "no":
                error_msg("mode '%s' inherits mode '%s' which is not inheritable." % \
                          (mode.name, base_mode.name), mode.filename, mode.line_n)

    # (*) A mode that is instantiable (to be implemented) needs finally contain matches!
    for mode in ModeDB.values():
        if mode.name in applicable_mode_name_list and mode.get_pattern_action_pair_list() == []:
            error_msg("Mode '%s' was defined without the option <inheritable: only>.\n" % mode.name + \
                      "However, it contains no matches--only event handlers. Without pattern\n"     + \
                      "matches it cannot act as a pattern detecting state machine, and thus\n"      + \
                      "cannot be an independent lexical analyzer mode. Define the option\n"         + \
                      "<inheritable: only>.", \
                      mode.filename, mode.line_n)

    # (*) Entry/Exit Transitions
    for mode in ModeDB.values():
        __entry_exit_transitions(mode, mode_name_list)

    # (*) An indentation counter shall not interfer with whatsoever pattern
    for mode in ModeDB.values():
        indentation_setup = mode.options["indentation"]
        if indentation_setup == None: continue

        # The newline pattern shall not have intersections with other patterns!
        newline_info        = indentation_setup.newline_state_machine
        assert newline_info != None
        __commonality(mode, newline_info, newline_info.get(), "indentation newline")

        newline_suppressor_info = indentation_setup.newline_suppressor_state_machine
        if newline_suppressor_info.get() != None:
            # Supressor *can* have commonalities with other patterns without confusion,
            # since it does not trigger indentation handling.
            # __commonality(mode, newline_suppressor_info, newline_suppressor_info.get(), 
            #              "indentation newline suppressor")

            # Newline and newline suppressor should never have a superset/subset relation
            if    subset_checker.do(newline_info.get(), newline_suppressor_info.get()) \
               or subset_checker.do(newline_suppressor_info.get(), newline_info.get()):

                error_msg("The indentation newline pattern '%s' and the newline" \
                          % newline_info.pattern_str, 
                          newline_info.file_name, newline_info.line_n, 
                          DontExitF=True, WarningF=False)

                error_msg("suppressor pattern '%s' match same on same lexemes." \
                          % newline_suppressor_info.pattern_str, 
                          newline_suppressor_info.file_name, newline_suppressor_info.line_n)


def __commonality(mode, Info, ReferenceSM, Name):
    for pattern_action_pair in mode.get_pattern_action_pair_list():
        if pattern_action_pair.comment in ["indentation newline", "indentation newline suppressor"]: 
            continue

        sm = pattern_action_pair.pattern_state_machine()
        if commonality_checker.do(ReferenceSM, sm) != commonality_checker.NONE:
            error_msg("The %s pattern '%s'" \
                      % (Name, Info.pattern_str), Info.file_name, Info.line_n, 
                      DontExitF=True, WarningF=False)

            pattern           = pattern_action_pair.pattern
            file_name, line_n = pattern_action_pair.get_action_location()
            error_msg("has commonalities with pattern '%s' defined here." % pattern, 
                      file_name, line_n)

def __start_mode(applicable_mode_name_list, mode_name_list):
    """If more then one mode is defined, then that requires an explicit 
       definition 'start = mode'.
    """
    assert len(applicable_mode_name_list) != 0

    start_mode = lexer_mode.initial_mode.get_pure_code()
    if start_mode == "":
        # Choose an applicable mode as start mode
        start_mode              = applicable_mode_name_list[0]
        lexer_mode.initial_mode = CodeFragment(start_mode)
        if len(applicable_mode_name_list) > 1:
            error_msg("No initial mode defined via 'start' while more than one applicable mode exists.\n" + \
                      "Use for example 'start = %s;' in the quex source file to define an initial mode." \
                      % start_mode)
        # This Branch: start mode is applicable and present

    else: 
        FileName = lexer_mode.initial_mode.filename
        LineN    = lexer_mode.initial_mode.line_n
        # Start mode present and applicable?
        verify_word_in_list(start_mode, mode_name_list,
                            "Start mode '%s' is not defined." % start_mode,
                            FileName, LineN)
        verify_word_in_list(start_mode, applicable_mode_name_list,
                            "Start mode '%s' is inheritable only and cannot be instantiated." % start_mode,
                            FileName, LineN)

def __entry_exit_transitions(mode, mode_name_list):
    FileName = mode.filename
    LineN    = mode.line_n
    for mode_name in mode.options["exit"]:

        verify_word_in_list(mode_name, mode_name_list,
                            "Mode '%s' allows entry from\nmode '%s' but no such mode exists." % \
                            (mode.name, mode_name), FileName, LineN)

        that_mode = lexer_mode.mode_description_db[mode_name]

        # Other mode allows all entries => don't worry.
        if len(that_mode.options["entry"]) == 0: continue

        # Other mode restricts the entries from other modes
        # => check if this mode or one of the base modes can enter
        for base_mode in mode.get_base_mode_sequence():
            if base_mode.name in that_mode.options["entry"]: break
        else:
            error_msg("Mode '%s' has an exit to mode '%s' but" % (mode.name, mode_name),
                      FileName, LineN, DontExitF=True, WarningF=False)
            error_msg("mode '%s' has no entry for mode '%s'\n" % (mode_name, mode.name) + \
                      "or any of its base modes.",
                      that_mode.filename, that_mode.line_n)

    for mode_name in mode.options["entry"]:
        # Does that mode exist?
        verify_word_in_list(mode_name, mode_name_list,
                            "Mode '%s' allows entry from\nmode '%s' but no such mode exists." % \
                            (mode.name, mode_name), FileName, LineN)

        that_mode = lexer_mode.mode_description_db[mode_name]
        # Other mode allows all exits => don't worry.
        if len(that_mode.options["exit"]) == 0: continue

        # Other mode restricts the exits to other modes
        # => check if this mode or one of the base modes can be reached
        for base_mode in mode.get_base_mode_sequence():
            if base_mode.name in that_mode.options["exit"]: break
        else:
            error_msg("Mode '%s' has an entry for mode '%s' but" % (mode.name, mode_name),
                      FileName, LineN, DontExitF=True, WarningF=False)
            error_msg("mode '%s' has no exit to mode '%s'\n" % (mode_name, mode.name) + \
                      "or any of its base modes.",
                      that_mode.filename, that_mode.line_n)
            

