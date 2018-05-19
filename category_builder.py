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

from __future__ import absolute_import
from __future__ import print_function
import argparse
import category_builder_util as util

def GetArgumentParser():
  parser = argparse.ArgumentParser(description='Category Builder')
  parser.add_argument('--rho', default=3.0, type=float, help="The rho param")
  parser.add_argument('--n', default=100, type=int,
                      help="How many features to use")
  parser.add_argument('seeds', nargs='+', help="Seeds to expand")
  return parser

if __name__ == "__main__":
  args = GetArgumentParser().parse_args()

  CB = util.CategoryBuilder()
  
  items = CB.ExpandCategory(seeds=args.seeds,
                            rho=args.rho,
                            n=args.n)
  for item in items[:50]:
    print(item[1], "\t", item[0])
