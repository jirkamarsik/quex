################################################################################
#! /usr/bin/env python
# Quex is  free software;  you can  redistribute it and/or  modify it  under the
# terms  of the  GNU Lesser  General  Public License  as published  by the  Free
# Software Foundation;  either version 2.1 of  the License, or  (at your option)
# any later version.
# 
# This software is  distributed in the hope that it will  be useful, but WITHOUT
# ANY WARRANTY; without even the  implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the  GNU Lesser General Public License for more
# details.
# 
# You should have received a copy of the GNU Lesser General Public License along
# with this  library; if not,  write to the  Free Software Foundation,  Inc., 59
# Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# (C) 2006, 2007 Frank-Rene Schaefer
#
################################################################################
import sys
import os

from copy                import copy, deepcopy
from quex.frs_py.file_in import error_msg, verify_word_in_list, get_current_line_info_number
from quex.core_engine.generator.action_info import *
import quex.core_engine.state_machine.subset_checker   as subset_checker
import quex.core_engine.state_machine.identity_checker as identity_checker
import quex.core_engine.state_machine.transformation   as transformation
import quex.core_engine.state_machine.index            as index
from   quex.core_engine.interval_handling              import Interval

# ModeDescription/Mode Objects:
#
# During parsing 'ModeDescription' objects are generated. Once parsing is over, 
# the descriptions are translated into 'real' mode objects where code can be generated
# from. All matters of inheritance and pattern resolution are handled in the
# transition from description to real mode.
#-----------------------------------------------------------------------------------------
# mode_description_db: storing the mode information into a dictionary:
#                      key  = mode name
#                      item = ModeDescription object
#-----------------------------------------------------------------------------------------
mode_description_db = {}

#-----------------------------------------------------------------------------------------
# mode_db: storing the mode information into a dictionary:
#            key  = mode name
#            item = Mode object
#-----------------------------------------------------------------------------------------
mode_db = {}

class OptionInfo:
    """This type is used only in context of a dictionary, the key
       to the dictionary is the option's name."""
    def __init__(self, Type, Domain=None, Default=-1):
        # self.name = Option see comment above
        self.type          = Type
        self.domain        = Domain
        self.default_value = Default

