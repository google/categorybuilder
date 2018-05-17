# Category Builder

This repository contains data and code for the Category Builder system.

Category Builder can do set expansion while dealing robustly with polysemy.
See category_builder_paper.pdf in this directory.

## Installation
``` shell
git clone https://github.com/google/categorybuilder
cd categorybuilder
git lfs pull
```

## How to use Category Builder
_Note: The first time you run this command it will take a few minutes to initalize._

``` shell
python category_builder.py ford nixon
python category_builder.py --rho=2 --n=20 ford chevy
```

## How to do analogies

The same system can solve analogies such as "What is the mount everest of africa?"

``` shell
python analogy.py "mount everest" africa
```

