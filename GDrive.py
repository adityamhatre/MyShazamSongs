import os.path
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from Logger import info, error

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']


def notify(name, crashed=False, customText=False):
    from pyfcm import FCMNotification

    push_service = FCMNotification(api_key="api_key")
    registration_id = "device_registration_token"
    message_title = "Song downloaded!" if not crashed else "Program crashed"

    if customText:
        message_title = "My Shazam Songs"
    if not customText:
        message_body = "Your song \"{}\" is ready in Google Drive (my.shazam.songs@gmail.com)".format(
            name) if not crashed else name
    else:
        message_body = name

    if not crashed:
        result = push_service.notify_single_device(registration_id=registration_id, message_title=message_title,
                                                   message_body=message_body)
        if result['success'] == 1:
            info("Notification sent for song {}".format(
                name) if not crashed else "Crash notification sent with msg = {}".format(name))


class GDrive:
    def __init__(self):
        self.service = None

    def authorize(self):
        """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        else:
            error("token.pickle doesn't exist")
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # notify("Login again", crashed=True)
                error("Creds expired. Refreshing....")
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        info("Authorized with Drive API")
        self.service = build('drive', 'v3', credentials=creds)

    def upload(self, key, name, file_path):
        try:
            self.authorize()
            file_metadata = {'name': name, 'key': key}
            media = MediaFileUpload(file_path, mimetype='audio/mpeg')
            result_file = self.service.files().create(body=file_metadata,
                                                      media_body=media,
                                                      fields='id').execute()
            info("Song {} uploaded to drive".format(name))
            self.delete_duplicate()
            return True if result_file else False
        except Exception:
            import traceback
            traceback.print_exc()
            stacktrace = traceback.format_exc()
            error(stacktrace)

    def delete_duplicate(self):
        info("Deleting duplicate files in drive")
        try:
            self.authorize()
            pageToken = None
            songs = []
            dups = {}
            while True:
                results = self.service.files().list(pageToken=pageToken,
                                                    fields="nextPageToken, files(id,name,modifiedTime)",
                                                    orderBy="modifiedTime asc").execute()
                items = results.get('files', [])
                pageToken = results.get('nextPageToken', None)
                songs += items
                if pageToken is None:
                    break

            found_dups = False
            for song in songs:
                if song['name'] in dups:
                    found_dups = True
                    dups[song["name"]].append(
                        {'name': song['name'], 'id': song['id'], 'modifiedTime': song['modifiedTime']})
                else:
                    dups[song["name"]] = [
                        {'name': song['name'], 'id': song['id'], 'modifiedTime': song['modifiedTime']}]
            if found_dups:
                info("No duplicate files found")
            for dup in dups:
                if len(dups[dup]) > 1:
                    others = sorted(dups[dup], key=lambda x: x['modifiedTime'])[1:]

                    for inst in others:
                        info(("Deleting duplicate song: {}".format(inst['name'])))
                        self.service.files().delete(fileId=inst['id']).execute()
        except Exception:
            import traceback
            traceback.print_exc()
            stacktrace = traceback.format_exc()
            error(stacktrace)
