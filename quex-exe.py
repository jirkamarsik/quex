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
# (C) 2007 Frank-Rene Schaefer
#
################################################################################
import sys
try:    
    if False: print ""
except: 
    print("error: This version of quex was not implemented for Python >= 3.0")
    print("error: Please, use Python versions 2.x.")
    sys.exit(-1)

#def __exeption_handler(TheException):
#    if isinstance(TheException, AssertionError):
#        error_msg("Assertion error -- please report a bug under\n" + \
#                  " https://sourceforge.net/tracker/?group_id=168259&atid=846112")
#
#    elif isinstance(TheException, KeyboardInterrupt): 
#        print
#        error_msg("#\n# Keyboard interrupt -- exiting while processing unfinished.\n#")
#
#    #elif isinstance(TheException, Exception):
#    else:
#        error_msg("Unknown exception occured -- please, report a bug under\n" + \
#                  " https://sourceforge.net/tracker/?group_id=168259&atid=846112")
    
from quex.frs_py.file_in  import error_msg

def on_exception(x, Txt):
    if "--debug-exception" in sys.argv: 
        raise x
    error_msg(Txt)

try:
    # (*) Check if everything is correctly installed
    import quex.DEFINITIONS
    quex.DEFINITIONS.check()

    import tempfile

    # This script needs to be located one directory above 'quex.'
    # so that it ca get the imports straight.
    from   quex.input.setup        import setup as Setup
    import quex.input.setup_parser as setup_parser
    import quex.input.query        as query_parser
    import quex.core               as core


except AssertionError, x:
    on_exception(x, "Module Assertion error -- please report a bug under\n" + \
                    " https://sourceforge.net/tracker/?group_id=168259&atid=846112")

except KeyboardInterrupt: 
    print
    error_msg("#\n# Keyboard interrupt -- exiting while loading modules unfinished.\n#")

except Exception, x:
   on_exception(x, "Module Exception occured -- please, report a bug under\n" + \
                " https://sourceforge.net/tracker/?group_id=168259&atid=846112")
    
try:
    pass
    #import psyco
    #psyco.full()
except ImportError:
    pass

if __name__ == "__main__":
    try:
        core._exception_checker()

        # (*) Call only for query? ___________________________________________________________
        if query_parser.do(sys.argv):   # if quex has been called for UCS property
            sys.exit(0)                 # query, then no further processing is performed

        # (*) Get Setup from Command Line and Config File ____________________________________
        #     If the setup parser returns 'False' the requested job was minor
        #     and no further processing has to be done. If 'True' start the process.
        if setup_parser.do(sys.argv):
            # (*) Run Quex ___________________________________________________________________
            if Setup.plot_graphic_format == "": core.do()       # 'normal' code generation
            else:                               core.do_plot()  # plot transition graphs

    except AssertionError, x:
        on_exception(x, "Assertion error -- please report a bug under\n" + \
                        " https://sourceforge.net/tracker/?group_id=168259&atid=846112")

    except KeyboardInterrupt: 
        print
        error_msg("#\n# Keyboard interrupt -- exiting while processing unfinished.\n#")

    except Exception, x:
        on_exception(x, "Exception occured -- please, report a bug under\n" + \
                        " https://sourceforge.net/tracker/?group_id=168259&atid=846112")

