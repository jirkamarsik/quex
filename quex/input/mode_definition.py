from   quex.frs_py.file_in              import *
from   quex.output.cpp.token_id_maker   import TokenInfo
from   quex.exception                   import RegularExpressionException
import quex.lexer_mode                as lexer_mode
import quex.input.regular_expression  as regular_expression
import quex.input.code_fragment       as code_fragment
import quex.input.indentation_setup   as indentation_setup
from   quex.core_engine.generator.action_info                     import GeneratedCode, UserCodeFragment
from   quex.core_engine.generator.languages.address               import get_label
import quex.core_engine.generator.skipper.character_set           as     skip_character_set
import quex.core_engine.generator.skipper.range                   as     skip_range
import quex.core_engine.generator.skipper.nested_range            as     skip_nested_range
import quex.core_engine.generator.state_coder.indentation_counter as     indentation_counter

import quex.core_engine.state_machine.index                      as index
import quex.core_engine.state_machine.sequentialize              as sequentialize
import quex.core_engine.state_machine.repeat                     as repeat
import quex.core_engine.state_machine.nfa_to_dfa                 as nfa_to_dfa
import quex.core_engine.state_machine.hopcroft_minimization      as hopcroft
import quex.core_engine.state_machine.character_counter          as character_counter    
from   quex.core_engine.state_machine.core                       import StateMachine, SideInfo
import quex.core_engine.regular_expression.snap_character_string as snap_character_string
from   quex.input.setup                                          import setup as Setup
import StringIO

def parse(fh):
    # NOTE: Catching of EOF happens in caller: parse_section(...)

    skip_whitespace(fh)
    mode_name = read_identifier(fh)
    if mode_name == "":
        error_msg("missing identifier at beginning of mode definition.", fh)

    # NOTE: constructor does register this mode in the mode_db
    new_mode  = lexer_mode.ModeDescription(mode_name, fh.name, get_current_line_info_number(fh))

    # (*) inherited modes / options
    skip_whitespace(fh)
    dummy = fh.read(1)
    if dummy not in [":", "{"]:
        error_msg("missing ':' or '{' after mode '%s'" % mode_name, fh)

    if dummy == ":":
        parse_mode_option_list(new_mode, fh)

    # (*) read in pattern-action pairs and events
    while parse_mode_element(new_mode, fh): 
        pass

    # (*) check for modes w/o pattern definitions
    if not new_mode.has_event_handler() and not new_mode.has_own_matches():
        if new_mode.options["inheritable"] != "only":
            new_mode.options["inheritable"] = "only"
            error_msg("Mode without pattern and event handlers needs to be 'inheritable only'.\n" + \
                      "<inheritable: only> has been added automatically.", fh,  DontExitF=True)

def parse_mode_option_list(new_mode, fh):
    position = fh.tell()
    try:  
        # ':' => inherited modes/options follow
        skip_whitespace(fh)

        parse_base_mode_list(fh, new_mode)
        
        while parse_mode_option(fh, new_mode):
            pass

    except EndOfStreamException:
        fh.seek(position)
        error_msg("End of file reached while parsing options of mode '%s'." % mode_name, fh)

def parse_base_mode_list(fh, new_mode):
    new_mode.base_modes = []
    trailing_comma_f    = False
    while 1 + 1 == 2:
        if   check(fh, "{"): fh.seek(-1, 1); break
        elif check(fh, "<"): fh.seek(-1, 1); break

        skip_whitespace(fh)
        identifier = read_identifier(fh)
        if identifier == "": break

        new_mode.base_modes.append(identifier)
        trailing_comma_f = False
        if not check(fh, ","): break
        trailing_comma_f = True


    if trailing_comma_f:
        error_msg("Trailing ',' after base mode '%s'." % new_mode.base_modes[-1], fh, 
                  DontExitF=True, WarningF=True)
        
    elif len(new_mode.base_modes) != 0:
        # This check is a 'service' -- for those who follow the old convention
        pos = fh.tell()
        skip_whitespace(fh)
        dummy_identifier = read_identifier(fh)
        if dummy_identifier != "":
            error_msg("Missing separating ',' between base modes '%s' and '%s'.\n" \
                      % (new_mode.base_modes[-1], dummy_identifier) + \
                      "(The comma separator is mandatory since quex 0.53.1)", fh)
        fh.seek(pos)

def parse_string_constant(fh, Name):
    pos = fh.tell()
    if fh.read(1) != "\"":
        pos = fh.tell()
        msg = fh.read(5)
        fh.seek(pos)
        error_msg("%s can\n" % Name + 
                  "only be a string and must start with a quote like \".\n" +
                  "Found '%s'" % msg, fh)

    sequence = snap_character_string.get_character_code_sequence(fh)
    end_pos  = fh.tell()
    fh.seek(pos)
    msg      = fh.read(end_pos - pos)
    return msg, sequence