class ModeDescription:
    def __init__(self, Name, Filename, LineN):
        global mode_description_db

        self.filename = Filename
        self.line_n   = LineN

        self.name       = Name
        self.base_modes = []
        # Read pattern information into dictionary object. This allows for the following:
        # (i)   inheritance of pattern behavior in different modes.
        # (ii)  'virtual' patterns in the sense that their behavior can be
        #       overwritten.
        self.__matches = {}            # genuine patterns as specified in the mode declaration

        self.__repriorization_db = {}  # patterns of the base class to be reprioritized
        #                              # map: pattern --> new pattern index
        self.__deletion_db       = {}  # patterns of the base class to be deleted

        # The list of actual pattern action pairs is constructed inside the function
        # '__post_process(...)'. Function 'get_pattern_action_pairs(...) calls it
        # in case that this variable is still [].
        self.__pattern_action_pair_list = []  

        # (*) Default Options
        self.options = {}      
        for name, descr in mode_option_info_db.items():
            # Not only copy the reference, copy the default value object!
            self.options[name] = deepcopy(descr.default_value)

        # (*) Default Event Handler: Empty
        self.events = {}
        for name in event_handler_db.keys():
            self.events[name] = CodeFragment()

        # Register ModeDescription at the mode database
        mode_description_db[Name] = self

    def add_match(self, Pattern, Action, PatternStateMachine, Comment=""):
        assert PatternStateMachine.is_DFA_compliant()
        assert PatternStateMachine.side_info != None, \
               "No side info for '%s'" % Pattern

        if self.__matches.has_key(Pattern):
            error_msg("Pattern '%s' appeared twice in mode definition.\n" % Pattern + \
                      "Only the last definition is considered.", 
                      Action.filename, Action.line_n, DontExitF=True)

        if len(PatternStateMachine.get_orphaned_state_index_list()) != 0:
            error_msg("Pattern '%s' resulted in state machine with orphan states.\n" % Pattern + \
                      "(After Transformation to internal encoding).\n" + \
                      "Please, submit a bug at quex.sourceforge.net.", 
                      DontExitF=True, WarningF=True)

        PatternStateMachine = transformation.do(PatternStateMachine)

        if len(PatternStateMachine.get_orphaned_state_index_list()) != 0:
            error_msg("Pattern '%s' resulted in state machine with orphan states.\n" % Pattern + \
                      "(After Transformation to internal encoding).\n" + \
                      "Please, submit a bug at quex.sourceforge.net.", 
                      DontExitF=False, WarningF=True)

        self.__matches[Pattern] = PatternActionInfo(PatternStateMachine, Action, Pattern, 
                                                    ModeName=self.name, Comment=Comment)

    def add_match_priority(self, Pattern, PatternStateMachine, PatternIdx, FileName, LineN):
        if self.__matches.has_key(Pattern):
            error_msg("Pattern '%s' appeared twice in mode definition.\n" % Pattern + \
                      "Only this priority mark is considered.", FileName, LineN)

        PatternStateMachine = transformation.do(PatternStateMachine)
        self.__repriorization_db[Pattern] = [PatternStateMachine, FileName, LineN, PatternIdx]

    def add_match_deletion(self, Pattern, PatternStateMachine, FileName, LineN):
        if self.__matches.has_key(Pattern):
            error_msg("Deletion of '%s' which appeared before in same mode.\n" % Pattern + \
                      "Deletion of pattern.", FileName, LineN)

        PatternStateMachine = transformation.do(PatternStateMachine)
        self.__deletion_db[Pattern] = [PatternStateMachine, FileName, LineN]

    def add_option(self, Option, Value):
        """ SANITY CHECK:
                -- which options are concatinated to a list
                -- which ones are replaced
                -- what are the values of the options
        """
        assert mode_option_info_db.has_key(Option)

        option_info = mode_option_info_db[Option]
        if option_info.type == "list":
            self.options.setdefault(Option, []).append(Value)
        else:
            if option_info.domain != None: assert Value in option_info.domain
            self.options[Option] = Value

    def get_pattern_action_pair(self, PatternStr):
        return self.__matches[PatternStr]

    def get_match_list(self):
        return self.__matches.values()

    def get_repriorization_db(self):
        return self.__repriorization_db

    def get_deletion_db(self):
        return self.__deletion_db

    def has_event_handler(self):
        for fragment in self.events.values():
            if fragment.get_code() != "": return True
        return False

    def has_pattern(self, PatternStr):
        return self.__matches.has_key(PatternStr)

    def has_own_matches(self):
        return len(self.__matches) != 0

    def has_matches(self):
        if self.__matches != {}: return True

        for name in self.base_modes:
           if mode_description_db[name].has_matches(): return True

        return False

