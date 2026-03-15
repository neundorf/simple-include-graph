# simple-include-graph
simple-include-graph is a simple python script to generate dot graphs
visualizing the files included by C/C++ sources.

It reads the incude dirs from a compile_commands.json, and then processes the
given C or C++ file. A compile_commands.json can geneerated e.g. by CMake by
setting CMAKE_EXPORT_COMPILE_COMMANDS to TRUE.
It basically reimplements the include file searching of the compiler, but in a simplified way.
Include files which are not found are simply ignored, #ifdefs are also ignored.
But nevertheless this should be good enough to produce a useful overview over the dependencies within
your project.
It is a simple python script, so it is easy to adapt.

Alexander Neundorf
<neundorf@kde.org>