def parse_mode_option(fh, new_mode):
    LanguageDB = Setup.language_db

    def fit_state_machine(SM):
        if not SM.is_DFA_compliant(): result = nfa_to_dfa.do(SM)
        else:                         result = SM
        result = hopcroft.do(result, CreateNewStateMachineF=False)
        return result

    identifier = read_option_start(fh)
    if identifier == None: return False

    verify_word_in_list(identifier, lexer_mode.mode_option_info_db.keys(),
                        "mode option", fh.name, get_current_line_info_number(fh))

    if identifier == "skip":
        # A skipper 'eats' characters at the beginning of a pattern that belong
        # to a specified set of characters. A useful application is most probably
        # the whitespace skipper '[ \t\n]'. The skipper definition allows quex to
        # implement a very effective way to skip these regions.
        pattern_str, trigger_set = regular_expression.parse_character_set(fh, PatternStringF=True)
        skip_whitespace(fh)

        if fh.read(1) != ">":
            error_msg("missing closing '>' for mode option '%s'." % identifier, fh)

        if trigger_set.is_empty():
            error_msg("Empty trigger set for skipper." % identifier, fh)

        # TriggerSet skipping is implemented the following way: As soon as one element of the 
        # trigger set appears, the state machine enters the 'trigger set skipper section'.
        # Enter the skipper as if the opener pattern was a normal pattern and the 'skipper' is the action.
        # NOTE: The correspondent CodeFragment for skipping is created in 'implement_skippers(...)'
        pattern_sm  = StateMachine()
        pattern_sm.add_transition(pattern_sm.init_state_index, trigger_set, AcceptanceF=True)

        # Skipper code is to be generated later
        action = GeneratedCode(skip_character_set.do, 
                               FileName = fh.name, 
                               LineN    = get_current_line_info_number(fh))
        action.data["character_set"] = trigger_set

        pattern_sm = fit_state_machine(pattern_sm)
        # For skippers line and column counting detection is not really a topic
        # It is done in the skipper itself.
        pattern_sm.side_info = SideInfo()

        new_mode.add_match(pattern_str, action, pattern_sm)

        return True

    elif identifier in ["skip_range", "skip_nested_range"]:
        # A non-nesting skipper can contain a full fledged regular expression as opener,
        # since it only effects the trigger. Not so the nested range skipper-see below.

        # -- opener
        skip_whitespace(fh)
        if identifier == "skip_nested_range":
            # Nested range state machines only accept 'strings' not state machines
            opener_str, opener_sequence = parse_string_constant(fh, "Opener pattern for 'skip_nested_range'")
            
            opener_sm = StateMachine()
            idx = opener_sm.init_state_index
            for letter in opener_sequence:
                idx = opener_sm.add_transition(idx, letter)
            opener_sm.states[idx].set_acceptance(True)
        else:
            opener_str, opener_sm = regular_expression.parse(fh)
            # For 'range skipping' the opener sequence is not needed, only the opener state
            # machine is webbed into the pattern matching state machine.
            opener_sequence       = None

        skip_whitespace(fh)

        # -- closer
        closer_str, closer_sequence = parse_string_constant(fh, "Closing pattern for 'skip_range' or 'skip_nested_range'")
        skip_whitespace(fh)
        if fh.read(1) != ">":
            error_msg("missing closing '>' for mode option '%s'" % identifier, fh)

        # Skipper code is to be generated later
        generator_function = { 
                "skip_range":        skip_range.do,
                "skip_nested_range": skip_nested_range.do,
        }[identifier]
        action = GeneratedCode(generator_function,
                               FileName = fh.name, 
                               LineN    = get_current_line_info_number(fh))

        action.data["opener_sequence"] = opener_sequence
        action.data["closer_sequence"] = closer_sequence
        action.data["mode_name"]       = new_mode.name

        fit_state_machine(opener_sm)

        # For skippers line and column counting detection is not really a topic
        # It is done in the skipper itself.
        opener_sm.side_info = SideInfo()

        new_mode.add_match(opener_str, action, opener_sm)

        return True
        
    elif identifier == "indentation":
        value = indentation_setup.do(fh)

        # Enter 'Newline' and 'Suppressed Newline' as matches into the engine.
        # Similar to skippers, the indentation count is then triggered by the newline.
        # -- Suppressed Newline = Suppressor followed by Newline,
        #    then newline does not trigger indentation counting.
        suppressed_newline_pattern = ""
        if value.newline_suppressor_state_machine.get() != None:
            suppressed_newline_pattern = \
                  "(" + value.newline_suppressor_state_machine.pattern_str + ")" \
                + "(" + value.newline_state_machine.pattern_str + ")"
                                           
            suppressed_newline_sm = \
                sequentialize.do([value.newline_suppressor_state_machine.get(),
                                  value.newline_state_machine.get()])
                 
            FileName = value.newline_suppressor_state_machine.file_name
            LineN    = value.newline_suppressor_state_machine.line_n
            # Go back to start.
            code_fragment = UserCodeFragment("goto %s;" % get_label("$start", U=True), FileName, LineN)

            suppressed_newline_sm = fit_state_machine(suppressed_newline_sm)

            # Analyze pattern for constant number of newlines, characters, etc.
            suppressed_newline_sm.side_info = SideInfo(
                    character_counter.get_newline_n(suppressed_newline_sm),
                    character_counter.get_character_n(suppressed_newline_sm))

            new_mode.add_match(suppressed_newline_pattern, code_fragment, suppressed_newline_sm,
                               Comment="indentation newline suppressor")

        # When there is an empty line, then there shall be no indentation count on it.
        # Here comes the trick: 
        #
        #      Let               newline         
        #      be defined as:    newline ([space]* newline])*
        # 
        # This way empty lines are eating away before the indentation count is activated.

        # -- 'space'
        x0 = StateMachine()
        x0.add_transition(x0.init_state_index, value.indentation_count_character_set(), 
                          AcceptanceF=True)
        # -- '[space]*'
        x1 = repeat.do(x0)
        # -- '[space]* newline'
        x2 = sequentialize.do([x1, value.newline_state_machine.get()])
        # -- '([space]* newline)*'
        x3 = repeat.do(x2)
        # -- 'newline ([space]* newline)*'
        x4 = sequentialize.do([value.newline_state_machine.get(), x3])
        # -- nfa to dfa; hopcroft optimization
        sm = hopcroft.do(nfa_to_dfa.do(x4), CreateNewStateMachineF=False)

        FileName = value.newline_state_machine.file_name
        LineN    = value.newline_state_machine.line_n
        action   = GeneratedCode(indentation_counter.do, FileName, LineN)

        action.data["indentation_setup"] = value

        sm = fit_state_machine(sm)
        sm.side_info = SideInfo(character_counter.get_newline_n(sm),
                                character_counter.get_character_n(sm))
        new_mode.add_match(value.newline_state_machine.pattern_str,
                           action, sm, Comment="indentation newline")

        # Announce the mode to which the setup belongs
        value.set_containing_mode_name(new_mode.name)
    else:
        value = read_option_value(fh)

    # The 'verify_word_in_list()' call must have ensured that the following holds
    assert lexer_mode.mode_option_info_db.has_key(identifier)

    # Is the option of the appropriate value?
    option_info = lexer_mode.mode_option_info_db[identifier]
    if option_info.domain != None and value not in option_info.domain:
        error_msg("Tried to set value '%s' for option '%s'. " % (Value, Option) + \
                  "Though, possible for this option are only: %s." % repr(oi.domain)[1:-1], fh)

    # Finally, set the option
    new_mode.add_option(identifier, value)

    return True

