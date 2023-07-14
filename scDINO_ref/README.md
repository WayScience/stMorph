# Running scDINO via Snakemake on Local Machine
### This file contains snakemake command for computing CLS features throughs scDINO on local machine
## Notes: 
* Must download scDINO and full checkpoint pre-trained scDINO model and run snakemake command from that directory.
* `only_downstream_analyses.yaml` contains a reference configuration file, but configurations must be set within the file in scDINO.

~~~
snakemake -s only_downstream_snakefile --until compute_CLS_features --configfile="configs/only_downstream_analyses.yaml" --cores all
~~~
