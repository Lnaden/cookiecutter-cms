import argparse
import yaml
import os
import re
import shutil
import subprocess as sp

# Args
parser = argparse.ArgumentParser(description='Creates a conda environment from file for a given Python version.')
parser.add_argument('-n', '--name', type=str, nargs=1,
                    help='The name of the created Python environment')
parser.add_argument('-p', '--python', type=str, nargs=1,
                    help='The version of the created Python environment')
parser.add_argument('conda_file', nargs='*',
                    help='The file for the created Python environment')

args = parser.parse_args()

# Open the base file
with open(args.conda_file[0], "r") as handle:
    yaml_script = yaml.load(handle.read())

tmp_file = "tmp_env.yaml"

# Make changes based on the options
# Python
python_replacement_string = "python {}*".format(args.python[0])
try:  # Python
    for dep_index, dep_value in enumerate(yaml_script['dependencies']):
        if re.match('python([ ><=*]+[0-9.*]*)?$', dep_value):  # Match explicitly 'python' and its formats
            yaml_script['dependencies'][dep_index] = python_replacement_string
            break  # Making the assumption there is only one Python entry
except KeyError:
    # Case of no dependencies key
    yaml_script['dependencies'] = [python_replacement_string]

with open(tmp_file, "w") as handle:
    handle.write(yaml.dump(yaml_script))

# Figure out conda path
if "CONDA_EXE" in os.environ:
    conda_path = os.environ["CONDA_EXE"]
else:
    conda_path = shutil.which("conda")

print("CONDA ENV NAME  {}".format(args.name[0]))
print("PYTHON VERSION  {}".format(args.python[0]))
print("CONDA FILE NAME {}".format(args.conda_file[0]))
print("CONDA PATH      {}".format(conda_path))

sp.call("{} env create -n {} -f {}".format(conda_path, args.name[0], tmp_file), shell=True)
os.remove(tmp_file)
