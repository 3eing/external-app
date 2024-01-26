# -*- coding: utf-8 -*-
import os
import pathlib
import secrets

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename

from .utils.File import get_uploads_files, purge_file, full_paths, \
    create_dir_if_dont_exist as create_dir, zip_files, decode_str_filename, add_to_list_file, get_items_from_file, \
    save_items_as_json, validate_file_dg, get_validated_files

from .utils.dg_allocation_tool import run_dg_analysis
from .utils.node_map_tool import run_nm_analysis

app = Flask(__name__)
app.secret_key = secrets.token_bytes()
app.config['ROOT_DIR'] = pathlib.Path(__file__)

app.config['MAX_CONTENT_LENGTH'] = 3072 * 3072
app.config['UPLOAD_EXTENSIONS'] = ['.csv', '.xlsx', '.xls']
app.config['UPLOAD_PATH'] = create_dir('uploads')
app.config['UPLOAD_PATH_ANALYSIS'] = create_dir('uploads/analysis')
app.config['GENERATED_PATH_ANALYSIS'] = create_dir('generated/analysis')
app.config['GENERATED_PATH'] = create_dir(r'generated')
app.config['FILES'] = {
    "network_file": False,
    "source_file": False,
    "open_file": False,
    "limit_file": False
}

app.config['CURRENT_OUTPUT_FILE'] = ''


@app.route('/')
def index():
    return render_template('accueil.html')


@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    app_name ='analysis'
    uploaded_files = get_uploads_files(app.config['UPLOAD_PATH_ANALYSIS'])
    validated_files = get_validated_files(app.config['FILES'])
    file_ready = False
    error_messages = []

    if request.method == 'POST':
        # ajout de fichier pour analyse
        if request.form['btn_id'] == 'soumettre_fichier':
            submittted_files = request.files
            for uploaded_file_name, uploaded_file in submittted_files.items():
                file = pathlib.Path(secure_filename(uploaded_file.filename))
                if file.name != '':
                    # valide si l'extension des fichiers est bonne
                    if file.suffix not in app.config['UPLOAD_EXTENSIONS']:
                        flash("Les fichiers reçus ne sont des fichiers .csv ou .xlsx", 'error')
                    path_to_file = pathlib.Path(app.config['UPLOAD_PATH_ANALYSIS']) / file
                    uploaded_file.save(path_to_file)
                    # valide en ouvrant les fichiers si le contenu est bon
                    try:
                        validate_file_dg(path_to_file, uploaded_file_name)
                        app.config['FILES'][uploaded_file_name] = path_to_file
                    except ValueError as e:
                        os.remove(path_to_file)
                        error_messages.append("{0}".format(e))

            flash("\n".join(error_messages), 'warning')
            return redirect(url_for('analysis'))

        elif request.form['btn_id'] == 'purger' or request.form['btn_id'] == 'terminer':
            return redirect(url_for('purge', app_name=app_name))

        elif request.form['btn_id'] == 'analyser':
            try:
                file_list = []
                dg = run_dg_analysis(app.config['FILES'], pathlib.Path(app.config['GENERATED_PATH']/app_name))
                nm = run_nm_analysis(app.config['FILES'], pathlib.Path(app.config['GENERATED_PATH']/app_name))
                file_list.append(dg)
                file_list.append(nm)
                app.config['CURRENT_OUTPUT_FILE'] = zip_files(file_list, zip_file_name=app_name + '_result')
                file_ready = True
            except Exception as e:
                error_messages.append("{0}".format(e))
                flash("\n".join(error_messages), 'error')

            return render_template('analysis.html', uploaded_files=uploaded_files, validated_files=validated_files,
                                   file_ready=file_ready)

        elif request.form['btn_id'] == 'telecharger':
            return redirect(url_for('download', app_name=app_name, filename=app.config['CURRENT_OUTPUT_FILE']))

    return render_template('analysis.html', uploaded_files=uploaded_files, validated_files=validated_files,
                           file_ready=file_ready)


@app.route('/<app_name>/<filename>/', methods=['GET', 'POST'])
def download(app_name, filename):
    filename, _type = decode_str_filename(filename)
    if _type == 'list':
        filename = os.path.basename(zip_files(filename, zip_file_name=app_name + '_result'))
    directory = os.path.abspath(os.path.join(app.config['GENERATED_PATH'], app_name))
    return send_from_directory(directory=directory, path=filename,
                               as_attachment=True)


@app.route('/purge/<app_name>', methods=['GET', 'POST'])
def purge(app_name):
    purge_file(os.path.join(app.config['UPLOAD_PATH'], app_name))
    purge_file(os.path.join(app.config['GENERATED_PATH'], app_name))
    return redirect(url_for(app_name))


@app.errorhandler(Exception)
def basic_error(e):
    return "an error occured: " + str(e)

