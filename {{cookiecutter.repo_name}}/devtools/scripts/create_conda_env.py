import argparse
import yaml  # Requires PyYAML
import os
import re
import shutil
import subprocess as sp
from tempfile import NamedTemporaryFile

# Args
parser = argparse.ArgumentParser(description='Creates a conda environment from file for a given Python version.')
parser.add_argument('-n', '--name', type=str,
                    help='The name of the created Python environment')
parser.add_argument('-p', '--python', type=str,
                    help='The version of the created Python environment')
parser.add_argument('conda_file',
                    help='The file for the created Python environment')

args = parser.parse_args()

# Open the base file
with open(args.conda_file, "r") as handle:
    yaml_script = yaml.load(handle.read())

# Make changes based on the options
# Python
python_replacement_string = "python {}*".format(args.python[0])
try:
    for dep_index, dep_value in enumerate(yaml_script['dependencies']):
        if re.match('python([ ><=*]+[0-9.*]*)?$', dep_value):  # Match explicitly 'python' and its formats
            yaml_script['dependencies'].pop(dep_index)
            break  # Making the assumption there is only one Python entry, also avoids need to enumerate in reverse
except KeyError:
    # Case of no dependencies key
    yaml_script['dependencies'] = []
finally:
    # Ensure the python version is added in. Even if the code does not need it, we assume the env does
    yaml_script['dependencies'].insert(0, python_replacement_string)

# Figure out conda path
if "CONDA_EXE" in os.environ:
    conda_path = os.environ["CONDA_EXE"]
else:
    conda_path = shutil.which("conda")
if conda_path is None:
    raise RuntimeError("Could not find a conda binary in CONDA_EXE variable or in executable search path")

print("CONDA ENV NAME  {}".format(args.name))
print("PYTHON VERSION  {}".format(args.python))
print("CONDA FILE NAME {}".format(args.conda_file))
print("CONDA PATH      {}".format(conda_path))

# Write to a temp file which will always be cleaned up
with NamedTemporaryFile() as temp_file:
    temp_file.write(yaml.dump(yaml_script).encode())  # Temp files opened as binaries, must encode
    temp_file.seek(0)  # Ensure head is moved to start since file never closes (it will delete if closed)
    sp.call("{} env create -n {} -f {}".format(conda_path, args.name, temp_file.name), shell=True)
