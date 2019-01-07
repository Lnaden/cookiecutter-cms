import argparse
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
    script = handle.read()

# Make changes based on the options (not relying on YAML)
# Determine whitespace level of first non-commented line
try:
    whitespace = re.search('^[\r\n]*?([ \t\f]*)[^\#\s]', script, re.MULTILINE).group(1)
except AttributeError:
    raise RuntimeError("The input Conda Environment File is either all comments or not YAML formatted. "
                       "Please check your file")
# Python
python_replacement_string = "- python {}*".format(args.python)
dep_entry = re.search('^{}dependencies:'.format(whitespace), script, re.MULTILINE)
if not dep_entry:
    # Case of no dependencies entry
    script += '\n{ws}dependencies:\n{ws} {py}'.format(ws=whitespace, py=python_replacement_string)
else:
    # Calculate the end of the dependencies
    try:
        dep_span = re.search('^[\r\n]*{}[^\#\s-]'.format(whitespace), script[dep_entry.end():], re.MULTILINE).start()
    except AttributeError:
        dep_span = None
    # Calculate whitespace of dependencies
    dep_whitespace_re = re.search('^[\r\n]*?{}([ \t\f]*)-'.format(whitespace),
                                  script[dep_entry.end():dep_span],
                                  re.MULTILINE)
    if dep_whitespace_re is None:
        # Dependencies entry, but no values
        dep_block = '\n{ws} {py}\n'.format(ws=whitespace, py=python_replacement_string)
    else:
        dep_block = script[dep_entry.end():dep_span]
        dep_whitespace = dep_whitespace_re.group(1)
        if not re.search('^[\r\n]*?{}{}-[ \t]*python'.format(whitespace, dep_whitespace), dep_block,
                         re.MULTILINE):
            # Dependencies but no uncommented python
            dep_block += '\n{ws}{dws}{py}\n'.format(ws=whitespace, dws=dep_whitespace, py=python_replacement_string)
        else:
            # Finally: Dependencies with fields and one of them is python
            dep_block = re.sub(r'-[ \t]*python([ ><=*]+[0-9.*]*)?$', python_replacement_string, dep_block,
                               flags=re.MULTILINE)
    final_script = script[:dep_entry.end()] + dep_block
    if dep_span is not None:
        final_script += script[dep_span:]
    script = final_script

# try:
#     for dep_index, dep_value in enumerate(yaml_script['dependencies']):
#         if re.match('python([ ><=*]+[0-9.*]*)?$', dep_value):  # Match explicitly 'python' and its formats
#             yaml_script['dependencies'].pop(dep_index)
#             break  # Making the assumption there is only one Python entry, also avoids need to enumerate in reverse
# except KeyError:
#     # Case of no dependencies key
#     yaml_script['dependencies'] = []
# finally:
#     # Ensure the python version is added in. Even if the code does not need it, we assume the env does
#     yaml_script['dependencies'].insert(0, python_replacement_string)

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
    # temp_file.write(yaml.dump(yaml_script).encode())  # Temp files opened as binaries, must encode
    temp_file.write(script.encode())  # Temp files opened as binaries, must encode
    temp_file.seek(0)  # Ensure head is moved to start since file never closes (it will delete if closed)
    temp_file.flush()  # Fix for Windows machines which need more than just seek
    sp.call("{} env create -n {} -f {}".format(conda_path, args.name, temp_file.name), shell=True)
