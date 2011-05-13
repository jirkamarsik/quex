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
################################################################################
#
from   quex.frs_py.file_in              import *
from   quex.output.cpp.token_id_maker   import TokenInfo
from   quex.exception                   import RegularExpressionException
import quex.lexer_mode               as lexer_mode
import quex.input.mode_definition    as mode_definition
import quex.input.token_type         as token_type_definition
import quex.input.regular_expression as regular_expression
import quex.input.code_fragment      as code_fragment
from   quex.input.setup             import setup as Setup
from   quex.core_engine.generator.action_info import UserCodeFragment

def do(file_list):
    global mode_db

    for file in file_list:
        fh = open_file_or_die(file, Codec="utf-8")

        # read all modes until end of file
        try:
            while 1 + 1 == 2:
                parse_section(fh)
        except EndOfStreamException:
            pass
        except RegularExpressionException, x:
            error_msg(x.message, fh)
        
    return lexer_mode.mode_description_db

def __parse_domain_of_whitespace_separated_elements(fh, CodeFragmentName, ElementNames, MinElementN):   
    """Returns list of lists, where 
     
         record_list[i][k]  means element 'k' of line 'i'

       NOTE: record_list[i][-1] contains the line 'i' as it appeared as a whole.
             record_list[i][-2] contains the line number of line in the given file.

    """       
    start_line_n = get_current_line_info_number(fh)
    if check(fh, "{") == False: 
        error_msg("missing '{' after %s statement" % CodeFragmentName, fh)
    #
    line_n = start_line_n       
    record_list = []
    while 1 + 1 == 2:
        line = fh.readline()
        line_n += 1
        #
        if line == "": 
            error_msg("found end of file while parsing a '%s' range.\n" % CodeFragmentName + \
                      "range started here.", fh, start_line_n)    
        line = line.strip()
        if line == "":                           continue           # empty line
        elif line[0] == '}':                     return record_list # end of define range
        elif len(line) > 1 and line[:2] == "//": continue           # comment

        # -- interpret line as list of whitespace separated record elements
        fields = line.split()    
        if fields != [] and is_identifier(fields[0]) == False:
            error_msg("'%s' is not a valid identifier." % fields[0], fh)

        if len(fields) < MinElementN: 
            format_str = ""
            for element in ElementNames:
                format_str += "%s   " % element 
            error_msg("syntax error in definition list\n" + \
                      "format: %s  NEWLINE" % format_str , fh, line_n)
        record_list.append(fields + [line_n, line])    

    assert True == False, "this code section should have never been reached!"


#

default_token_type_definition_triggered_by_mode_definition_f = False

def parse_section(fh):
    global default_token_type_definition_triggered_by_mode_definition_f

    # NOTE: End of File is supposed to be reached when trying to read a new
    #       section. Thus, the end-of-file catcher does not encompass the beginning.
    position = fh.tell()
    skip_whitespace(fh)
    word = read_identifier(fh)
    if word == "":
        error_msg("Missing section title.", fh)

    SectionTitleList = ["start", "define", "token", "mode", "repeated_token", "token_type" ] + lexer_mode.fragment_db.keys()

    verify_word_in_list(word, SectionTitleList, "Unknown quex section '%s'" % word, fh)
    try:
        # (*) determine what is defined
        #
        #     -- 'mode { ... }'     => define a mode
        #     -- 'start = ...;'     => define the name of the initial mode
        #     -- 'header { ... }'   => define code that is to be pasted on top
        #                              of the engine (e.g. "#include<...>")
        #     -- 'body { ... }'     => define code that is to be pasted in the class' body
        #                              of the engine (e.g. "public: int  my_member;")
        #     -- 'init { ... }'     => define code that is to be pasted in the class' constructors
        #                              of the engine (e.g. "my_member = -1;")
        #     -- 'define { ... }'   => define patterns shorthands such as IDENTIFIER for [a-z]+
        #     -- 'repeated_token_id = QUEX_TKN_ ...;' => enables token repetition, defines
        #                                                the token id to be repeated.
        #     -- 'token { ... }'    => define token ids
        #     -- 'token_type { ... }'  => define a customized token type
        #
        if word in lexer_mode.fragment_db.keys():
            element_name = lexer_mode.fragment_db[word]
            fragment     = code_fragment.parse(fh, word, AllowBriefTokenSenderF=False)        
            lexer_mode.__dict__[element_name] = fragment
            return

        elif word == "start":
            mode_name = parse_identifier_assignment(fh)
            if mode_name == "":
                error_msg("Missing mode_name after 'start ='", fh)
            elif lexer_mode.initial_mode.get_pure_code() != "":
                error_msg("start mode defined more than once!", fh, DontExitF=True)
                error_msg("previously defined here",
                          lexer_mode.initial_mode.filename,
                          lexer_mode.initial_mode.line_n)
        
            lexer_mode.initial_mode = UserCodeFragment(mode_name, fh.name, 
                                                       get_current_line_info_number(fh))
            return

        elif word == "repeated_token":
            lexer_mode.token_repetition_token_id_list = parse_token_id_definitions(fh, NamesOnlyF=True)
            for token_name in lexer_mode.token_repetition_token_id_list:
                verify_word_in_list(token_name[len(Setup.token_id_prefix):],
                                    lexer_mode.token_id_db.keys(),
                                    "Token ID '%s' not yet defined." % token_name,
                                    fh, ExitF=False)
            return
            
        elif word == "define":
            parse_pattern_name_definitions(fh)
            return

        elif word == "token":       
            parse_token_id_definitions(fh)
            return

        elif word == "token_type":       

            if Setup.token_class_file != "":
                error_msg("Token type definition inadmissible while specifying on the command line\n" + \
                          "the file %s to contain a manually written token class." % repr(Setup.token_class_file),
                          fh)
       
            if lexer_mode.token_type_definition == None:
                lexer_mode.token_type_definition = token_type_definition.parse(fh)
                return

            # Error case:
            if default_token_type_definition_triggered_by_mode_definition_f:
                error_msg("Section 'token_type' must appear before first mode definition.", fh)
            else:
                error_msg("Section 'token_type' has been defined twice.", fh, DontExitF=True)
                error_msg("Previously defined here.",
                          lexer_mode.token_type_definition.file_name_of_token_type_definition,
                          lexer_mode.token_type_definition.line_n_of_token_type_definition)
            return

        elif word == "mode":
            # When the first mode is parsed then a token_type definition must be 
            # present. If not, the default token type definition is considered.
            if lexer_mode.token_type_definition == None:
                sub_fh = open_file_or_die(os.environ["QUEX_PATH"] 
                                          + Setup.language_db["$code_base"] 
                                          + Setup.language_db["$token-default-file"])
                parse_section(sub_fh)
                sub_fh.close()
                default_token_type_definition_triggered_by_mode_definition_f = True

            mode_definition.parse(fh)
            return

        else:
            # This case should have been caught by the 'verify_word_in_list' function
            assert False

    except EndOfStreamException:
        fh.seek(position)
        error_msg("End of file reached while parsing '%s' section" % word, fh)

