# -*- coding: utf-8 -*-
import os
import pathlib
import secrets

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename

from .utils.File import get_uploads_files, purge_file, full_paths, \
    create_dir_if_dont_exist as create_dir, zip_files, add_to_list_file, get_items_from_file, \
    save_items_as_json, validate_file_dg, get_validated_files

from .utils.dg_allocation_tool import run_dg_analysis
from .utils.node_map_tool import run_nm_analysis

app = Flask(__name__)
app.secret_key = secrets.token_bytes()
app.config['ROOT_DIR'] = pathlib.Path(__file__)

app.config['MAX_CONTENT_LENGTH'] = 3072 * 3072
app.config['UPLOAD_EXTENSIONS'] = ['.csv', '.xlsx', '.xls']
app.config['UPLOAD_PATH'] = create_dir('uploads')
app.config['UPLOAD_PATH_DG'] = create_dir('uploads/dg_allocation')
app.config['GENERATED_PATH_DG'] = create_dir('generated/dg_allocation')
app.config['UPLOAD_PATH_NM'] = create_dir('uploads/node_map')
app.config['GENERATED_PATH_NM'] = create_dir('generated/node_map')
app.config['GENERATED_PATH'] = create_dir(r'generated')
app.config['FILES_DG'] = {
    "network_file": False,
    "source_file": False,
    "open_file": False,
    "limit_file": False
}

app.config['FILES_NM'] = {
    "network_file": False,
    "source_file": False,
    "open_file": False
}

app.config['CURRENT_OUTPUT_FILE'] = ''


@app.route('/')
def index():
    return render_template('accueil.html')


@app.route('/dg_allocation', methods=['GET', 'POST'])
def dg_allocation():
    app_name ='dg_allocation'
    uploaded_files = get_uploads_files(app.config['UPLOAD_PATH_DG'])
    validated_files = get_validated_files(app.config['FILES_DG'])
    file_dg_ready = False
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
                    path_to_file = pathlib.Path(app.config['UPLOAD_PATH_DG']) / file
                    uploaded_file.save(path_to_file)
                    # valide en ouvrant les fichiers si le contenu est bon
                    try:
                        validate_file_dg(path_to_file, uploaded_file_name)
                        app.config['FILES_DG'][uploaded_file_name] = path_to_file
                    except ValueError as e:
                        os.remove(path_to_file)
                        error_messages.append("{0}".format(e))

            flash("\n".join(error_messages), 'warning')
            return redirect(url_for('dg_allocation'))

        elif request.form['btn_id'] == 'purger' or request.form['btn_id'] == 'terminer':
            return redirect(url_for('purge', app_name=app_name))

        elif request.form['btn_id'] == 'analyser':
            try:
                dg = run_dg_analysis(app.config['FILES_DG'], pathlib.Path(app.config['GENERATED_PATH']/app_name))
                app.config['CURRENT_OUTPUT_FILE'] = dg
                file_dg_ready = True
            except Exception as e:
                error_messages.append("{0}".format(e))
                flash("\n".join(error_messages), 'error')

            return render_template('dg_allocation.html', uploaded_files=uploaded_files, validated_files=validated_files,
                                   file_ready=file_dg_ready)

        elif request.form['btn_id'] == 'telecharger':
            return redirect(url_for('download', app_name=app_name, filename=app.config['CURRENT_OUTPUT_FILE']))

    return render_template('dg_allocation.html', uploaded_files=uploaded_files, validated_files=validated_files,
                           file_ready=file_dg_ready)


@app.route('/node_map', methods=['GET', 'POST'])
def node_map():
    app_name ='node_map'
    uploaded_files = get_uploads_files(app.config['UPLOAD_PATH_NM'])
    validated_nm_files = get_validated_files(app.config['FILES_NM'])
    file_nm_ready = False
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
                    path_to_file = pathlib.Path(app.config['UPLOAD_PATH_NM']) / file
                    uploaded_file.save(path_to_file)
                    # valide en ouvrant les fichiers si le contenu est bon
                    try:
                        validate_file_dg(path_to_file, uploaded_file_name)
                        app.config['FILES_NM'][uploaded_file_name] = path_to_file
                    except ValueError as e:
                        os.remove(path_to_file)
                        error_messages.append("{0}".format(e))

            flash("\n".join(error_messages), 'warning')
            return redirect(url_for('node_map'))

        elif request.form['btn_id'] == 'purger' or request.form['btn_id'] == 'terminer':
            return redirect(url_for('purge', app_name=app_name))

        elif request.form['btn_id'] == 'analyser':
            try:
                nm = run_nm_analysis(app.config['FILES_NM'], pathlib.Path(app.config['GENERATED_PATH']/app_name))
                app.config['CURRENT_OUTPUT_FILE'] = nm
                file_nm_ready = True
            except Exception as e:
                error_messages.append("{0}".format(e))
                flash("\n".join(error_messages), 'error')

            return render_template('node_map.html', uploaded_files=uploaded_files, validated_files=validated_nm_files,
                                   file_ready=file_nm_ready)

        elif request.form['btn_id'] == 'telecharger':
            return redirect(url_for('download', app_name=app_name, file=app.config['CURRENT_OUTPUT_FILE']))

    return render_template('node_map.html', uploaded_files=uploaded_files, validated_files=validated_nm_files,
                           file_ready=file_nm_ready)

@app.route('/<app_name>/<file>/', methods=['GET', 'POST'])
def download(app_name, file):
    directory = os.path.abspath(os.path.join(app.config['GENERATED_PATH'], app_name))
    filename = pathlib.Path(file).name
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

