This set of tools can be used to start and monitor jobs on LXBATCH.
It will monitor every job individually and resubmit it in case of failure. 
There is a maximum number of trials before the monitor stops resubmitting
the jobs. It consists of a python server and a python client, both
running pyro (Python Remote Objects). 

The server keeps track of all the batches, generates the jobs, monitor
them and resubmit in case of failure. 

The client connects to the server and receives informations about 
the batches running on the server. It has a curse interface that shows 
two different screens. 
 - The first is the main menu, displaying the list of
 existing batches. The top menu gives the list of available commands. Use
 the arrow keys to navigate through the batches and the screen. Up and
 down to select a different batch. Right to see the details of the batch
 (second screen). The delete key will remove the batch from the server
 (stop monitoring only, do not actually kills or remove the jobs). 
 Finally a capital K will stop the server (WARNING! When stopped the
 server forgets all the batches).
 - The second screen shows the details of the selected batch, with 
 information about the batch itself, statistics about the jobs. It also
 gives access to commands to generate the jobs or re-generate them when
 completely failed. The left key goes back to the main screen.
	
To initiate the connection with the server, the client needs to know the 
ip address where the server runs. When starting the server writes this
information in a file (.ns.cfg) in the HOME of the user. This is where the
client retrieve the information.


batchMon.py Usage
--------------
batchMon.py [-h] [-q QUEUE] [-t] [-n NAME] [-x] [-k] [--limit]
				[(-c CONFIG | -l LOAD)] [-s]

optional arguments:
	-h, --help        	show this help message and exit
	-q QUEUE, --queue 	Indicates on which LXBATCH queue the jobs will be submitted
	--limit				Maximum number of concurrently running jobs
	-t, --test			When restarting a series of job, for each job 
							test if the output file already exists. If yes, 
							skip the job (do not regenerate existing output files)
	-n NAME, --name 	Name of the batch
	-k, --keep			Do not delete the LXBATCH output (LSFJOB_xxxxxxx)
	-c CONFIG, --config Configuration file to use (new batch)
	-l LOAD, --load 	Reload a previous batch (restart tracking the jobs,
							do not regenerate them)
	-s, --submit		Submit a batch, request the job generation and exit

Specifying no option will only open the normal curse interface without creating any
batch.

batchServer.py Usage
--------------------
batServer.py [-dn] [-t] [-h|-help|help]
	-dn:  Print debugging information according to the debug level n: 0=No debug, 1=Error, 2=Warning, 3=Info
	-t: Activate tracing
	-h|-help|help: Print this help


Configuration file
------------------
The configuration file is parsed and defines the monitor. 
Several fields are mandatory:
	o listFile : path to a file containing the list of files to process
	o executable : path to the main executable to run

Others are not:
	o optTemplate :	line to use as argument for the executable (templated)
	o preExecute :	bash script to execute before starting the executable
						(templated)
	o postExecute :	bash script to execute after the executable finished
						it's execution (templated)
	o startIndex :	starting index in the input list file 
	o maxJobs : 	maximum number of files to read fron the input list
						file
	o maxAttempts :	maximum attempts before giving up on a job
	o outputDir : 	path to a directory where the monitor can find the
						output files
	o outputFile :	name of the ouput file (templated)
	o requirement :	specify requirement for bsub (-R flag)
	o finalScript :	script executed when all jobs are successfully finished
						(can be used to create a new batch)
	o jobsGrouping: number of input files to group in a single job. 
						Example: with 202 input files and jobsGrouping = 100,
						3 jobs will be created. The first job run over the
						100 first files, the second over the 100 next and
						the third over the last 2 files.

The fields marked as "templated" can use of the following placeholder that
will be replaced when submitting the job:
	o $jobIndex : 		will be replaced by the index of the job (=file index
							in the list of files)
	o $fileNameArr[n] :	will be replaced by the file name of the nth file in
							the list of input files of the job	
	o $fileName :  		will be replaced by the file name of the first input 
							file of the job
	o $fileList :		will be replaced by a list of the input files name
							of the job separated by \n
	o $outputDir : 		will be replaced by the output directory as defined by
							the outputDir field
	o $outputFile :		will be replaced by the filename as defined by the
							outputFile field
