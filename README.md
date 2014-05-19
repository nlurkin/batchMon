This tool can be used to start and monitor jobs on LXBATCH.
It will monitor every job individually and resubmit it in
ase of failure.
There is a maximum number of trials before the monitor
stops resubmitting the jobs.

Usage
-----
batchMon.py [-h] [-q QUEUE] [-t] [-n NAME] [-x] [-k]
				(-c CONFIG | -l LOAD)

optional arguments:
	-h, --help        	show this help message and exit
	-q QUEUE, --queue 	Indicates on which LXBATCH queue the jobs will be submitted
	-t, --test				When restarting a series of job, for each job 
	`							test if the output file already exists. If yes, 
								skip the job (do not regenerate existing output files)
	-n NAME, --name 		Name of the monitor (used for later recovery)
	-x, --nocurse			Disable the curse interface
	-k, --keep				Do not delete the LXBATCH output (LSFJOB_xxxxxxx)
	-c CONFIG, --config  Configuration file to use (new monitor)
	-l LOAD, --load 		Reload a previous monitor (restart tracking the jobs,
								do not regenerate them)

-c or -l is required.

Configuration file
------------------
The configuration file is parsed and defintes the monitor. 
Several fields are mandatory:
	o listFile : path to a file containing the list of files to process
	o executable : path to the main executable to run

Others are not:
	o optTemplate :line to use as argument for the
						executable 	(templated)
	o preExecute : bash script to execute before starting 
						the executable (templated)
	o postExecute :bash script to execute after the 
						executable finished it's execution 
						(templated)
	o startIndex : starting index in the input list file
	o maxJobs : 	maximum number of files to read fron the
						input list file
	o maxAttempts :maximum attempts before giving up on a job
	o outputDir : 	path to a directory where the monitor 
						can find the output files
	o outputFile : name of the ouput file (templated)

The fields marked as "templated" can use of the following 
placeholder that will be replaced when submitting the job:
	o $jobIndex : 	will be replaced by the index of the job
						(=file index in the list of files)
	o $fileName :  will be replaced by the input file name
	o $outputDir : will be replaced by the output directory
						as defined by the outputDir field
	o $outputFile :will be replaced by the filename as defined
						by the outputFile field

