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
import bz2
import csv
import io
import itertools
import os.path
import sqlite3
from collections import defaultdict

from alive_progress import alive_bar

# Filenames for input paths
I_TO_F_INPUT = 'candidate_release-i-to-f.csv.bz2'
F_TO_I_INPUT = 'candidate_release-f-to-i.csv.bz2'

# Sqlite3 database filename.
SQLITE3_DB = 'cb.db'


def process_bz2file_into_db(infile, table_name, cursor, connection, expected_size):
    with bz2.BZ2File(infile) as f:
        csv_reader = csv.reader(map((lambda x: x.decode('utf-8')), f))
        line_num = 0
        with alive_bar(expected_size) as bar:
            for line in csv_reader:
                if len(line) % 2 == 0:
                    print(f'Malformed line: >>{line}<<')
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(line[1:])
                key, rest = line[0], output.getvalue()
                cursor.execute(f"insert into {table_name} values (?, ?)", (key, rest.strip()))
                line_num += 1
                if line_num % 100 == 0:
                    connection.commit()
                bar()
    connection.commit()


def add_c_relations_as_i_to_f(data_dir):
    """The CB paper was optimized for size. For CBC, we need the map available from i_to_f as well."""
    connection = sqlite3.connect(os.path.join(data_dir, SQLITE3_DB))
    cursor = connection.cursor()

    f_to_i_input = os.path.join(data_dir, F_TO_I_INPUT)
    item_to_features = defaultdict(list)
    with bz2.BZ2File(f_to_i_input) as f:
        csv_reader = csv.reader(map((lambda x: x.decode('utf-8')), f))
        line_num = 0
        with alive_bar(1148327) as bar:
            for line in csv_reader:
                line_num += 1
                if len(line) % 2 == 0:
                    print(f'Malformed line: >>{line}<<')
                feature = line[0]
                if feature.startswith("S"):
                    bar()
                    continue
                iterators = [iter(line[1:])] * 2
                grouped = [(p[0], int(p[1]))
                           for p in itertools.zip_longest(*iterators)]

                item_dict = dict(grouped)
                for item, wt in item_dict.items():
                    item_to_features[item].append((feature, int(wt)))
                bar()
    cursor.execute(f'CREATE TABLE I_TO_F_C (item text, features text)')
    connection.commit()

    lines_num = 0
    with alive_bar(len(item_to_features)) as bar:
        for item, features in item_to_features.items():
            features_sorted = sorted(features,
                                     key=lambda x: -x[1])
            row_to_write = []
            for f, wt in features_sorted:
                row_to_write.append(f)
                row_to_write.append(str(wt))
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(row_to_write)
            key, rest = item, output.getvalue()
            cursor.execute(f"insert into I_TO_F_C values (?, ?)", (key, rest.strip()))
            line_num += 1
            if line_num % 100 == 0:
                connection.commit()
            bar()
    connection.commit()

    print(f"Creating indices.")
    cursor.execute(f'CREATE INDEX I_TO_F_C_IDX ON I_TO_F_C (item)')
    connection.commit()


def create_db(data_dir, verbose=False):
    """Convert a pair of CSV files to a sqlite3 database.

      This is a no-op if outfile exists.
    """
    db_path = os.path.join(data_dir, SQLITE3_DB)
    i_to_f_input = os.path.join(data_dir, I_TO_F_INPUT)
    f_to_i_input = os.path.join(data_dir, F_TO_I_INPUT)

    if verbose:
        print(f"Checking if we need to produce '{db_path}' from '{i_to_f_input}' and '{f_to_i_input}")

    if os.path.exists(db_path):
        return

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute(f'CREATE TABLE I_TO_F (item text, features text)')
    cursor.execute(f'CREATE TABLE F_TO_I (feature text, items text)')
    connection.commit()

    print("INITIALIZING. ONLY DONE ONCE, WILL TAKE A FEW MINUTES.")
    print(f"Creating table 1 of 3: item-to-feature matrix.")
    process_bz2file_into_db(i_to_f_input, 'I_TO_F', cursor, connection, expected_size=192049)
    print(f"Creating table 2 of 3: feature-to-item matrix.")
    process_bz2file_into_db(f_to_i_input, 'F_TO_I', cursor, connection, expected_size=1148327)

    print(f"Creating indices.")
    cursor.execute(f'CREATE INDEX I_TO_F_IDX ON I_TO_F (item)')
    cursor.execute(f'CREATE INDEX F_TO_I_IDX ON F_TO_I (feature)')
    connection.commit()

    print(f"Creating table 3 of 3: item-to-feature matrix (contextual).")
    add_c_relations_as_i_to_f(data_dir=data_dir)