class Mode:
    def __init__(self, Other):
        """Translate a ModeDescription into a real Mode. Here is the place were 
           all rules of inheritance mechanisms and pattern precedence are applied.
        """
        assert isinstance(Other, ModeDescription)
        self.name     = Other.name
        self.filename = Other.filename
        self.line_n   = Other.line_n
        self.options  = Other.options

        self.__base_mode_sequence = []
        self.__determine_base_mode_sequence(Other, [])

        # (1) Collect Event Handlers
        self.__event_handler_code_fragment_list = {}
        self.__collect_event_handler()
        
        # (2) Collect Pattern/Action Pairs
        self.__history_repriorization = []
        self.__history_deletion       = []
        self.__pattern_action_pair_list = self.__collect_pattern_action_pairs()

        # (3) Collection Options
        self.__collect_options()

    def insert_code_fragment_at_front(self, EventName, TheCodeFragment):
        assert isinstance(TheCodeFragment, CodeFragment)
        assert EventName == "on_end_of_stream"
        self.__event_handler_code_fragment_list[EventName].insert(0, TheCodeFragment)

    def set_code_fragment_list(self, EventName, TheCodeFragment):
        assert isinstance(TheCodeFragment, CodeFragment)
        assert EventName in ["on_end_of_stream", "on_failure"]
        assert self.__event_handler_code_fragment_list[EventName] == []
        self.__event_handler_code_fragment_list[EventName] = [TheCodeFragment]

    def has_base_mode(self):
        return len(self.__base_mode_sequence) != 1

    def has_code_fragment_list(self, EventName):
        assert self.__event_handler_code_fragment_list.has_key(EventName)
        return len(self.__event_handler_code_fragment_list[EventName]) != 0

    def get_base_mode_sequence(self):
        return self.__base_mode_sequence

    def get_base_mode_name_list(self):
        return map(lambda mode: mode.name, self.__base_mode_sequence)

    def get_code_fragment_list(self, EventName):
        assert self.__event_handler_code_fragment_list.has_key(EventName)
        return self.__event_handler_code_fragment_list[EventName]

    def get_pattern_action_pair_list(self):
        return self.__pattern_action_pair_list

    def get_documentation(self):
        L = max(map(lambda mode: len(mode.name), self.__base_mode_sequence))
        txt  = "\nMODE: %s\n" % self.name

        txt += "\n"
        if len(self.__base_mode_sequence) != 1:
            txt += "    BASE MODE SEQUENCE:\n"
            base_mode_name_list = map(lambda mode: mode.name, self.__base_mode_sequence[:-1])
            base_mode_name_list.reverse()
            for name in base_mode_name_list:
                txt += "      %s\n" % name
            txt += "\n"

        if self.__history_deletion != []:
            txt += "    DELETION ACTIONS:\n"
            for entry in self.__history_deletion:
                txt += "      %s:  %s%s  (from mode %s)\n" % \
                       (entry[0], " " * (L - len(self.name)), entry[1], entry[2])
            txt += "\n"

        if self.__history_repriorization != []:
            txt += "    PRIORITY-MARK ACTIONS:\n"
            self.__history_repriorization.sort(lambda x, y: cmp(x[4], y[4]))
            for entry in self.__history_repriorization:
                txt += "      %s: %s%s  (from mode %s)  (%i) --> (%i)\n" % \
                       (entry[0], " " * (L - len(self.name)), entry[1], entry[2], entry[3], entry[4])
            txt += "\n"

        if self.__pattern_action_pair_list != []:
            txt += "    PATTERN-ACTION PAIRS:\n"
            self.__pattern_action_pair_list.sort(lambda x, y:
                            cmp(x.pattern_state_machine().get_id(),
                                y.pattern_state_machine().get_id()))
            for pattern_action_pair in self.__pattern_action_pair_list:
                txt += "      (%3i) %s: %s%s\n" % \
                       (pattern_action_pair.pattern_state_machine().get_id(),
                        pattern_action_pair.mode_name, " " * (L - len(self.name)), 
                        pattern_action_pair.pattern)
            txt += "\n"

        return txt

    def default_indentation_handler_sufficient(Mode):
        """If no user defined indentation handler is defined, then the 
           default token handler is sufficient.
        """
        return     not Mode.has_code_fragment_list("on_indentation_error") \
               and not Mode.has_code_fragment_list("on_indentation_bad")   \
               and not Mode.has_code_fragment_list("on_indent")            \
               and not Mode.has_code_fragment_list("on_dedent")            \
               and not Mode.has_code_fragment_list("on_nodent") 
           
    def __determine_base_mode_sequence(self, ModeDescr, InheritancePath):
        """Determine the sequence of base modes. The type of sequencing determines
           also the pattern precedence. The 'deep first' scheme is chosen here. For
           example a mode hierarchie of

                                       A
                                     /   \ 
                                    B     C
                                   / \   / \
                                  D  E  F   G

           results in a sequence: (A, B, D, E, C, F, G).reverse()

           This means, that patterns and event handlers of 'E' have precedence over
           'C' because they are the childs of a preceding base mode.

           This function detects circular inheritance.
        """
        if ModeDescr.name in InheritancePath:
            msg = "mode '%s'\n" % InheritancePath[0]
            for mode_name in InheritancePath[InheritancePath.index(ModeDescr.name) + 1:]:
                msg += "   inherits mode '%s'\n" % mode_name
            msg += "   inherits mode '%s'" % ModeDescr.name

            error_msg("circular inheritance detected:\n" + msg, ModeDescr.filename, ModeDescr.line_n)

        base_mode_name_list_reversed = deepcopy(ModeDescr.base_modes)
        #base_mode_name_list_reversed.reverse()
        for name in base_mode_name_list_reversed:
            # -- does mode exist?
            verify_word_in_list(name, mode_description_db.keys(),
                                "Mode '%s' inherits mode '%s' which does not exist." % (ModeDescr.name, name),
                                ModeDescr.filename, ModeDescr.line_n)

            if name in map(lambda m: m.name, self.__base_mode_sequence): continue

            # -- grab the mode description
            mode_descr = mode_description_db[name]
            self.__determine_base_mode_sequence(mode_descr, InheritancePath + [ModeDescr.name])

        self.__base_mode_sequence.append(ModeDescr)

        return self.__base_mode_sequence

    def __collect_event_handler(self):
        """Collect event handlers from base mode and the current mode.
           Event handlers of the most 'base' mode come first, then the 
           derived event handlers. 

           See '__determine_base_mode_sequence(...) for details about the line-up.
        """
        for event_name in event_handler_db.keys():
            self.__event_handler_code_fragment_list[event_name] = []

        for mode_descr in self.__base_mode_sequence:
            
            for event_name in event_handler_db.keys():
                fragment = mode_descr.events[event_name]
                if fragment != None and fragment.get_code() != "":
                    self.__event_handler_code_fragment_list[event_name].append(fragment)

        return 

    def __collect_pattern_action_pairs(self):
        """Collect patterns of all inherited modes. Patterns are like virtual functions
           in C++ or other object oriented programming languages. Also, the patterns of the
           uppest mode has the highest priority, i.e. comes first.
        """
        def __ensure_pattern_indeces_follow_precedence(MatchList, RepriorizationDB, PrevMaxPatternIndex):
            """When a derived mode is defined before its base mode, then its pattern ids
               (according to the time they were created) are lower than thos of the base
               mode. This would imply that they have higher precedence, which is against
               our matching rules. Here, pattern ids are adapted to be higher than a certain
               minimum, and follow the same precedence sequence.
            """
            # Patterns of a 'lower precedence mode' **must** have higher pattern ids
            # that patterns of a 'higher precedence mode'. This is to ensure that 
            # base mode patterns precede derived mode patterns.
            min_pattern_index = min(map(lambda match: match.pattern_state_machine().get_id(),
                                        MatchList))
            if min_pattern_index > PrevMaxPatternIndex:
                return MatchList, RepriorizationDB

            match_list        = deepcopy(MatchList)
            repriorization_db = deepcopy(RepriorizationDB)

            # Determine the offset for each pattern
            offset = PrevMaxPatternIndex + 1 - min_pattern_index
            assert offset >= 1

            # Assign new pattern ids starting from MinPatternID
            for match in match_list:
                current_pattern_id = match.pattern_state_machine().get_id()
                match.pattern_state_machine().core().set_id(current_pattern_id + offset)
            
            # The reprioritizations must also be adapted
            ## for key, info in repriorization_db.items():
            ##    print "##reprio:", key, info[-1], info[-1] + offset
            for info in repriorization_db.items():
                info[-1] += offset

            return match_list, repriorization_db 
                                             
        def __handle_deletion_and_repriorization(CurrentModeName, pattern_action_pair_list, 
                                                 repriorization_db, deletion_db):
            def __validate_marks(DB, DoneDB, CommentStr):
                ok_f = True
                for pattern, info in DB.items():
                    if DoneDB.has_key(pattern): continue
                    ok_f = False
                    error_msg("Pattern '%s' was marked %s but does not\n" % (pattern, CommentStr) + \
                              "exist in any base mode of mode '%s'." % self.name,
                              info[1], info[2], DontExitF=True, WarningF=False)
                return ok_f

            def __is_in_patterns(AllegedIdenticalSM, MyDB):
                for pattern, info in MyDB.items():
                    sm = info[0]
                    if identity_checker.do(AllegedIdenticalSM, sm): return pattern
                return ""

            # DELETION / PRIORITY-MARK 
            deletion_done_db       = {}
            repriorization_done_db = {}
            i    = 0
            size = len(pattern_action_pair_list)
            while i < size:
                match         = pattern_action_pair_list[i]
                state_machine = match.pattern_state_machine()

                found_pattern = __is_in_patterns(state_machine, deletion_db)
                if found_pattern != "":
                    # Delete pattern from the list of pattern action pairs
                    del pattern_action_pair_list[i]
                    size -= 1
                    # Mark 'deletion applied'
                    deletion_done_db[found_pattern] = True
                    self.__history_deletion.append([CurrentModeName, match.pattern, match.mode_name])
                    continue

                found_pattern = __is_in_patterns(state_machine, repriorization_db)
                if found_pattern != "":
                    # Adapt the pattern index, this automatically adapts the match precedence
                    old_state_machine_id = state_machine.get_id()
                    new_state_machine_id = repriorization_db[found_pattern][-1]
                    new_match = deepcopy(match)
                    new_match.pattern_state_machine().core().set_id(new_state_machine_id)
                    pattern_action_pair_list[i] = new_match
                    # Mark 'repriorization applied'
                    repriorization_done_db[found_pattern] = True
                    self.__history_repriorization.append([CurrentModeName, match.pattern, match.mode_name,
                                                          old_state_machine_id, new_state_machine_id]) 
                i += 1

            # Ensure that all mentioned marks really had some effect.
            if    not __validate_marks(deletion_db, deletion_done_db, "for DELETION")  \
               or not __validate_marks(repriorization_db, repriorization_done_db, "with PRIORITY-MARK"):
                error_msg("Abort.")
            return

        def __add_new_pattern_action_pair(pattern_action_pair_list, PatternActionPair):
            state_machine = PatternActionPair.pattern_state_machine()
            pattern       = PatternActionPair.pattern

            for earlier_match in pattern_action_pair_list:
                if earlier_match.pattern_state_machine().get_id() > state_machine.get_id(): continue
                if subset_checker.do(earlier_match.pattern_state_machine(), state_machine) == False: continue
                file_name, line_n = earlier_match.get_action_location()
                error_msg("Pattern '%s' matches a superset of what is matched by" % 
                          earlier_match.pattern, file_name, line_n,
                          DontExitF=True, WarningF=False) 
                file_name, line_n = PatternActionPair.get_action_location()
                error_msg("pattern '%s' while the former has precedence.\n" % \
                          pattern + "The latter can never match.\n" + \
                          "You may switch the sequence of definition to avoid this error.",
                          file_name, line_n)
                # Here we already quit by error_msg(...).
            else:
                # Shallow copy is enough! Later on, there might be actions that 
                # generate source code, and then the source code takes the place of
                # the action. For this to work, inherited actions must be de-antangled.
                pattern_action_pair_list.append(copy(PatternActionPair))

        result                 = []
        prev_max_pattern_index = -1
        # Iterate from the base to the top (include this mode's pattern)
        for mode_descr in self.__base_mode_sequence:

            repriorization_db = {}
            consider_pattern_action_pairs_f = mode_descr.has_own_matches()
            if consider_pattern_action_pairs_f:
                match_list, repriorization_db = \
                        __ensure_pattern_indeces_follow_precedence(mode_descr.get_match_list(),
                                                                   mode_descr.get_repriorization_db(),
                                                                   prev_max_pattern_index)

            # Delete/Repriorize patterns from more basic modes
            __handle_deletion_and_repriorization(mode_descr.name, result, 
                                                 repriorization_db, mode_descr.get_deletion_db())

            if consider_pattern_action_pairs_f:
                # Add the new pattern action pairs
                for pattern_action_pair in match_list:
                    __add_new_pattern_action_pair(result, pattern_action_pair)

                # Determine the max pattern index at this level of inheritance
                prev_max_pattern_index = max([prev_max_pattern_index] + \
                                             map(lambda match: match.pattern_state_machine().get_id(),
                                             match_list))


        return result

    def __collect_options(self):
        for mode in self.__base_mode_sequence[:-1]:
            for name, option_descr in mode_option_info_db.items():
                if option_descr.type != "list": continue
                # Need to decouple by means of 'deepcopy'
                self.options.setdefault(name, []).extend(mode.options[name])

