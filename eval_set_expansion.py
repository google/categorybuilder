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

"""Runs MAP evaluation.

Input is a filename, where each line is a synset. See eval_data/cat_eval_data/* for examples.
"""

from collections import defaultdict
import shlex, subprocess
import sys
import random
from subprocess import Popen, PIPE
from eval_util import CleanString, GetExpansion, EvaluateOneList
import argparse

class CategoryEvalMAP(object):

  SEEDS_TO_USE = 3  # How many seeds to use in each trial

  def __init__(self, filename):
    self.filename = filename
    self.Read()

  def Read(self):
    self.item_to_index = defaultdict(int)
    self.candidate_seeds = []

    next_index = 1
    with open(self.filename) as f:
      for line in f:
        parts = [x.strip() for x in line.split(',')]
        parts = [x for x in parts if x]
        if parts:
          self.candidate_seeds.append(parts[0])
          for p in parts:
            self.item_to_index[p] = next_index
            self.item_to_index[CleanString(p)] = next_index
          next_index = next_index + 1


  def Eval(self, num_iterations, seeds_in_top_n, map_n, rho, n):
    effective_seeds = self.candidate_seeds
    if seeds_in_top_n > 0:
      effective_seeds = effective_seeds[:seeds_in_top_n]
    synsets_to_seek = map_n
    if not synsets_to_seek:
      synsets_to_seek = len(effective_seeds)
    print(f"SEEDS TO SELECT FROM: {effective_seeds}")
    
    # An intruder is a bad item in the expansion that comes before good ones.
    # Baddness is the fraction of sysnsets before which it occurs: for U.S states,
    # seeing "China" in the first position in the expansion has badness=1.0, but seeing
    # it after 45 states have been seen is 5/50 (unseen states divided by total number of states).
    intrusions_by_badness = defaultdict(float)

    score_sum = 0.0
    for itercount in range(num_iterations):
      seeds = random.sample(effective_seeds, self.SEEDS_TO_USE)
      expansion = GetExpansion(seeds, rho=rho, n=n)
      score_here, intrusions = EvaluateOneList(self.item_to_index, expansion, synsets_to_seek)
      for intrusion, position, badness in intrusions:
        intrusions_by_badness[intrusion] += badness
      print(f"\nITERATION #{itercount}: {seeds} ==> Mean precision: {score_here}")
      print(f"\tTop Intrusions: {intrusions[:20]}")
      score_sum += score_here
    
    print("\n\nTop Intrusions (a score of 3% here means that this entry was typically seen after 97% of the real entries):\n")
    for intrusion, badness in sorted(intrusions_by_badness.items(),
                                     reverse=True,
                                     key=lambda x: x[1])[:20]:
      print(f"\t{100.0 * badness / num_iterations:5.3f}%\t{intrusion}")

    print(f"\n\nMAP score: {100.0 * score_sum / num_iterations: 5.3f}%")
      
  

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Parse Args')
  parser.add_argument('--iterations', type=int, default=50)
  parser.add_argument('--seeds_in_top_n', type=int, default=0,
                      help='If > 0, select among first n items as seeds')
  parser.add_argument('--map_n', type=int, default = 0,
                      help='If > 0, then stop after N synsets')
  parser.add_argument('filename', type=str, help='File containing eval data')
  parser.add_argument('--rho', default=3.0, type=float, help="The rho param")
  parser.add_argument('--n', default=100, type=int,
                      help="How many features to use")
  flags = parser.parse_args()
  
  eval_category = CategoryEvalMAP(flags.filename)
  eval_category.Eval(num_iterations=flags.iterations,
    	             seeds_in_top_n=flags.seeds_in_top_n,
    	             map_n=flags.map_n, rho=flags.rho, n=flags.n)