def parse_pattern_name_definitions(fh):
    """Parses pattern definitions of the form:
   
          WHITESPACE  [ \t\n]
          IDENTIFIER  [a-zA-Z0-9]+
          OP_PLUS     "+"
          
       That means: 'name' whitespace 'regular expression' whitespace newline.
       Comments can only be '//' nothing else and they have to appear at the
       beginning of the line.
       
       One regular expression can have more than one name, but one name can 
       only have one regular expression.
    """
    skip_whitespace(fh)
    if not check(fh, "{"):
        error_msg("define region must start with opening '{'.", fh)

    while 1 + 1 == 2:
        skip_whitespace(fh)

        if check(fh, "}"): 
            return
        
        # -- get the name of the pattern
        skip_whitespace(fh)
        pattern_name = read_identifier(fh)
        if pattern_name == "":
            error_msg("Missing identifier for pattern definition.", fh)

        skip_whitespace(fh)

        if check(fh, "}"): 
            error_msg("Missing regular expression for pattern definition '%s'." % \
                      pattern_name, fh)

        # A regular expression state machine
        regular_expression_str, state_machine = \
                regular_expression.parse(fh, AllowNothingIsFineF=True) 

        if state_machine.core().has_pre_or_post_context():
            error_msg("Pattern definition with pre- and/or post-context.\n" + \
                      "This pattern cannot be used in replacements.", fh, DontExitF=True)

        lexer_mode.shorthand_db[pattern_name] = \
                lexer_mode.PatternShorthand(pattern_name, state_machine, 
                                            fh.name, get_current_line_info_number(fh),
                                            regular_expression_str)

def parse_token_id_definitions(fh, NamesOnlyF=False):
    # NOTE: Catching of EOF happens in caller: parse_section(...)
    #
    token_prefix       = Setup.token_id_prefix
    token_prefix_plain = Setup.token_id_prefix_plain # i.e. without name space included

    if NamesOnlyF: db = {}
    else:          db = lexer_mode.token_id_db

    skip_whitespace(fh)
    if not check(fh, "{"):
        error_msg("missing opening '{' for after 'token' section identifier.\n", fh)

    while check(fh, "}") == False:
        skip_whitespace(fh)

        candidate = read_identifier(fh, TolerantF=True)

        if candidate == "":
            error_msg("Missing valid token identifier." % candidate, fh)

        # -- check the name, if it starts with the token prefix paste a warning
        if candidate.find(token_prefix) == 0:
            error_msg("Token identifier '%s' starts with token prefix '%s'.\n" % (candidate, token_prefix) + \
                      "Token prefix is mounted automatically. This token id appears in the source\n" + \
                      "code as '%s%s'." % (token_prefix, candidate), \
                      fh, DontExitF=True)
        elif candidate.find(token_prefix_plain) == 0:
            error_msg("Token identifier '%s' starts with token prefix '%s'.\n" % (candidate, token_prefix) + \
                      "Token prefix is mounted automatically. This token id appears in the source\n" + \
                      "code as '%s%s'." % (token_prefix, candidate), \
                      fh, DontExitF=True)

        skip_whitespace(fh)

        if NamesOnlyF:
            db[token_prefix + candidate] = True
            if check(fh, ";") == False:
                error_msg("Missing ';' after definition of token identifier '%s'.\n" % candidate + \
                          "This is mandatory since Quex version 0.50.1.", fh)
            continue

        # Parse a possible numeric value after '='
        numeric_value = None
        if check(fh, "="):
            skip_whitespace(fh)
            numeric_value = read_integer(fh)
            if numeric_value == None:
                error_msg("Missing number after '=' for token identifier '%s'." % candidate, fh)

        if check(fh, ";") == False:
            error_msg("Missing ';' after definition of token identifier '%s'.\n" % candidate + \
                      "This is mandatory since Quex version 0.50.1.", fh)

        db[candidate] = TokenInfo(candidate, numeric_value, Filename=fh.name, LineN=get_current_line_info_number(fh))

    if NamesOnlyF:
        result = db.keys()
        result.sort()
        return result

