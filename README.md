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

_Note: This will take a few minutes to initalize. An sqlite database of about 5.7 GB is produced._

_Note: The initialization uses alive_progress to show progress. You can get it by 'pip3 install alive_progress'._

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

### Example Output

| Seeds   | Expansion |
| :------- | :----------|
|ford, nixon | nixon, obama, bush, johnson, clinton, ford, reagan, ... |
|ford, chevy | ford, chevy, toyota, chevrolet, honda, bmw, nissan, ... |
|ford,  stallone| ford, stallone, khan, kapoor, sylvester stallone, depp, tom cruise, ... |
|cancer, diabetes| cancer, diabetes, disease, asthama, infection, breast cancer, syndrome, ...|
|cancer, taurus| virgo, pisces, libra, taurus, scorpio, saggitarius, cancer, aries, capricorn, aquarius, gemini, leo, ...|
|safari, trip|trip, tour, trips, safari, vacation, adventure, holiday, excursion, cruisetours, journey, ...|
|safari, ie|firefox, internet explorer, chrome, explorer, safari, ie, google chrome, browsers, web browser, ...|
|beautiful, serene|beautiful, serene, peaceful, tranquil, picturesque, quite, lovely, stunning, scenic, secluded, ...|
|beautiful, poignant| beautiful, poignant, romantic, evocative, gorgeous, poetic, haunting, funny, sad, vivid, ...|
|beautiful, chic|elegant, chic, stylish, beautiful, gorgeous, stunning, trendy, lovely, vintage, classy, sleek, ...|


## How to do analogies

The same system can solve analogies such as "What is the mount everest of africa?"

``` shell
python analogy.py "mount everest" africa
```
Note that these are harder than "proportional" analogies such as "hand:glove::foot:?". People don't need to be provided the first term ("hand") and can answer "What is the glove for a foot?"

### Example Output

The items are labeled B and C because analogies are often shown as A:B::C:D.

|  B   | C | What is the B of C? |
|:----|:-----|:---------------------------|
|mount everest|africa| kilimanjaro|
|mount everest|alaska| denali|
|glove | foot | shoe |
|darwin | physics | einstein |
|corolla|honda|honda civic|
|sacramento|indiana|indianapolis|
|dollar|india|rupee|
|football|india|cricket|
|voldemort|tolkien|sauron|
|voldemort|star wars|vader|
|tolkien|voldemort|rowling|

## How to run the evaluation suite

``` shell
python3 eval_set_expansion.py eval_data/cat_eval_data/nfl-teams

python3 eval_analogy.py eval_data/analogy_eval_data/questions-words.txt
```