#-----------------------------------------------------------------------------------------
# mode option information/format: 
#-----------------------------------------------------------------------------------------
mode_option_info_db = {
   # -- a mode can be inheritable or not or only inheritable. if a mode
   #    is only inheritable it is not printed on its on, only as a base
   #    mode for another mode. default is 'yes'
   "inheritable":       OptionInfo("single", ["no", "yes", "only"], Default="yes"),
   # -- a mode can restrict the possible modes to exit to. this for the
   #    sake of clarity. if no exit is explicitly mentioned all modes are
   #    possible. if it is tried to transit to a mode which is not in
   #    the list of explicitly stated exits, an error occurs.
   #    entrys work respectively.
   "exit":              OptionInfo("list", Default=[]),
   "entry":             OptionInfo("list", Default=[]),
   # -- a mode can restrict the exits and entrys explicitly mentioned
   #    then, a derived mode cannot add now exits or entrys
   "restrict":          OptionInfo("list", ["exit", "entry"], Default=[]),
   # -- a mode can have 'skippers' that effectivels skip ranges that are out of interest.
   "skip":              OptionInfo("list", Default=[]), # "multiple: RE-character-set
   "skip_range":        OptionInfo("list", Default=[]), # "multiple: RE-character-string RE-character-string
   "skip_nested_range": OptionInfo("list", Default=[]), # "multiple: RE-character-string RE-character-string
   # -- indentation setup information
   "indentation":       OptionInfo("single", Default=None),
}
#-----------------------------------------------------------------------------------------
# event handler list: 
#-----------------------------------------------------------------------------------------
event_handler_db = {
        "on_entry":     "On entry of a mode.",
        "on_exit":      "On exit of a mode.", 
        "on_indent":                 "On opening indentation.",
        "on_nodent":                 "On same indentation.",
        "on_dedent":                 "On closing indentation'.",
        "on_n_dedent":               "On closing indentation'.",
        "on_indentation_error":      "Closing indentation on non-border.",
        "on_indentation_bad":        "On bad character in indentation.",
        "on_indentation":            "General Indentation Handler.",
        "on_match":                  "On each match.",
        "on_failure":                "In case that no pattern matches.",
        "on_skip_range_open":        "On missing skip range delimiter.",
        "on_end_of_stream":          "On end of file/stream.",
        }

