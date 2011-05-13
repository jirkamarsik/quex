#ifndef __QUEX_INCLUDE_GUARD__COMPATIBILITY__INTTYPES_H
#define __QUEX_INCLUDE_GUARD__COMPATIBILITY__INTTYPES_H
/* NOTE: At the time of this writing (Aug. 2007) there are still some
 *       compilers that do not support C99 Standard completely and
 *       do not provided 'inttypes.h' and 'stdint.h' along with their
 *       compiler package (e.g. a major Redmondian Company). For this
 *       reason this header creates som adaptions. */

#if ! defined(__QUEX_OPTION_PLAIN_C)
extern "C" {
#endif

#if defined (_MSC_VER)
#   include <quex/code_base/compatibility/win/msc_inttypes.h>
#elif defined(__BORLANDC__)
#   include <quex/code_base/compatibility/win/borland_inttypes.h>
#else
#   include <inttypes.h>
#endif

#if ! defined(__QUEX_OPTION_PLAIN_C)
} /* extern "C" */
#endif

#endif /* __QUEX_INCLUDE_GUARD__COMPATIBILITY__INTTYPES_H */
