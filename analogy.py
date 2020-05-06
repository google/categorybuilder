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

import argparse
import category_builder_util as util

def GetArgumentParser():
  parser = argparse.ArgumentParser(description='Category Builder Analogies')
  parser.add_argument('--squash', default=100.0, type=float, help="Squash for combining scores")
  parser.add_argument('b', help="The B in A:B::C:?")
  parser.add_argument('c', help="The C in A:B::C:?")
  return parser

if __name__ == "__main__":
  args = GetArgumentParser().parse_args()

  CB = util.CategoryBuilder(data_dir=".")
  
  items = CB.DoAnalogy(b=args.b, c=args.c, squash=args.squash)
  for item in items[:10]:
    print(f"{item[1]:5.3f}\t\t{item[0]}")