class LocalizedParameter:
    def __init__(self, Name, Default, FH=-1):
        self.name      = Name
        self.__default = Default
        if FH == -1:
            self.__value   = None
            self.file_name = ""
            self.line_n    = -1
        else:
            self.__value   = Default
            self.file_name = FH.name
            self.line_n    = get_current_line_info_number(FH)

    def set(self, Value, fh):
        if self.__value != None:
            error_msg("%s has been defined more than once.\n" % self.name, fh, DontExitF=True)
            error_msg("previous definition has been here.\n", self.file_name, self.line_n)
                      
        self.__value   = Value
        self.file_name = fh.name
        self.line_n    = get_current_line_info_number(fh)

    def get(self):
        if self.__value != None: return self.__value
        return self.__default

#-----------------------------------------------------------------------------------------
# initial_mode: mode in which the lexcial analyser shall start
#-----------------------------------------------------------------------------------------
initial_mode = CodeFragment()

#-----------------------------------------------------------------------------------------
# header: code fragment that is to be pasted before mode transitions
#         and pattern action pairs (e.g. '#include<something>'
#-----------------------------------------------------------------------------------------
header = CodeFragment()

#-----------------------------------------------------------------------------------------
# class_body_extension: code fragment that is to be pasted inside the class definition
#                       of the lexical analyser class.
#-----------------------------------------------------------------------------------------
class_body_extension = CodeFragment()

