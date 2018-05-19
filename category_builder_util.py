# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections import defaultdict
import bz2
import csv
import io
import itertools
import os.path
import shelve
import sys

DATA_DIR = '.'

# Filenames for input paths
I_TO_F_INPUT = 'candidate_release-i-to-f.csv.bz2'
F_TO_I_INPUT = 'candidate_release-f-to-i.csv.bz2'

# Filenames for generated shelves
I_TO_F_SHELF = 'i-to-f-shelf'
F_TO_I_SHELF = 'f-to-i-shelf'


def GetPath(filename):
  return os.path.join(DATA_DIR, filename)

def CreateShelf(infile, outfile, linecount, verbose):
  """Convert a CSV file to a shelf keyed by the first column.
  
  This is a no-op if outfile exists.
  """
  if verbose:
    print "Checking if we need to produce '%s' from '%s'" % (outfile, infile)
  if os.path.exists(outfile):
    # We are probably fine, but check size just to be sure.
    output_size = os.path.getsize(outfile)
    if verbose:
      print "\tSize of %s: %d" % (outfile, output_size)
    if output_size < 500000000:
      print "The file %s seems too small, likely corrupted. Please delete it rerun initialize.py." % outfile
      sys.exit(1)
    if verbose:
      print "\tLooks good."
    return

  if verbose:
    print "Processing '%s'. This may take a couple of minutes." % infile

  input_size = os.path.getsize(infile)
  if input_size < 500000000:
    print "The file %s seems too small." % outfile
    print "Did you run 'git lfs pull'? Git stores large files differently."
    sys.exit(1)

  s = shelve.open(outfile)
  with bz2.BZ2File(infile) as f:
    linenum = 0
    csvreader = csv.reader(f)
    for line in csvreader:
      output = io.BytesIO()
      writer = csv.writer(output)
      writer.writerow(line[1:])
      key, rest = line[0], output.getvalue()
      s[key] = rest.strip()
      linenum = linenum + 1
      if linenum % 10000 == 0:
        print "\tCreating shelf. Processed %s lines out of %s" % (linenum, linecount)
  s.close()

def CreateShelves(verbose=False):
  """Create shelves for the two matrices."""
  if verbose:
    print "Initializing two matrices."
  CreateShelf(GetPath(I_TO_F_INPUT), GetPath(I_TO_F_SHELF), linecount=200000, verbose=verbose)
  CreateShelf(GetPath(F_TO_I_INPUT), GetPath(F_TO_I_SHELF), linecount=1150000, verbose=verbose)

def GetRow(shelf, key):
  try:
    row_string = shelf[key]
  except KeyError:
    return dict()
  
  pieces = csv.reader([row_string]).next()
  iterators = [iter(pieces)] * 2
  grouped = [(p[0], float(p[1]) / 100)
             for p in itertools.izip_longest(*iterators)]
  return dict(grouped)

def RestrictToSyntactic(looked_up_row):
  return dict(p for p in looked_up_row.iteritems() if p[0][0] == 'S')

def RestrictToCooc(looked_up_row):
  return dict(p for p in looked_up_row.iteritems() if p[0][0] == 'C')

def MatrixMultiply(shelf, wtd_seeds, rho=0, filterfn=None):
  each_seed_fraction = 1.0 / len(wtd_seeds)
  context_fraction = defaultdict(float)
  context_weight = defaultdict(float)
  for s, seed_wt in wtd_seeds:
    unfiltered_row = GetRow(shelf, s)
    if filterfn:
      contexts_for_s = filterfn(unfiltered_row)
    else:
      contexts_for_s = unfiltered_row
    for c, wt in contexts_for_s.iteritems():
      context_fraction[c] += each_seed_fraction
      context_weight[c] += seed_wt * wt
  
  # Now we penalize contexts not seen with all items.
  for context, fraction in context_fraction.iteritems():
    context_weight[context] *= pow(fraction, rho)
  sorted_contexts = sorted(context_weight.items(), reverse=True,
                           key=lambda x: x[1])
  return sorted_contexts

def MergeScores(a_scores, b_scores, squash=100.0):
  total_score = defaultdict(float)
  for k, v in a_scores:
    total_score[k] += 1.0 * squash * v / (squash - 1.0 + v)
  for k, v in b_scores:
    if k not in total_score:
      continue
    total_score[k] += 1.0 * squash * v / (squash - 1.0 + v)
  return sorted(total_score.items(), reverse=True,
                key=lambda x: x[1])

class CategoryBuilder(object):
  def __init__(self):
    CreateShelves()
    self.IToF = shelve.open(GetPath(I_TO_F_SHELF)) 
    self.FToI = shelve.open(GetPath(F_TO_I_SHELF))

  def GetItemsGivenWeightedContexts(self, wtd_contexts):
    return MatrixMultiply(self.FToI, wtd_contexts, 0.0)

  def ExpandCategory(self, seeds, rho, n):
    sorted_contexts = MatrixMultiply(shelf=self.IToF,
                                     wtd_seeds=[(x, 1) for x in seeds],
                                     rho=rho,
                                     filterfn=RestrictToSyntactic)
    if not sorted_contexts:
      print "Did not find any contexts for ", seeds
      return []
    return MatrixMultiply(shelf=self.FToI,
                          wtd_seeds=sorted_contexts[:n],
                          rho=0)
  
  def GetCooccurringItems(self, seed):
    sorted_contexts = MatrixMultiply(shelf=self.IToF,
                                     wtd_seeds=((seed, 1.0),), 
                                     rho=0,
                                     filterfn=RestrictToCooc)
    if not sorted_contexts:
      print "Did not find any contexts for ", seed
      return []
    return MatrixMultiply(shelf=self.FToI,
                          wtd_seeds=sorted_contexts,
                          rho=0)
  
  def DoAnalogy(self, b, c, squash):
    print "Looking for the ", b, " of the ", c
    
    things_like_b = self.ExpandCategory(seeds=[b,], rho=1, n=100)
    things_cooccuring_with_c = self.GetCooccurringItems(seed=c)
    return MergeScores(things_like_b, things_cooccuring_with_c, squash=squash)
