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
import shlex, subprocess
import sys
import random
from subprocess import Popen, PIPE

def CleanString(inp):
  return inp.lower().replace('_', ' ')


def GetExpansionCBGivenQuery(seeds, rho, n):
  arguments = [
    'python3', 'category_builder.py', '--cutpaste',
    '--n', str(n), '--rho', str(rho), '--expansion_size', '500'
  ]
  for seed in seeds:
    arguments.append('\'%s\'' % seed)
  arguments = shlex.split(' '.join(arguments))
  expansion = subprocess.check_output(arguments,
                                      universal_newlines=True).strip().split(', ')
  return expansion

def GetExpansion(seeds, rho, n):
  modified_seeds = [x.lower().replace('_', ' ') for x in seeds]
  return GetExpansionCBGivenQuery(modified_seeds, rho, n)

def EvaluateOneList(item_to_index, expansion, synsets_to_seek):
  """Returns a MAP precision shown by one list, and weights of offending intrusions."""
  seen_indices = set()
  bad_entries_count = 0
  good_entries_count = 0
  score_sum = 0.0

  intrusions = []  

  for idx, item in enumerate(expansion):
    if CleanString(item) not in item_to_index:
      bad_entries_count = bad_entries_count + 1
      # The badness of an intrusion is the fraction of correct entries that are yet to be seen.
      intrusion_badness = 1.0 * (synsets_to_seek - len(seen_indices)) / synsets_to_seek
      intrusions.append((item, '#%d' % (idx + 1), intrusion_badness))
    else:
      good_entries_count = good_entries_count + 1
      this_index = item_to_index[CleanString(item)]
      if this_index not in seen_indices:
        seen_indices.add(this_index)
        prec_here = 1.0 * good_entries_count / (good_entries_count + bad_entries_count)
        score_sum = score_sum + prec_here
        if len(seen_indices) == synsets_to_seek:
          break
  return score_sum / synsets_to_seek, intrusions