#-----------------------------------------------------------------------------------------
# class_constructor_extension: code fragment that is to be pasted inside the lexer class constructor
#-----------------------------------------------------------------------------------------
class_constructor_extension = CodeFragment()

#-----------------------------------------------------------------------------------------
# memento_extension: fragment to be pasted into the memento  class's body.
#-----------------------------------------------------------------------------------------
memento_class_extension = CodeFragment()
#-----------------------------------------------------------------------------------------
# memento_pack_extension: fragment to be pasted into the function that packs the
#                         lexical analyzer state in a memento.
#-----------------------------------------------------------------------------------------
memento_pack_extension = CodeFragment()
#-----------------------------------------------------------------------------------------
# memento_unpack_extension: fragment to be pasted into the function that unpacks the
#                           lexical analyzer state in a memento.
#-----------------------------------------------------------------------------------------
memento_unpack_extension = CodeFragment()


fragment_db = {
        "header":         "header",
        "body":           "class_body_extension",
        "init":           "class_constructor_extension",
        "memento":        "memento_class_extension",
        "memento_pack":   "memento_pack_extension",
        "memento_unpack": "memento_unpack_extension",
}

class PatternShorthand:
    def __init__(self, Name="", StateMachine="", Filename="", LineN=-1, RE=""):
        assert StateMachine.__class__.__name__ == "StateMachine"
        assert StateMachine.has_origins() == False

        self.name               = Name
        self.__state_machine    = StateMachine
        self.filename           = Filename
        self.line_n             = LineN
        self.regular_expression = RE

    def get_state_machine(self):
        return self.__state_machine.clone()

    def get_character_set(self):
        if len(self.__state_machine.states) != 2: return None
        t = self.__state_machine.states[self.__state_machine.init_state_index].transitions()
        db = t.get_map()
        if len(db) != 1: return None
        return deepcopy(db[db.keys()[0]])
        