def parse_mode_element(new_mode, fh):
    """Returns: False, if a closing '}' has been found.
                True, else.
    """
    position = fh.tell()
    try:
        description = "Pattern or event handler name.\n" + \
                      "Missing closing '}' for end of mode"

        skip_whitespace(fh)
        # NOTE: Do not use 'read_word' since we need to continue directly after
        #       whitespace, if a regular expression is to be parsed.
        position = fh.tell()

        word = read_until_whitespace(fh)
        if word == "}": return False

        # -- check for 'on_entry', 'on_exit', ...
        if check_for_event_specification(word, fh, new_mode): return True

        fh.seek(position)
        description = "Start of mode element: regular expression"
        pattern, pattern_state_machine = regular_expression.parse(fh)

        if new_mode.has_pattern(pattern):
            previous = new_mode.get_pattern_action_pair(pattern)
            error_msg("Pattern has been defined twice.", fh, DontExitF=True)
            error_msg("First defined here.", 
                     previous.action().filename, previous.action().line_n)


        position    = fh.tell()
        description = "Start of mode element: code fragment for '%s'" % pattern

        parse_action_code(new_mode, fh, pattern, pattern_state_machine)

    except EndOfStreamException:
        fh.seek(position)
        error_msg("End of file reached while parsing %s." % description, fh)

    return True

