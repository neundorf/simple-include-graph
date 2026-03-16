#!/usr/bin/env python3

# Copyright 2026, Alexander Neundorf <neundorf@kde.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.


import json
import re
import argparse
import os
from pathlib import Path

# Load the compile_commands.json
def load_command_map(filename):
  with open(filename, "r", encoding="utf-8") as f:
    data = json.load(f)

  result = {}
  for entry in data:
    file = entry.get("file")
    command = entry.get("command")
    if file and command:
      resolved_file = Path(file).resolve()
      result[resolved_file] = command

  return result


# Parse the include directories from the compile command and return them as list
def extract_include_paths(command):
  result = []

  for token in command.split():
    if token.startswith("-isystem"):
      result.append(token[len("-isystem"):])
    if token.startswith("-external:I"):
      result.append(token[len("-external:I"):])
    elif token.startswith("-I"):
      result.append(token[len("-I"):])
    elif token.startswith("-i"):
      result.append(token[len("-i"):])

  return result


# Parse the include files from a source file and return them as a list
# Each entry still has the "" or <> around them
def collect_include_files(filename):
  pattern = re.compile(r'^\s*#\s*include\s+([<"]([\w/]+\.\w+)[>"]).*')
  results = []

  with open(filename, "r", encoding="utf-8") as f:
    for line in f:
      m = pattern.match(line)
      if m:
        results.append(m.group(1))

  return results


# Escape a string for dot
def esc(s):
  return s.replace("\\", "\\\\")


# A class for generating a dot digraph file
class DotGraph:
  def __init__(self):
    self.props = dict()
    self.edges = []
    self.prefix = None
    self.skip = None

  # Call this if some node should have special properties
  def set_node_props(self, node, props):
    self.props[node] = props

  # Add an edge from the first node to the second node
  def add_edge(self, from_node, to_node):
    print(f"  Added from {from_node} to {to_node}")
    self.edges.append((from_node, to_node))

  # Write the dot file with the edges and node properties created so far.
  def write_file(self, filename, prefix = None, skip=None):
    with open(filename, "w", encoding="utf-8") as file:
      file.write("digraph Inc {\n")

      for n, p in self.props.items():
        if skip and skip in n:
          continue
        if prefix:
          if not n.startswith(prefix):
            continue
          n = n.removeprefix(prefix)

        file.write(f"  \"{esc(n)}\" [{p}];\n")

      for f, t in self.edges:
        if skip and skip in t:
          continue
        if prefix:
          if not t.startswith(prefix):
            continue
          f = f.removeprefix(prefix)
          t = t.removeprefix(prefix)

        file.write(f"  \"{esc(f)}\" -> \"{esc(t)}\";\n")
      file.write("}\n")


# Parse a C/C++ file and add edges for all included files.
# The include files are searched in the given include_dirs. If some file
# cannot be found it is simply skipped.
def parse_file(filename, files_to_process, include_dirs, graph):
  incs = collect_include_files(filename)
  for inc in incs:
#    print(f"{filename} INC: {inc}")
    inc_file = inc[1:-1]
    included_file = None
    if inc.startswith("\""):
      f = Path(filename).parent / inc_file
      if f.exists():
        included_file = str(f.resolve())

    if not included_file: # check the include dirs
      for dir in include_dirs:
        f = Path(dir) / inc_file
        if f.exists():
          included_file = str(f.resolve())
          break

    if included_file:
      graph.add_edge(str(filename), included_file)
#      print(f"  found {included_file}")
      files_to_process.append(included_file)
    else:
      print(f"{filename}: Did not find any file for {inc}")



def main():
  parser = argparse.ArgumentParser(description="Generate a dot graph file "
                                   "showing the include files of a C/C++ file.")

  parser.add_argument("--file", required=True, help="Input filename")
  parser.add_argument("--compile-commands-file", default="compile_commands.json",
                      help="The path to the compile_commands.json file to use. "
                      "If not set, it reads it from the current directory.")
  parser.add_argument("--dot", default="incs.dot", help="Output dot filename. "
                      "If not set, it will write to incs.dot")
  parser.add_argument("--basedir", help="If set, only files within that "
                      "directory will be included in the generated graph, and "
                      "the base dir will be removed from the node names in the "
                      "graph, so it will be easier to read.")

  args = parser.parse_args()

  print("File:", args.file)
  print("JSON file:", args.compile_commands_file)

  graph = DotGraph()

  commands = load_command_map(args.compile_commands_file)

  file = Path(args.file).resolve()
  graph.set_node_props(str(file), "color=red, style=filled")

  cmd = commands[file]
#  print(f"file: {file}") # cmd: {cmd}")
  include_dirs = extract_include_paths(cmd)
#  print(f"inc: {include_dirs}")

  files_to_process = [ file ]
  processed_files = set()
  while len(files_to_process) > 0:
    next_file = files_to_process.pop(0)
    if not next_file in processed_files:
      processed_files.add(next_file)
      parse_file(next_file, files_to_process, include_dirs, graph)

  prefix = None
  if args.basedir:
    prefix = str(Path(args.basedir).resolve())
  graph.write_file(args.dot, prefix, "3rdParty")


if __name__ == "__main__":
  main()