#-----------------------------------------------------------------------------------------
# shorthand_db: user defined names for regular expressions.
#               (this is what contained in the pattern file for flex-based engines.
#                it is only used with quex generated engines)   
#-----------------------------------------------------------------------------------------
shorthand_db = {}

#-----------------------------------------------------------------------------------------
# token_id_db: list of all defined token-ids together with the file position
#              where they are defined. See token_ide_maker, class TokenInfo.
#-----------------------------------------------------------------------------------------
token_id_db = {}


#-----------------------------------------------------------------------------------------
# token_id_implicit_list: Keep track of all token identifiers that ware defined 
#                         implicitly, i.e. not in a token section or in a token id file. 
#                         Each list element has three cells:
#                         [ Prefix-less Token ID, Line number in File, File Name]
#-----------------------------------------------------------------------------------------
token_id_implicit_list = []

#-----------------------------------------------------------------------------------------
# token_repetition_support: Quex can be told to return multiple times the same
#                           token before further analyzsis happens. For this,
#                           the engine needs to know how to read and write the
#                           repetition number in the token itself.
# If the 'token_repetition_token_id_list' == None, then the token repetition feature
# is disabled. Otherwise, token repetition in 'token-receiving.i' is enabled
# and the token id that can be repeated is 'token_repetition_token_id'.
#-----------------------------------------------------------------------------------------
token_repetition_token_id_list = ""

#-----------------------------------------------------------------------------------------
# token_type_definition: Object that defines a (user defined) token class.
#
#                        The first token_type section defines the variable as 
#                        a real 'TokenTypeDescriptor'.
#
#                        Default = None is detected by the 'quex_file_parser.py' and
#                        triggers the parsing of the default token type description. 
#          
#                        The setup_parser.py checks for the specification of a manually
#                        written token class file. If so then an object of type 
#                        'ManualTokenClassSetup' is assigned.
#-----------------------------------------------------------------------------------------
token_type_definition = None

#-----------------------------------------------------------------------------------------
# Helper functions about required features.
#-----------------------------------------------------------------------------------------
def requires_indentation_count(ModeDB):
    """Determine whether the lexical analyser needs indentation counting
       support. if one mode has an indentation handler, than indentation
       support must be provided.                                         
    """
    for mode in ModeDB.values():
        if    mode.has_code_fragment_list("on_indent")      \
           or mode.has_code_fragment_list("on_nodent")      \
           or mode.has_code_fragment_list("on_indentation") \
           or mode.has_code_fragment_list("on_dedent"):
            return True

        if mode.options["indentation"] != None:
            assert mode.options["indentation"].__class__.__name__ == "IndentationSetup"
            return True

    return False

def requires_begin_of_line_condition_support(ModeDB):
    """If one single pattern in one mode depends on begin of line, then
       the begin of line condition must be supported. Otherwise not.
    """
    for mode in ModeDB.values():
        pattern_action_pair_list = mode.get_pattern_action_pair_list()
        for info in pattern_action_pair_list:
            state_machine = info.pattern_state_machine()
            if state_machine.core().pre_context_begin_of_line_f():
                return True
    return False

