# chaser
`chaser` is a set of functions for sorting through eBird data to find diverse birding locations or life birds.

Currently, `chaser` consists of a demonstration, but more flexible functionality will be added soon. 

The demonstration downloads eBird frequency charts for every week of the year for every county in the United States. Then, I clean this data and use a life list downloaded from eBird to find the top three counties to bird in to maximize lifers in Texas, Arizona, and New Mexico during November, December, and January. (For the selected life list, all the best counties are in Texas!)

The pipeline:
* Download eBird frequency charts in R using [download_frequencies.Rmd](https://github.com/rhine3/chaser/blob/master/download_freqs.Rmd).
  * This file uses [rebird](https://github.com/ropensci/rebird) plus general calls to the eBird API. 
* Modules for analyzing eBird frequency charts: [chaser.py](https://github.com/rhine3/chaser/blob/master/chaser.py)
  * For a demonstration of this pipeline, see [analyze_county.ipynb](https://github.com/rhine3/chaser/blob/master/analyze_county.ipynb)
* Use modules to demonstrate a run of `chaser`: [demonstration.ipynb](https://github.com/rhine3/chaser/blob/master/demonstration.ipynb)


