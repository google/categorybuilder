# Category Builder

This repository contains data and code for the Category Builder system.

Category Builder can do set expansion while dealing robustly with polysemy.
See category_builder_paper.pdf in this directory.

## Installation

Download code and data using git. You will need to have installed [git lfs](https://git-lfs.github.com/).

``` shell
git clone https://github.com/google/categorybuilder
cd categorybuilder
git lfs pull
```

## Initialization

_Note: This will take a few minutes to initalize. Two files totaling 7 GB are produced._

``` shell
python initialize.py
```

## How to use Category Builder

``` shell
python category_builder.py ford nixon
python category_builder.py --rho=2 --n=20 ford chevy
```

The seeds to expand are provided on the command line as positional arguments and should be lowercase. Compound names (e.g., "New York") should be quoted.

``` shell
python category_builder.py chicago "new york"
```

### More examples to try

* ford stallone
* cancer diabetes
* cancer taurus


## How to do analogies

The same system can solve analogies such as "What is the mount everest of africa?"

``` shell
python analogy.py "mount everest" africa
```

