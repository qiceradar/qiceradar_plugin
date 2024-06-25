import pathlib
import shutil
import sqlite3
import subprocess
import tempfile
from typing import Callable, Dict

import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets
import requests  # for downloading files
from qgis.core import QgsMessageLog

from .qiceradar_config import UserConfig

# TODO: should have already been configured after download?
#     (I think this is meant to allow user to change config if
#     they discvoer it's necessary during a download attempt.)
from .qiceradar_config_widget import QIceRadarConfigWidget
from .radar_viewer_data_utils import get_granule_filepath


class RadarViewerDownloadWidget(QtWidgets.QDialog):
    def __init__(
        self,
        config: UserConfig,
        config_cb: Callable[[UserConfig], None],
        attributes: Dict[str, str],
        database_file: str,
    ):
        super(RadarViewerDownloadWidget, self).__init__()

        self.user_config = config
        self.set_config = config_cb
        self.attributes = attributes  # attributes from the feature
        self.database_file = database_file  # database with metadata
        self.setup_ui()

    def setup_ui(self):
        """
        UI should be something like:

        ------------ (campaign-specific widget)

        KOPRI-KRT1 data can be found at:
        Download the zip file and extract it to:
        Then try again.

        (only an OK button)

        ----


        -----
        # TODO/QUESTION: should downloader + viewer work at the segment or granule level?
        #    for now, I'm dealing with granules, but I kind of expect that it will be
        #    preferable to shove them all together.
        UTIG-??? data can be automatically downloaded.
        URI:

        The requested granule is _______ (MB/GB)
        """
        QgsMessageLog.logMessage(f"Setting up download widget for feature with attributes: {self.attributes}")
        region = self.attributes["region"]
        institution = self.attributes["institution"]
        campaign = self.attributes["campaign"]
        segment = self.attributes["segment"]
        granule = self.attributes["granule"]

        # TODO: Look up data from granules table:
        # download_method
        # url
        # destination_path
        # filesize
        connection = sqlite3.connect(self.database_file)
        cursor = connection.cursor()
        granule_name = f"{institution}_{campaign}_{granule}"
        sql_cmd = f"SELECT * FROM granules where name = '{granule_name}'"
        result = cursor.execute(sql_cmd)
        rows = result.fetchall()
        connection.close()
        # QUESTION: How do I want to log this? I need to figure out how these errors
        #    will propagate through the system.
        try:
            _, _, data_format, download_method, url, destination_path, filesize = rows[0]
        except:
            QgsMessageLog.logMessage(f"Invalid response {rows} from command {sql_cmd}")
            data_format, download_method, url, destination_path, filesize = None, None, None, None, None

        granule_filepath = pathlib.Path(self.user_config.rootdir, destination_path)

        self.intro_text = QtWidgets.QLabel(
            "".join(
                [
                    "Unable to find radargram in your filesystem. \n\n",
                    f"institution: {institution} \n",
                    f"campaign: {campaign} \n",
                    f"granule: {granule} \n\n",
                    "Expected to be at: \n",
                    str(granule_filepath),
                ]
            )
        )

        # Rather than being institution-specific, this should switch
        # on download_method.
        self.provider_widget = None
        if download_method == "wget":
            self.provider_widget = RadarViewerWgetDownloadWidget(
                self.user_config, url, granule_filepath, filesize
            )

        self.config_widget = QIceRadarConfigWidget(
            None, self.user_config, self.set_config
        )

        # TODO: I don't love this. Better to only create the config
        #   widget if/when needed. Add indirection via self.handle_config_button_clicked
        self.config_button = QtWidgets.QPushButton("Edit Config")
        self.config_button.clicked.connect(self.config_widget.run)
        # QUESTION: I'm not sure whether it's better to just start over, or
        #           try to update the config here. User would probably prefer
        #           being dumped back out into the download window, but getting
        #           the updated config isn't super clean.
        #           Easier to have them re-start.
        self.config_widget.closed.connect(self.close)

        self.vbox_layout = QtWidgets.QVBoxLayout()
        self.vbox_layout.addWidget(self.intro_text)
        self.vbox_layout.addStretch(1)
        self.vbox_layout.addWidget(self.config_button)
        self.vbox_layout.addWidget(HorizontalLine())
        self.vbox_layout.addStretch(1)

        if self.provider_widget is None:
            QgsMessageLog.logMessage(
                f"BUG: Unable to help download data from {institution}, even though it should be supported"
            )
        else:
            self.provider_widget.closed.connect(self.close)
            self.vbox_layout.addWidget(self.provider_widget)
            # TODO: close this widget when the internal one's button is clicked?

        self.setLayout(self.vbox_layout)
        self.setWindowTitle("Download Data")

    def run(self):
        QgsMessageLog.logMessage("RadarViewerDownloadWidget.run()")
        self.exec()


