import re
import pandas as pd
import openpyxl
from pathlib import Path
import os
import json
import zipfile
from pathlib import Path


def get_uploads_files(upload_dir=r'.\uploads'):
    upload_dir = Path(upload_dir)
    if upload_dir.exists() and upload_dir.is_dir():
        return [child for child in upload_dir.iterdir()]
    else:
        print("Directory ", upload_dir.name, " doesn't exist")
        return []


def get_validated_files(files):
    for v in files.values():
        if not v:
            return False
    return True


def purge_file(dir_name=Path(r'.\uploads')):
    if get_uploads_files(dir_name) != []:
        for file in get_uploads_files(dir_name):
            file.unlink()


def validate_file_dg(file, type):
    """

    :param file: Path (pathlib) to the file to validate
    :param type: what file it is (network_file, source_file, open_file, limit_file)
    :return: The type of file it is for the study, None is not valitated
    """
    cols = {
        "network_file": {
            "section",
            "start",
            "end"
        },
        "source_file": {"source"},
        "open_file": {"section"},
        "limit_file": {
            "node",
            "limit",
            "type",
            "x",
            "y",
            "dg",
            "c"
        },
    }

    try:
        df = pd.DataFrame(pd.read_csv(file))
    except:
        try:
            df = pd.DataFrame(pd.read_excel(file, engine='openpyxl'))
        except openpyxl.utils.exceptions.InvalidFileException as notXL:
            return None

    if cols[type].issubset(df.columns.to_list()) or cols[type].issubset(df.columns.to_list()):
        return type
    else:
        missing_col = cols[type] - set(df.columns.to_list())
        raise ValueError(
            "Les colonnes {0} du fichier '{1}' semblent être manquantes ou mal écrite dans les fichiers "
            "fournis".format(missing_col, file.name)
        )



def full_paths(upload_dir):
    return upload_dir / "*"


def create_dir_if_dont_exist(dir_name):
    Path(dir_name).mkdir(parents=True, exist_ok=True)
    return Path(dir_name)


def zip_files(list_of_files, zip_file_name=''):
    """
    Generate a zip file from a list of files in the location of the first file of the list
    :param list_of_files:
    :type list_of_files:
    :param zip_file_name:
    :type zip_file_name:
    :return:
    :rtype:
    """

    if zip_file_name == '':
        file_name = Path(list_of_files[0]).parent

    # the current working directory is changed to the directory of the first file in the list
    # return to the previous directory after saving
    previous_dir = Path.cwd()
    wd = Path(list_of_files[0]).parent
    os.chdir(wd)
    zip_file_name += '.zip'
    with zipfile.ZipFile(zip_file_name,
                         "w",
                         zipfile.ZIP_DEFLATED,
                         allowZip64=True) as zf:
        for file in list_of_files:
            zf.write(Path(file).name)

    zippath = wd.joinpath(zip_file_name)
    os.chdir(previous_dir)
    return zippath.name


def decode_str_filename(str_filename):
    try:
        test_str = eval(str_filename)
        if len(test_str[0]) > 1:
            return test_str, 'list'
        else:
            return str_filename, 'str'
    except NameError or IndexError:
        return str_filename, 'str'


def add_to_list_file(filename, *items):
    with open(filename, 'a') as file:
        for item in items:
            file.write(item)
            file.write('\n')
    file.close()


def get_items_from_file(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            lines = [line.rstrip('\n') for line in file]
        file.close()

        return lines

    else:
        return []


def get_items_from_json(filename):
    if os.path.exists(filename):
        with open('data.json') as json_file:
            data = json.load(json_file)

        return data


def save_items_as_json(data, path, filename="data.json"):
    json_object = json.dumps(data, indent=4)
    filepath = os.path.join(path, filename)
    with open(filepath, "w") as outfile:
        outfile.write(json_object)

    return filename, filepath


