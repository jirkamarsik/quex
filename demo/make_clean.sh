for x in `find -maxdepth 3 -mindepth 1 -type f -or -path "*.svn*" -prune -or -print`; do echo "###### $x"; cd $x; make clean; cd $q/demo; done