# TODO: This should probably have a base class, then derived ones that
#   change the text in the info label + how the download is performed.
class RadarViewerWgetDownloadWidget(QtWidgets.QWidget):
    closed = QtCore.pyqtSignal()

    def __init__(
        self, config: UserConfig, url: str, destination_filepath: pathlib.Path, filesize: int
    ):
        super(RadarViewerWgetDownloadWidget, self).__init__()
        QgsMessageLog.logMessage("initializing RadarViewerWgetDownloadWidget")
        self.user_config = config
        self.url = url
        self.destination_filepath = destination_filepath
        self.filesize = filesize
        self.setup_ui()

    def download_clicked(self, _event):
        # Create destination directory
        self.destination_filepath.parents[0].mkdir(parents=True, exist_ok=True)
        QgsMessageLog.logMessage("TODO: Actually download radargram!")
        # TODO: use self.url and self.destination_filepath to construct wget call!
        try:
            # Create a temporary file to avoid having to clean up partial downloads.
            # This may not be ideal if the temporary file is created in a different filesystem than the
            # output file belongs in. (I expect to eventually be downloading data to an external drive/NAS)
            # TODO: create the temporary file in the same directory? or in the RadarData directory?
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                # wget_cmd = ["wget", "--no-clobber", "--quiet", "--output-document", dest_filepath, flight['url']]
                # If saving to a temp file, get rid of --no-clobber, since the file will already have been created.
                # TODO: For windows, will probably need another approach. requests or urllib might be good?
                # https://stackoverflow.com/questions/24346872/python-equivalent-of-a-given-wget-command
                wget_cmd = [
                    "wget",
                    "--quiet",
                    "--output-document",
                    temp_file.name,
                    self.url,
                ]
                QgsMessageLog.logMessage(f"Starting to download: {self.url}")
                QgsMessageLog.logMessage(f"Temporary file: {temp_file.name}")
                # subprocess.check_call(wget_cmd)
                # TODO: for plugin download, replace this with
                #       `shutil.move` for cross-platform compatibility
                req = requests.get(self.url)
                open(temp_file.name, 'wb').write(req.content)
                shutil.move(temp_file.name, self.destination_filepath)
                QgsMessageLog.logMessage(f"Got {self.destination_filepath}")
        except subprocess.CalledProcessError as ex:
            print(f"Failed to download: {self.url} \n\n error: {ex}")
        self.closed.emit()

    def setup_ui(self):
        # TODO: The database needs to include file sizes, and where
        #   to download.
        # TODO: format this string more nicely?
        filesize_kb = self.filesize / (1024)
        filesize_mb = self.filesize / (1024**2)
        filesize_gb = self.filesize / (1024**3)
        if filesize_gb > 1:
            filesize_str = f"{filesize_gb:0.1f} GB"
        elif filesize_mb > 1:
            filesize_str = f"{filesize_mb:0.1f} MB"
        elif filesize_kb > 1:
            filesize_str = f"{filesize_kb:0.1f} KB"
        else:
            filesize_str = f"{self.filesize} Bytes"

        self.info_label = QtWidgets.QLabel(
            "".join(
                [
                    f"The requested transect is {filesize_str}\n",
                    "And can be downloaded from: \n",
                    self.url,
                    "\n\n Destination: \n",
                    str(self.destination_filepath)
                ]
            )
        )
        self.info_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)

        self.cancel_pushbutton = QtWidgets.QPushButton("Cancel")
        self.cancel_pushbutton.clicked.connect(self.closed.emit)
        self.download_pushbutton = QtWidgets.QPushButton("Download")
        self.download_pushbutton.clicked.connect(self.download_clicked)

        self.button_hbox = QtWidgets.QHBoxLayout()
        self.button_hbox.addWidget(self.cancel_pushbutton)
        self.button_hbox.addStretch(1)
        self.button_hbox.addWidget(self.download_pushbutton)

        self.main_vbox = QtWidgets.QVBoxLayout()
        self.main_vbox.addWidget(self.info_label)
        self.main_vbox.addLayout(self.button_hbox)
        self.setLayout(self.main_vbox)


class HorizontalLine(QtWidgets.QFrame):
    def __init__(self):
        super(HorizontalLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


class VerticalLine(QtWidgets.QFrame):
    def __init__(self):
        super(VerticalLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