def get_row(cursor, table_name, field_name, key):
    cursor.execute(f"select * from {table_name} where {field_name}=?""", (key,))
    results = cursor.fetchall()
    if results:
        row_string = results[0][1]
    else:
        return dict()

    pieces = next(csv.reader([row_string]))
    iterators = [iter(pieces)] * 2
    grouped = [(p[0], float(p[1]) / 100)
               for p in itertools.zip_longest(*iterators)]
    return dict(grouped)


def restrict_to_syntactic(looked_up_row):
    return dict(p for p in looked_up_row.items() if p[0][0] == 'S')


def restrict_to_cooc(looked_up_row):
    return dict(p for p in looked_up_row.items() if p[0][0] == 'C')


def MatrixMultiply(cursor, table_name, field_name, wtd_seeds, rho=0.0, filterfn=None):
    each_seed_fraction = 1.0 / len(wtd_seeds)
    context_fraction = defaultdict(float)
    context_weight = defaultdict(float)
    for s, seed_wt in wtd_seeds:
        unfiltered_row = get_row(cursor, table_name, field_name, s)
        if filterfn:
            contexts_for_s = filterfn(unfiltered_row)
        else:
            contexts_for_s = unfiltered_row
        for c, wt in contexts_for_s.items():
            context_fraction[c] += each_seed_fraction
            context_weight[c] += seed_wt * wt

    # Now we penalize contexts not seen with all items.
    for context, fraction in context_fraction.items():
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
    def __init__(self, data_dir):
        self.data_dir = data_dir
        create_db(data_dir, verbose=False)
        self.connection = sqlite3.connect(os.path.join(data_dir, SQLITE3_DB))
        self.cursor = self.connection.cursor()

    def GetItemsGivenWeightedContexts(self, wtd_contexts):
        return MatrixMultiply(self.cursor, 'F_TO_I', 'feature', wtd_contexts, 0.0)

    def ExpandCategory(self, seeds, rho, n):
        sorted_contexts = MatrixMultiply(self.cursor, 'I_TO_F', 'item',
                                         wtd_seeds=[(x, 1) for x in seeds],
                                         rho=rho,
                                         filterfn=restrict_to_syntactic)
        if not sorted_contexts:
            print(f"Did not find any contexts for {seeds}")
            return []
        return MatrixMultiply(self.cursor, 'F_TO_I', 'feature',
                              wtd_seeds=sorted_contexts[:n],
                              rho=0)

    def GetCooccurringItems(self, seed):
        sorted_contexts = MatrixMultiply(self.cursor, 'I_TO_F', 'item',
                                         wtd_seeds=((seed, 1.0),),
                                         rho=0,
                                         filterfn=restrict_to_cooc)
        if not sorted_contexts:
            print(f"Did not find any contexts for '{seed}'")
            return []
        return MatrixMultiply(self.cursor, 'F_TO_I', 'feature',
                              wtd_seeds=sorted_contexts,
                              rho=0)

    def DoAnalogy(self, b, c, squash, semantic_n=100):
        print(f"Looking for the '{b}' of the '{c}'")

        # Since we have a single seed, the exact value of rho does not matter.
        # This is so because we multiply the weight sum by fraction ^ rho, and
        # fraction with a single seed can only ever be 0 or 1.
        things_like_b = self.ExpandCategory(seeds=[b, ], rho=1, n=semantic_n)
        things_cooccuring_with_c = self.GetCooccurringItems(seed=c)
        return MergeScores(things_like_b, things_cooccuring_with_c, squash=squash)

    def GetSyntacticFeaturesForItem(self, item):
        syntactic_features = get_row(self.cursor, 'I_TO_F', 'item', item)
        # Due to a bad design choice, there may be a single contextual feature here, with wt 100.
        return dict((k, v) for (k, v) in syntactic_features.items() if k.startswith('S'))

    def GetContextualFeaturesForItem(self, item):
        return get_row(self.cursor, 'I_TO_F_C', 'item', item)

    def GetItemsForFeature(self, feature):
        return get_row(self.cursor, 'F_TO_I', 'feature', feature)
