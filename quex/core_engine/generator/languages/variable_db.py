from copy import copy

class Variable:
    def __init__(self, Name, Type, ElementN, InitialValue, Condition=None, ConditionNegatedF=False, PriorityF=False):
        """ElementN == None --> scalar value
                    is int  --> array of dimension ElementN
        """
        assert type(ElementN) in [int, long] or None == ElementN, \
               "ElementN is of type '%s'" % repr(type(ElementN))

        self.name                = Name
        self.variable_type       = Type
        self.initial_value       = InitialValue
        self.element_n           = ElementN
        self.condition           = Condition
        self.condition_negated_f = ConditionNegatedF
        # Some variables need to be defined before others --> Set some to 'prior'
        self.priority_f          = PriorityF


_candidate_db = {
# Name                             Type(0),                         InitialValue(2),                    PriorityF(3)
"input":                          ["QUEX_TYPE_CHARACTER",           "(QUEX_TYPE_CHARACTER)(0x00)",      False],
"target_state_index":             ["QUEX_TYPE_GOTO_LABEL",          "((QUEX_TYPE_CHARACTER)0x0)",       False],
"target_state_else_index":        ["QUEX_TYPE_GOTO_LABEL",          "((QUEX_TYPE_CHARACTER)0x0)",       False],
"last_acceptance":                ["QUEX_TYPE_GOTO_LABEL",          None,                               False],
"last_acceptance_input_position": ["QUEX_TYPE_CHARACTER_POSITION",  "((QUEX_TYPE_CHARACTER*)0x00)",     False],
"PostContextStartPositionN":      ["const size_t",                  None,                               False],
"post_context_start_position":    ["QUEX_TYPE_CHARACTER_POSITION",  None,                               False],
"pre_context_%i_fulfilled_f":     ["int",                           "0",                                False], 
"end_of_core_pattern_position":   ["QUEX_TYPE_CHARACTER_POSITION",  "((QUEX_TYPE_CHARACTER*)0x0)",      False],
#                                 
# (*) Path Compression
"path_iterator":                  ["const QUEX_TYPE_CHARACTER*",    "((QUEX_TYPE_CHARACTER*)0x0)",      False],
"path_end_state":                 ["QUEX_TYPE_GOTO_LABEL",          "QUEX_GOTO_STATE_LABEL_INIT_VALUE", False], 
"path_%i":                        ["const QUEX_TYPE_CHARACTER*",    None,                               False],
"path_walker_%i_base":            ["const QUEX_TYPE_CHARACTER",     None,                               True],
"path_walker_%i_state":           ["const QUEX_TYPE_GOTO_LABEL",    None,                               False],
#
# (*) Template Compression
"template_state_key":                       ["ptrdiff_t",                     "(ptrdiff_t)0",           False],
"template_%i_target_%i":                    ["const QUEX_TYPE_GOTO_LABEL",    None,                     False],
"template_%i_map_state_key_to_state_index": ["const QUEX_TYPE_GOTO_LABEL",    None,                     False],
}

class VariableDB:

    def __init__(self):
        self.__db = {}

    def init(self, InitialDB=None):
        if InitialDB == None: self.__db.clear()
        else:                 self.__db = copy(InitialDB)

    def get(self):
        return self.__db

    def __enter(self, Name, Type, ElementN, InitialValues, Condition, ConditionNegatedF, PriorityF):
        # (*) Determine unique key for Name, Condition, and ConditionNegatedF.
        if Condition == None: 
            key = Name
        else:
            key = "%s/%s" % (Condition, Name)
            if ConditionNegatedF: key = "!" + key

        # (*) Enter the variable into the database
        self.__db[key] = Variable(Name, Type, ElementN, InitialValues, Condition, ConditionNegatedF, PriorityF)

    def __condition(self, Condition_ComputedGoto):
        if Condition_ComputedGoto == None:
            return None, None
        else:
            assert type(Condition_ComputedGoto) == bool
            return "QUEX_OPTION_COMPUTED_GOTOS", not Condition_ComputedGoto

    def require(self, Name, Initial=None, Index=None, Condition_ComputedGoto=None):
        global _candidate_db

        condition, condition_negated_f = self.__condition(Condition_ComputedGoto)

        # Name --> Type(0), InitialValue(1), PriorityF(2)
        x = _candidate_db[Name]

        if Index != None:   Name = Name % Index

        if Initial != None: initial = Initial
        else:               initial = x[1]

        self.__enter(Name, x[0], None, initial, condition, condition_negated_f, x[2])

    def require_array(self, Name, ElementN, Initial, Index=None, Condition_ComputedGoto=None):
        global _candidate_db

        condition, condition_negated_f = self.__condition(Condition_ComputedGoto)

        # Name --> Type(0), InitialValue(1), PriorityF(2)
        x = _candidate_db[Name]

        if Index != None: Name = Name % Index
        self.__enter(Name, x[0], ElementN, Initial, condition, condition_negated_f, x[2])

variable_db = VariableDB()
