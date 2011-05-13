/* -*- C++ -*- vim: set syntax=cpp:
 *
 * (C) 2005-2010 Frank-Rene Schaefer                                                */

#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/inttypes.h>
#include <quex/code_base/asserts>

#include <quex/code_base/converter_helper/utf8>
#include <quex/code_base/converter_helper/utf16>
#include <quex/code_base/converter_helper/utf32>

/* We want to include the headers 'utf8', 'utf16', and 'utf32' here 
 * dependent on __QUEX_TYPE_CHARACTER_SIZE and keep the condition
 * local to this file. Those files above, though, undefine the 
 * macros __QUEX_TYPE_DRAIN and __QUEX_TO at the end so we use 
 * a 'special' naming here that is safe from being undefined.       */
#ifndef    __QUEX_UNI_TYPE_DRAIN
#   error "__QUEX_UNI_TYPE_DRAIN has not been defined."
#endif
#ifndef    __QUEX_UNI_TO
#   error "__QUEX_UNI_TO has not been defined."
#endif

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
__QUEX_CONVERTER_STRING(unicode, __QUEX_UNI_TO)(const QUEX_TYPE_CHARACTER**    source_pp, 
                                                const QUEX_TYPE_CHARACTER*     SourceEnd, 
                                                __QUEX_UNI_TYPE_DRAIN**        drain_pp, 
                                                const __QUEX_UNI_TYPE_DRAIN*   DrainEnd)
{
    switch( sizeof(QUEX_TYPE_CHARACTER) ) {
    case 1:   
        __QUEX_CONVERTER_STRING(utf8, __QUEX_UNI_TO)((const uint8_t**)source_pp, 
                                                     (const uint8_t*)SourceEnd, 
                                                     drain_pp,        
                                                     DrainEnd); 
        break;
    case 2:   
        __QUEX_CONVERTER_STRING(utf16, __QUEX_UNI_TO)((const uint16_t**)source_pp, 
                                                      (const uint16_t*)SourceEnd, 
                                                      drain_pp,                    
                                                      DrainEnd); 
        break;
    default:  
        __QUEX_CONVERTER_STRING(utf32, __QUEX_UNI_TO)((const uint32_t**)source_pp, 
                                                      (const uint32_t*)SourceEnd, 
                                                      drain_pp,                    
                                                      DrainEnd); 
        break;
    }
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::basic_string<__QUEX_UNI_TYPE_DRAIN>
__QUEX_CONVERTER_STRING(unicode, __QUEX_UNI_TO)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source)
{
    switch( sizeof(QUEX_TYPE_CHARACTER) ) {
    case 1: {
                std::basic_string<uint8_t>  tmp((const uint8_t*)Source.c_str());
                return __QUEX_CONVERTER_STRING(utf8, __QUEX_UNI_TO)(tmp); 
        }
    case 2: {
                std::basic_string<uint16_t>  tmp((const uint16_t*)Source.c_str());
                return __QUEX_CONVERTER_STRING(utf16, __QUEX_UNI_TO)(tmp);
        }
    default: { 
                 std::basic_string<uint32_t>  tmp((const uint32_t*)Source.c_str());
                 return __QUEX_CONVERTER_STRING(utf32, __QUEX_UNI_TO)(tmp); 
        }
    }
}
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#undef  __QUEX_UNI_TO         
#undef  __QUEX_UNI_TYPE_DRAIN 

#include <quex/code_base/converter_helper/utf8.i>
#include <quex/code_base/converter_helper/utf16.i>
#include <quex/code_base/converter_helper/utf32.i>
