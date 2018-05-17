# Category Builder

This repository contains data and code for the Category Builder system.

Category Builder can do set expansion while dealing robustly with polysemy.
See category_builder_paper.pdf in this directory.

## How to use Category Builder

``` shell
git clone https://github.com/google/categorybuilder
cd categorybuilder
python category_builder.py ford nixon
python category_builder.py --rho=2 --n=20 ford chevy
```

## How to do analogies

The same system can solve analogies such as "What is the mount everest of africa?"

``` shell
python analogy.py "mount everest" africa
```

