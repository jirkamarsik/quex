from copy import deepcopy
import quex.core_engine.state_machine.dead_end_analyzis as dead_end_analyzis
import quex.core_engine.generator.languages.address     as address 

class StateMachineDecorator:
    def __init__(self, SM, Name, PostContextSM_ID_List, 
                 BackwardLexingF, BackwardInputPositionDetectionF):
        assert SM.__class__.__name__ == "StateMachine"
        assert Name != ""
        assert type(BackwardInputPositionDetectionF) == bool
        assert type(BackwardLexingF) == bool
        assert not BackwardInputPositionDetectionF or BackwardLexingF == True, \
               "BackwardInputPositionDetectionF can only be set if BackwardLexingF is set."
        assert type(PostContextSM_ID_List) == list
        if BackwardInputPositionDetectionF: assert BackwardLexingF

        self.__name                   = Name
        self.__state_machine          = SM
        self.__post_condition_id_list = deepcopy(PostContextSM_ID_List)
        self.__post_condition_id_list.sort()

        self.__mode = "ForwardLexing"
        if BackwardLexingF:
            if BackwardInputPositionDetectionF: self.__mode = "BackwardInputPositionDetection"
            else:                               self.__mode = "BackwardLexing"

        # -- collect the 'dead end states' (states without further transitions)
        #    create a map from the 'dead end state
        self.__dead_end_state_db = dead_end_analyzis.do(SM)

        if BackwardLexingF:
            # During backward lexing (pre-condition, backward input position detection)
            # there are no dedicated terminal states in the first place.
            self.__directly_reached_terminal_id_list = []

    def name(self):
        return self.__name

    def mode(self):
        return self.__mode

    def backward_lexing_f(self):
        assert self.__mode in ["ForwardLexing", "BackwardLexing", "BackwardInputPositionDetection"]
        return self.__mode == "BackwardLexing"

    def forward_lexing_f(self):
        assert self.__mode in ["ForwardLexing", "BackwardLexing", "BackwardInputPositionDetection"]
        return self.__mode == "ForwardLexing"

    def backward_input_position_detection_f(self):
        assert self.__mode in ["ForwardLexing", "BackwardLexing", "BackwardInputPositionDetection"]
        return self.__mode == "BackwardInputPositionDetection" 

    def post_contexted_sm_id_list(self):
        return self.__post_condition_id_list

    def post_contexted_sm_n(self):
        return len(self.post_contexted_sm_id_list())

    def get_post_context_index(self, PostContextSM_ID):
        assert PostContextSM_ID in self.__post_condition_id_list, \
               "Error: request of post context state machine id which does not exist."
        return self.__post_condition_id_list.index(PostContextSM_ID)

    def sm(self):
        return self.__state_machine

    def dead_end_state_db(self):
        return self.__dead_end_state_db

    def directly_reached_terminal_id_list(self):
        result = []
        for info in self.__dead_end_state_db.itervalues():
            result.extend(info[1])
        return result

    def get_direct_transition_to_terminal_db(self):
        """Returns a dictionary that maps:

                state-index  -->   directly entered terminal

           where the 'state-index' is the index of a dead-end-state, i.e.
           a state that does nothing else but transiting into the terminal.
           Thus, this intermediate state can be shortcut.
        """
        result = {}
        for key, item in self.__dead_end_state_db.iteritems():
            # item[0] == False => State is a dead-end and an acceptance state
            if item[0] != False: continue
            assert len(item[1]) == 1
            result[key] = address.get_address("$terminal", item[1][0].state_machine_id)
        return result



