/* -*- C++ -*- vim: set syntax=cpp:
 *
 * (C) 2005-2009 Frank-Rene Schaefer                                                */
#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/inttypes.h>
#include <quex/code_base/asserts>
#if ! defined(__QUEX_OPTION_PLAIN_C)
#   include <string>
#endif

#ifndef   __QUEX_FROM
#   error "__QUEX_FROM must be defined."
#endif
#ifndef   __QUEX_TYPE_SOURCE
#   error "__QUEX_TYPE_SOURCE must be defined."
#endif

/* NOTE: '__QUEX_MAX_CHAR_SIZE' referes to the maximum number of chunks.
 *       For utf8 the 'chunks' are bytes. For utf16 the 'chunks' are 
 *       two byte long. For utf32 the chunks are 4 byte long. Thus, the
 *       numbers for __QUEX_MAX_CHAR_SIZE as seen below.                   */
#define __QUEX_TYPE_DRAIN    uint8_t
#define __QUEX_TO            utf8
#define __QUEX_MAX_CHAR_SIZE 4
#include <quex/code_base/converter_helper/base-core.gi>

#define __QUEX_TYPE_DRAIN    uint16_t
#define __QUEX_TO            utf16
#define __QUEX_MAX_CHAR_SIZE 2
#include <quex/code_base/converter_helper/base-core.gi>

#define __QUEX_TYPE_DRAIN    uint32_t
#define __QUEX_TO            utf32
#define __QUEX_MAX_CHAR_SIZE 1
#include <quex/code_base/converter_helper/base-core.gi>

/* Adapt 'char' and 'wchar_t' to utf8, utf16 or utf32 depending on its size. */
#define __QUEX_TYPE_DRAIN    char
#define __QUEX_TO            char
#define __QUEX_DRAIN_CODEC   QUEX_SETTING_CHAR_CODEC
#include <quex/code_base/converter_helper/base-char-and-wchar.gi>

#if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)
#   define __QUEX_TYPE_DRAIN    wchar_t
#   define __QUEX_TO            wchar
#   define __QUEX_DRAIN_CODEC   QUEX_SETTING_WCHAR_CODEC
#   include <quex/code_base/converter_helper/base-char-and-wchar.gi>
#endif 

#undef __QUEX_FROM
#undef __QUEX_TYPE_SOURCE 