def parse_action_code(new_mode, fh, pattern, pattern_state_machine):

    position = fh.tell()
    try:
        skip_whitespace(fh)
        position = fh.tell()
            
        code_obj = code_fragment.parse(fh, "regular expression", ErrorOnFailureF=False) 
        if code_obj != None:
            new_mode.add_match(pattern, code_obj, pattern_state_machine)
            return

        fh.seek(position)
        word = read_until_letter(fh, [";"])
        if word == "PRIORITY-MARK":
            # This mark 'lowers' the priority of a pattern to the priority of the current
            # pattern index (important for inherited patterns, that have higher precedence).
            # The parser already constructed a state machine for the pattern that is to
            # be assigned a new priority. Since, this machine is not used, let us just
            # use its id.
            fh.seek(-1, 1)
            check_or_quit(fh, ";", ". Since quex version 0.33.5 this is required.")
            new_mode.add_match_priority(pattern, pattern_state_machine, pattern_state_machine.get_id(), 
                                        fh.name, get_current_line_info_number(fh))

        elif word == "DELETION":
            # This mark deletes any pattern that was inherited with the same 'name'
            fh.seek(-1, 1)
            check_or_quit(fh, ";", ". Since quex version 0.33.5 this is required.")
            new_mode.add_match_deletion(pattern, pattern_state_machine, fh.name, get_current_line_info_number(fh))
            
        else:
            error_msg("Missing token '{', 'PRIORITY-MARK', 'DELETION', or '=>' after '%s'.\n" % pattern + \
                      "found: '%s'. Note, that since quex version 0.33.5 it is required to add a ';'\n" % word + \
                      "to the commands PRIORITY-MARK and DELETION.", fh)


    except EndOfStreamException:
        fh.seek(position)
        error_msg("End of file reached while parsing action code for pattern.", fh)

def check_for_event_specification(word, fh, new_mode):
    pos = fh.tell()

    # Allow '<<EOF>>' and '<<FAIL>>' out of respect for classical tools like 'lex'
    if   word == "<<EOF>>":                  word = "on_end_of_stream"
    elif word == "<<FAIL>>":                 word = "on_failure"
    elif len(word) < 3 or word[:3] != "on_": return False

    comment = "Unknown event handler '%s'. \n" % word + \
              "Note, that any pattern starting with 'on_' is considered an event handler.\n" + \
              "use double quotes to bracket patterns that start with 'on_'."

    __general_validate(fh, new_mode, word, pos)
    verify_word_in_list(word, lexer_mode.event_handler_db.keys(), comment, fh)
    __validate_required_token_policy_queue(word, fh, pos)

    continue_f = True
    if word == "on_end_of_stream":
        # When a termination token is sent, no other token shall follow. 
        # => Enforce return from the analyzer! Do not allow CONTINUE!
        continue_f = False

    new_mode.events[word] = code_fragment.parse(fh, "%s::%s event handler" % (new_mode.name, word),
                                                ContinueF=continue_f)

    return True

def __general_validate(fh, Mode, Name, pos):
    if Name == "on_indentation":
        fh.seek(pos)
        error_msg("Definition of 'on_indentation' is no longer supported since version 0.51.1.\n"
                  "Please, use 'on_indent' for the event of an opening indentation, 'on_dedent'\n"
                  "for closing indentation, and 'on_nodent' for no change in indentation.", fh) 


    def error_dedent_and_ndedent(code_fragment, A, B):
        filename = "(unknown)"
        line_n   = "0"
        if hasattr(code_fragment, "filename"): filename = code_fragment.filename
        if hasattr(code_fragment, "line_n"): line_n = code_fragment.line_n
        error_msg("Indentation event handler '%s' cannot be defined, because\n" % A,
                  fh, DontExitF=True, WarningF=False)
        error_msg("the alternative '%s' has already been defined." % B,
                  filename, line_n)

    if Name == "on_dedent" and Mode.events.has_key("on_n_dedent"):
        fh.seek(pos)
        code_fragment = Mode.events["on_n_dedent"]
        if code_fragment.get_code() != "":
            error_dedent_and_ndedent(code_fragment, "on_dedent", "on_n_dedent")
                      
    if Name == "on_n_dedent" and Mode.events.has_key("on_dedent"):
        fh.seek(pos)
        code_fragment = Mode.events["on_dedent"]
        if code_fragment.get_code() != "":
            error_dedent_and_ndedent(code_fragment, "on_n_dedent", "on_dedent")
                      
def __validate_required_token_policy_queue(Name, fh, pos):
    """Some handlers are better only used with token policy 'queue'."""

    if Name not in ["on_entry", "on_exit", 
                    "on_indent", "on_n_dedent", "on_dedent", "on_nodent", 
                    "on_indentation_bad", "on_indentation_error", 
                    "on_indentation"]: 
        return
    if Setup.token_policy == "queue":
        return
    if Setup.warning_disabled_no_token_queue_f:
        return

    fh.seek(pos)
    error_msg("Using '%s' event handler, while the token queue is disabled.\n" % Name + \
              "Use '--token-policy queue', so then tokens can be sent safer\n" + \
              "from inside this event handler. Disable this warning by command\n"
              "line option '--no-warning-on-no-token-queue'.", fh, DontExitF=True) 
