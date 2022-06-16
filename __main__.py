import os.path
import httplib2
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
import tkinter
import tkinter.filedialog
import tkinter.simpledialog

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client import file, client, tools


class Uploader():
    def __init__(self, secret_filename, credentials_filename):
        store = file.Storage(credentials_filename)
        credentials = store.get()

        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(
                secret_filename, 'https://www.googleapis.com/auth/drive.file')
            credentials = tools.run_flow(flow, store)

        self.drive = build(
            'drive', 'v3', http=credentials.authorize(httplib2.Http()))

    def upload(self, path):
        filename = os.path.basename(path)
        metadata = {'name': filename}
        media = MediaFileUpload(filename)

        self.drive.files().create(body=metadata, media_body=media).execute()
        print('Uploaded: ' + filename)


class Handler(FileSystemEventHandler):
    def __init__(self, filenames, uploader) -> None:
        super().__init__()
        self.filenames = filenames
        self.uploader = uploader

    def on_created(self, event: FileCreatedEvent):
        if not isinstance(event, FileCreatedEvent):
            return

        filename = os.path.basename(event.src_path)
        if filename not in self.filenames:
            return

        self.uploader.upload(event.src_path)


class Watcher:
    def __init__(self, dirname, filenames, uploader) -> None:
        self.observer = Observer()
        self.dirname = dirname
        self.filenames = filenames
        self.uploader = uploader
        pass

    def start(self):
        self.observer.schedule(Handler(self.filenames, self.uploader),
                               self.dirname, recursive=False)
        self.observer.start()

        try:
            while True:
                pass
        except KeyboardInterrupt:
            self.observer.stop()

        self.observer.join()


class Dialog:
    def get_names(self):
        dir_name = tkinter.filedialog.askdirectory(
            title='Directory file will be saved into')
        if dir_name is None:
            return (None, None)

        file_names = tkinter.simpledialog.askstring(
            'File name', 'File name that will be saved (with extension, separate multiple names with commas)')
        if file_names == None:
            return (None, None)

        return (dir_name, [e.strip() for e in file_names.split(',')])


def main():
    uploader = Uploader('secret.json', 'credentials.json')

    dialog = Dialog()
    (dirname, filenames) = dialog.get_names()

    if dirname is None or filenames is None:
        print('Canceled')
        return

    watcher = Watcher(dirname, filenames, uploader)
    watcher.start()


if __name__ == '__main__':
    main()
