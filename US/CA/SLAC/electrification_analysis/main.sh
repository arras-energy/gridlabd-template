gridlabd --version
### Check if a directory does not exist ###
if [ ! -d "model_files/" ] 
then
    mkdir model_files
fi
if [ ! -d "output/" ] 
then
    mkdir output
fi
if [ ! -d "output/feeder_plot" ] 
then
    mkdir output/feeder_plot
fi
if [ ! -d "output/feeder_power" ] 
then
    mkdir output/feeder_power
fi
if [ ! -d "output/line_losses" ] 
then
    mkdir output/line_losses
fi
if [ ! -d "output/main_node_power" ] 
then
    mkdir output/main_node_power
fi
if [ ! -d "output/output_loadshapes" ] 
then
    mkdir output/output_loadshapes
fi
if [ ! -d "elec_config/" ] 
then
    mkdir elec_config
fi
if [ ! -d "paneldump/" ] 
then
    mkdir paneldump
fi
python3 main.py
for filename in model_files/*.glm; do 
	gridlabd "$filename"
done
# python3 pythontools/post_process.py
python3 pythontools/feeder_plot.py
