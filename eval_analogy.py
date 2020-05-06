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

"""Runs analogy evaluation.

Input is a filename, where each line is a four-part analogy problem.
  For example:
    Athens Greece Baghdad Iraq
Problems have been grouped into classes, indicated by solitary lines starting with a colon.
The example above is from this set:
   : capital-common-countries.
"""


from collections import defaultdict
import random
from eval_util import CleanString
import argparse
import category_builder_util as util

def ReadData(filename):
  """Returns named sets of four-tuples representing an analogy problem."""
  out = defaultdict(list)
  dataset_name = "NONE"
  with open(filename) as f:
    for line in f:
      if line.startswith(":"):
        dataset_name = line[1:].strip()
      else:
        parts = line.strip().split(' ')
        if len(parts) != 4:
          continue
        out[dataset_name].append([CleanString(x) for x in parts])
  return out


def GetAnalogy(CB, b, c, squash, semantic_n):
  expansion = CB.DoAnalogy(b=b, c=c, squash=squash, semantic_n=semantic_n)[:50]
  return expansion

def EvaluateAnalogies(CB, catname, fourtuples, rho, n, squash, reverse,
                      semantic_n):
  effective_catname = catname
  if reverse:
    effective_catname = effective_catname + " REVERSE"
  print(f"\n\n=========  {effective_catname} ============\n\n")
  correct_at_pos = defaultdict(int)
  for tuple_number, fourtuple in enumerate(fourtuples):
    if reverse:
      pair_1 = {'lhs': fourtuple[1], 'rhs': fourtuple[0]}
      pair_2 = {'lhs': fourtuple[3], 'rhs': fourtuple[2]}
    else:
      pair_1 = {'lhs': fourtuple[0], 'rhs': fourtuple[1]}
      pair_2 = {'lhs': fourtuple[2], 'rhs': fourtuple[3]}
    expansion = GetAnalogy(CB, b=pair_1["rhs"], c=pair_2["lhs"], squash=squash,
                           semantic_n=semantic_n)
    solved = False
    incorrect_seen = []
    for idx, item in enumerate(expansion):
      if item[0] == pair_2["rhs"]:
        # We have a hit!
        print("%s : %s :: %s : %s Solved at position %d %s" % (
            pair_1["lhs"],
            pair_1["rhs"],
            pair_2["lhs"],
            pair_2["rhs"],
            len(incorrect_seen),
            (' AFTER: ' + '; '.join(incorrect_seen[:10]) if incorrect_seen else '')))
        for i in range(len(incorrect_seen) + 1, 26):
          correct_at_pos[i] = correct_at_pos[i] + 1
        print("\tCurrent Precision: ", 1.0 * correct_at_pos[1] / (tuple_number + 1))
        solved = True
        break
      else:
        if item[0] != pair_1["rhs"] and item[0] != pair_2["lhs"]:
          incorrect_seen.append(item[0])
    if not solved:
      print("#### FAILED: %s : %s :: %s : %s" % (pair_1["lhs"],
                                                 pair_1["rhs"],
                                                 pair_2["lhs"],
                                                 pair_2["rhs"]))
  print("=====================================")
  print("CORRECTNESS By Index for ", effective_catname, correct_at_pos)
  print(f"ACCURACY FOR {effective_catname}:\t {1.0 * correct_at_pos[1] / len(fourtuples)}")


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Parse Args')
  parser.add_argument('--rho', default=3.0, type=float, help="The rho param")
  parser.add_argument('--n', default=100, type=int,
                      help="How many features to use")
  parser.add_argument('--squash', default=100.0, type=float, help="Squash for combining scores")
  parser.add_argument('--semantic_n', default=200, type=int, help="n for semantic expansion")

  parser.add_argument('filename', type=str, help='File containing eval data')
  flags = parser.parse_args()

  CB = util.CategoryBuilder(data_dir='.')

  data = ReadData(flags.filename)
  for catname, fourtuples in data.items():
    random.shuffle(fourtuples)
    if catname.startswith('gram') and not catname.startswith('gram6'):
      print("SKIPPING ", catname)
      continue
    EvaluateAnalogies(CB, catname, fourtuples, rho=flags.rho, n=flags.n, squash=flags.squash, reverse=True,
                      semantic_n=flags.semantic_n)
    EvaluateAnalogies(CB, catname, fourtuples, rho=flags.rho, n=flags.n, squash=flags.squash, reverse=False,
                      semantic_n=flags.semantic_n)
