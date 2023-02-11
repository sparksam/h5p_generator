import socketserver
import zipfile
import os
import tempfile
import logging
import time
import shutil

import  http.server

def create_temporary_dir() -> str:
    """
    Create  a temporary folder in the temp folder

    Returns:
        str: Temporary directory
    """
    storage_dir = f"{os.sep.join([tempfile.gettempdir(), str(time.time())])}"
    # TODO fail if the folder could not be created
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)
    return storage_dir


def h5p_zipper(source_dir: str, filename: str, destination_dir: str):
    generated_zip = os.sep.join([destination_dir, filename])
    with zipfile.ZipFile(generated_zip, 'w') as zip_object:
        for folder_name, sub_folders, file_names in os.walk(source_dir):
            for filename in file_names:
                # print(os.path.basename(os.path.join(folder_name, filename)))
                file_path = os.path.join(folder_name, filename)
                zip_object.write(file_path, file_path.replace(source_dir, ""))


def h5p_unzipper(source_dir: str, filename: str, destination_dir: str):
    file_path = os.sep.join([source_dir, filename])
    with zipfile.ZipFile(file=file_path, mode='r') as zip_ref:
        zip_ref.extractall(destination_dir)


def handler_from(directory):
    def _init(self, *args, **kwargs):
        return http.server.SimpleHTTPRequestHandler.__init__(self, *args, directory=self.directory, **kwargs)
    return type(f'HandlerFrom<{directory}>',
                (http.server.SimpleHTTPRequestHandler,),
                {'__init__': _init, 'directory': directory})


def launch_web_server(source_dir: str, filename: str):
    server_root_dir =  f"{os.sep.join([tempfile.gettempdir(), str(time.time())])}"
    shutil.copytree(src="viewer", dst=server_root_dir)
    logging.info(f"Server Root dir: {server_root_dir}")
    os.makedirs(os.sep.join([server_root_dir, "h5p_dir"]), exist_ok=True)
    h5p_unzipper(source_dir=source_dir, filename=filename,
                 destination_dir=os.sep.join([server_root_dir, "h5p_dir"]))

    port = 8080
    with socketserver.TCPServer(("", port), handler_from(server_root_dir)) as httpd:
        logging.info(
            f"Serving HTTP on localhost port {port} (http://localhost:{port}/) ... from {server_root_dir}")
        httpd.serve_forever()


if __name__ == '__main__':
    logging.root.setLevel(logging.DEBUG)
    source_dir = "templates"
    filename = "H5P.Accordion.h5p"
    launch_web_server(source_dir=source_dir, filename=filename)
    # temporary_dir = create_temporary_dir()
    # logging.info(f"Temporary Folder: {temporary_dir}")
    # h5p_unzipper(source_dir=source_dir, filename=filename,
    #              destination_dir=temporary_dir)
    # h5p_zipper(destination_dir="generated", filename="test.h5p",
    #            source_dir=temporary_dir)


