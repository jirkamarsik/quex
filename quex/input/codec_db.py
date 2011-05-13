#! /usr/bin/env python
#
# (C) 2009 Frank-Rene Schaefer
# ABSOLUTELY NO WARRANTY

import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
import codecs

from quex.DEFINITIONS     import QUEX_PATH
from quex.frs_py.file_in                                            import get_file_content_or_die, \
                                                                           open_file_or_die, \
                                                                           error_msg, \
                                                                           verify_word_in_list
from quex.core_engine.interval_handling                             import Interval, NumberSet
from quex.core_engine.regular_expression.snap_backslashed_character import __parse_hex_number

__codec_list_db = []
__supported_codec_list = []
__supported_codec_list_plus_aliases = []

def get_codec_list_db():
    """
       ...
       [ CODEC_NAME  [CODEC_NAME_LIST]  [LANGUAGE_NAME_LIST] ]
       ...
    """
    global __codec_list_db
    if __codec_list_db != []: return __codec_list_db

    file_name = QUEX_PATH + "/quex/data_base/codecs/00-ALL.txt"
    fh        = open_file_or_die(file_name, "rb")
    # FIELD SEPARATOR:  ';'
    # RECORD SEPARATOR: '\n'
    # FIELDS:           [Python Coding Name]   [Aliases]   [Languages] 
    # Aliases and Languages are separated by ','
    __codec_list_db = []
    for line in fh.readlines():
        line = line.strip()
        if len(line) == 0 or line[0] == "#": continue
        fields = map(lambda x: x.strip(), line.split(";"))
        try:
            codec         = fields[0]
            aliases_list  = map(lambda x: x.strip(), fields[1].split(","))
            language_list = map(lambda x: x.strip(), fields[2].split(","))
        except:
            print "Error in line:\n%s\n" % line
        __codec_list_db.append([codec, aliases_list, language_list])

    fh.close()
    return __codec_list_db

def get_supported_codec_list(IncludeAliasesF=False):
    assert type(IncludeAliasesF) == bool

    global __supported_codec_list
    if __supported_codec_list != []: 
        if IncludeAliasesF: return __supported_codec_list_plus_aliases
        else:               return __supported_codec_list

    file_name = QUEX_PATH + "/quex/data_base/codecs/00-SUPPORTED.txt"
    content   = get_file_content_or_die(file_name)

    __supported_codec_list = content.split()
    __supported_codec_list.sort()
    codec_db_list = get_codec_list_db()
    for codec_name, aliases_list, dummy in codec_db_list:
        if codec_name in __supported_codec_list: 
            __supported_codec_list_plus_aliases.extend(filter(lambda x: x != "", aliases_list))
        
    __supported_codec_list_plus_aliases.sort()
    if IncludeAliasesF: return __supported_codec_list_plus_aliases
    else:               return __supported_codec_list

def get_supported_language_list(CodecName=None):
    if CodecName == None:
        result = []
        for record in get_codec_list_db():
            for language in record[2]:
                if language not in result: 
                    result.append(language)
        result.sort()
        return result
    else:
        for record in get_codec_list_db():
            if record[0] == CodecName: return record[2]
        return []

def get_codecs_for_language(Language):
    
    result = []
    for record in get_codec_list_db():
        codec = record[0]
        if codec not in get_supported_codec_list(): continue
        if Language in record[2]: 
            result.append(record[0])
    if result == []:
        verify_word_in_list(Language, get_supported_language_list(),
                "No codec found for language '%s'." % Language)
    return result

def __get_distinct_codec_name_for_alias(CodecAlias, FH=-1, LineN=None):
    """Arguments FH and LineN correspond to the arguments of error_msg."""
    assert len(CodecAlias) != 0

    for record in get_codec_list_db():
        if CodecAlias in record[1] or CodecAlias == record[0]: 
            return record[0]

    verify_word_in_list(CodecAlias, get_supported_codec_list(), 
                        "Character encoding '%s' unknown to current version of quex." % CodecAlias,
                        FH, LineN)

