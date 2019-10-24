import myscript as script
import imaplib
import email
import os
from dateutil import parser
from datetime import datetime,timedelta
import re
import shelve
#user='immanuelebe30@gmail.com'
inbox=["INBOX",'"[Gmail]/Sent Mail"','"[Gmail]/Trash"']
indexname=['/index.txt','/sent.txt','/trash.txt']
def syncmail(user,shelf):
	os.makedirs(user,exist_ok=True)
	r_t=shelf[user][1]
	a_t,e=script.refresh_authorization(refresh_token=r_t)
	a_s=script.generate_oauth2_string(user,a_t)
	imap_conn = imaplib.IMAP4_SSL('imap.gmail.com')
	imap_conn.debug = 4
	imap_conn.authenticate('XOAUTH2', lambda x: a_s)
	imap_conn.list()
	for k in range(0,3):
		imap_conn.select(inbox[k])
		typ, data = imap_conn.search(None, 'SINCE 30-Apr-2019')
		i = len(data[0].split())
		index={}
		indexlist=[]	
		myfile = open(user+'/email.txt', 'a')
		for x in range(i):
			num=data[0].split()[x]
			typ, email_data = imap_conn.fetch(num, '(RFC822)')
			#print('Message %s\n%s\n' % (num, email_data[0][1]))
			raw_email=email_data[0][1]
			try:
				raw_email_string=raw_email.decode('utf-8')
				email_message=email.message_from_string(raw_email_string)
				for part in email_message.walk():
					if part.get_content_type() == "text/plain": # ignore attachments/html
					
						body = part.get_payload(decode=True)
						#save_string = str("D:Dumpgmailemail_" + str(x) + ".eml")
						# location on disk
						pos=myfile.tell()
						body=body.decode()
						#size=len(body)
						size=myfile.write(body+'$#$')
						date=parser.parse(email_message['date'])
						print(date)
						if k!=1:
							fadd=re.findall('<.+>',email_message['from'])
						else:
							fadd=re.findall('<.+>',email_message['to'])
						subject=email_message['subject']
						#subject=subject.lower()
						#if subject.lower().startswith('=?utf-8?'):
						subject=email.header.decode_header(subject)
						if type(subject[0][0])==type(''):
							subject=subject[0][0]
						else:
							subject=subject[0][0].decode()
						if subject=='':
							subject='No Subject'
						subject=subject.replace('\n',' ')
						print(subject)
						index[date]=str(pos)+'||'+str(size)+'||'+fadd[0]+'||'+subject.strip()
						indexlist.append(date)
						# body is again a byte literal
			except:pass
		indexfile=open(user+indexname[k],'w')
		indexlist.sort(reverse=True)
		for i in indexlist:
			indexfile.write(str(i)+'||'+index[i]+'\n')
		indexfile.close()
		myfile.close()
	imap_conn.shutdown()
