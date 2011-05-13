/* -*- C++ -*- vim: set syntax=cpp:
 *
 * (C) 2005-2010 Frank-Rene Schaefer                                                */
#ifndef  __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UNICODE_I
#define  __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UNICODE_I

#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/inttypes.h>
#include <quex/code_base/asserts>


#define  __QUEX_UNI_TO          utf8
#define  __QUEX_UNI_TYPE_DRAIN  uint8_t
#include <quex/code_base/converter_helper/base-unicode.gi>

#define  __QUEX_UNI_TO         utf16
#define  __QUEX_UNI_TYPE_DRAIN uint16_t
#include <quex/code_base/converter_helper/base-unicode.gi>

#define  __QUEX_UNI_TO         utf32
#define  __QUEX_UNI_TYPE_DRAIN uint32_t
#include <quex/code_base/converter_helper/base-unicode.gi>

/* Adapt 'char' and 'wchar_t' to utf8, utf16 or utf32 depending on its size. */
#define __QUEX_TYPE_SOURCE   QUEX_TYPE_CHARACTER
#define __QUEX_FROM          QUEX_SETTING_CODEC

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

#endif /* __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UNICODE_I */