def get_codec_transformation_info(Codec, FH=-1, LineN=None):
    """Provides the information about the relation of character codes in a particular 
       coding to unicode character codes. It is provided in the following form:

       # Codec Values                 Unicode Values
       [ (Source0_Begin, Source0_End, TargetInterval0_Begin), 
         (Source1_Begin, Source1_End, TargetInterval1_Begin),
         (Source2_Begin, Source2_End, TargetInterval2_Begin), 
         ... 
       ]

       Arguments FH and LineN correspond to the arguments of error_msg.

    """
    distinct_codec = __get_distinct_codec_name_for_alias(Codec)
    file_name      = QUEX_PATH + "/quex/data_base/codecs/%s.dat" % distinct_codec

    fh = open_file_or_die(file_name, "rb")

    # Read coding into data structure
    transformation_list = []
    if 1:
        line_n = -1
        for line in fh.readlines():
            line_n += 1
            if line == "" or line[0] == "#": continue
            fields = line.split()
            source_begin = int("0x" + fields[0], 16)
            source_end   = source_begin + int("0x" + fields[1], 16)
            target_begin = int("0x" + fields[2], 16)

            transformation_list.append([source_begin, source_end, target_begin])
    else:
        error_msg("Syntax error in database file for codec '%s'." % Codec, fh.name, line_n)

    return transformation_list

def get_supported_unicode_character_set(CodecAlias, FH=-1, LineN=None):
    result = NumberSet()
    for source_begin, source_end, target_begin in get_codec_transformation_info(CodecAlias, FH, LineN):
        result.add_interval(Interval(source_begin, source_end))
    return result

def __get_transformation(encoder, CharCode):
    # Returns the encoding for the given character code, 
    # plus the number of bytes which it occupies.
    input_str = eval("u'\\U%08X'" % CharCode)
    try:    
        result = encoder(input_str)[0]
    except: 
        # '-1' stands for: 'no encoding for given unicode character'
        return -1, -1

    if len(result) >= 2 and result == "\\u":
        # For compatibility with versions of python <= 2.5, convert the unicode
        # string by hand.
        n = (len(result) - 2) / 2
        return __parse_hex_number(result[2:], len(result) - 2), n

    else:
        L = len(result) 
        if   L == 1: return ord(result), 1
        elif L == 2: return ord(result[0]) * 256      + ord(result[1]), 2
        elif L == 3: return ord(result[0]) * 65536    + ord(result[1]) * 256 + ord(result[2]), 3
        elif L == 4: return ord(result[0]) * 16777216L + ord(result[0]) * 65536 + ord(result[1]) * 256 + ord(result[2]), 4
        else:
            print "Character Encoding of > 4 Bytes."
            return -1, 5

def __create_database_file(TargetEncoding, TargetEncodingName):
    """Writes a database file for a given TargetEncodingName. The 
       TargetEncodingName is required to name the file where the 
       data is to be stored.
    """
    encoder     = codecs.getencoder(TargetEncoding)
    prev_output = -1
    db          = []
    bytes_per_char = -1
    for input in range(0x110000):
        output, n = __get_transformation(encoder, input)
        # output, n = __get_transformation(encoder, input)

        if bytes_per_char == -1: 
            bytes_per_char = n
        elif n != -1 and bytes_per_char != n:
            print "# not a constant size byte format."
            return False

        # Detect discontinuity in the mapping
        if   prev_output == -1:
            if output != -1:
                input_interval        = Interval(input)
                target_interval_begin = output

        elif output != prev_output + 1:
            # If interval was valid, append it to the database
            input_interval.end    = input
            db.append((input_interval, target_interval_begin))
            # If interval ahead is valid, prepare an object for it
            if output != -1:
                input_interval        = Interval(input)
                target_interval_begin = output

        prev_output = output

    if prev_output != -1:
        input_interval.end = input
        self.__db.append((interval, target_interval_begin))

    fh = open_file_or_die(QUEX_PATH + "/quex/data_base/codecs/%s.dat" % TargetEncoding, "wb")
    fh.write("# Describes mapping from Unicode Code pointer to Character code in %s (%s)\n" \
             % (TargetEncoding, TargetEncodingName))
    fh.write("# [SourceInterval.begin] [SourceInterval.Size]  [TargetInterval.begin] (all in hexidecimal)\n")
    for i, t in db:
        fh.write("%X %X %X\n" % (i.begin, i.end - i.begin, t))
    fh.close()

    return True

        
if __name__ == "__main__":
    # PURPOSE: Helper script to create database files that describe the mapping from
    #          unicode characters to character codes of a particular encoding.
    fh           = open("00-ALL.txt")
    fh_supported = open("00-SUPPORTED.txt", "wb")
    # FIELD SEPARATOR:  ';'
    # RECORD SEPARATOR: '\n'
    # FIELDS:           [Python Coding Name]   [Aliases]   [Languages] 
    # Aliases and Languages are separated by ','
    db_list = get_codec_list_db()
    for record in db_list:
        codec         = record[0]
        language_list = record[2]
        print repr(language_list) + " (", codec, ")",
        if __create_database_file(codec, language_list):
            fh_supported.write("%s " % codec)
            print "[OK]"
            
