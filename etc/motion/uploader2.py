#!/usr/bin/python2.7
'''
Created on 6 Jun 2012
Modified on 10 Jan 2014
 
@author: Jeremy Blythe
@author: Pascal A.
 
Motion Uploader - uploads videos to Google Drive
 
Read the blog entry at http://jeremyblythe.blogspot.com and/or http://notes.depad.fr for more information
'''
 
import smtplib
from datetime import datetime
 
import os.path
import sys
 
import gdata.data
import gdata.docs.data
import gdata.docs.client
import ConfigParser
 
class MotionUploader:
    def __init__(self, config_file_path):
        # Load config
        config = ConfigParser.ConfigParser()
        config.read(config_file_path)
 
        # GMail account credentials
        self.username = config.get('gmail', 'user')
        self.password = config.get('gmail', 'password')
        self.from_name = config.get('gmail', 'name')
        self.sender = config.get('gmail', 'sender')
 
        # Recipient email address (could be same as from_addr)
        self.recipient = config.get('gmail', 'recipient')
 
        # Subject line for email
        self.subject = config.get('gmail', 'subject')
 
        # First line of email message
        self.message = config.get('gmail', 'message')
 
        # Folder (or collection) in Docs where you want the videos to go
        self.folder = config.get('docs', 'folder')
 
        # Options
        self.delete_after_upload = config.getboolean('options', 'delete-after-upload')
        self.send_email = config.getboolean('options', 'send-email')
 
        self._create_gdata_client()
 
    def _create_gdata_client(self):
        """Create a Documents List Client."""
        self.client = gdata.docs.client.DocsClient(source='motion_uploader')
        self.client.http_client.debug = False
        self.client.client_login(self.username, self.password, service=self.client.auth_service, source=self.client.source)
 
    def _get_folder_resource(self):
        """Return the resource for given folder."""
 
        # Create a query matching exactly a title, and include collections
        q = gdata.docs.client.DocsQuery(
            title=self.folder,
            title_exact='true',
            show_collections='true'
            )
        # Execute the query and get the first entry
        resource = self.client.GetResources(q=q).entry[0]
 
        if resource.title.text == self.folder:
            col = resource
        return col
 
    def _send_email(self,msg):
        '''Send an email using the GMail account.'''
        senddate=datetime.strftime(datetime.now(), '%Y-%m-%d')
        m="Date: %srnFrom: %s <%s>rnTo: %srnSubject: %srnX-Mailer: My-Mailrnrn" % (senddate, self.from_name, self.sender, self.recipient, self.subject)
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.starttls()
        server.login(self.username, self.password)
        server.sendmail(self.sender, self.recipient, m+msg)
        server.quit()
 
    def _upload(self, video_file_path, folder_resource):
        '''Upload the video and return the doc'''
        doc = gdata.docs.data.Resource(type='video', title=os.path.basename(video_file_path))
        media = gdata.data.MediaSource()
        media.SetFileHandle(video_file_path, 'video/avi')
        doc = self.client.CreateResource(doc, media=media, collection=folder_resource)
        return doc
 
    def upload_video(self, video_file_path):
        """Upload a video to the specified folder. Then optionally send an email and optionally delete the local file."""
        folder_resource = self._get_folder_resource()
        if not folder_resource:
            raise Exception('Could not find the %s folder' % self.folder)
 
        doc = self._upload(video_file_path, folder_resource)
 
        if self.send_email:
            video_link = None
            for link in doc.link:
                if 'video.google.com' in link.href:
                    video_link = link.href
                    break
            # Send an email with the link if found
            msg = self.message
            if video_link:
                msg += 'nn' + video_link
            self._send_email(msg)
 
        if self.delete_after_upload:
            os.remove(video_file_path)
 
if __name__ == '__main__':
    try:
        if len(sys.argv) < 3:
            exit('Motion Uploader - uploads videos to Google Driven   by Jeremy Blythe (http://jeremyblythe.blogspot.com)nn   Usage: uploader.py {config-file-path} {video-file-path}')
        cfg_path = sys.argv[1]
        vid_path = sys.argv[2]
        if not os.path.exists(cfg_path):
            exit('Config file does not exist [%s]' % cfg_path)
        if not os.path.exists(vid_path):
            exit('Video file does not exist [%s]' % vid_path)
        MotionUploader(cfg_path).upload_video(vid_path)
    except gdata.client.BadAuthentication:
        exit('Invalid user credentials given.')
    except gdata.client.Error:
        exit('Login Error')
    except Exception as e:
        exit('Error: [%s]' % e)
