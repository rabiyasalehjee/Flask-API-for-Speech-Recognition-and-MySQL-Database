from pathlib import Path
from flask import Flask, render_template, request, jsonify, json,send_file, send_from_directory, safe_join, abort
import speech_recognition as speechr
import librosa 
import numpy as np
import math
from flask_mysqldb import MySQL
from datetime import date
#from werkzeug.datastructures import T
#from werkzeug.wrappers import response


app = Flask(__name__)

app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_DB'] = 'speach'
mysql = MySQL(app)

def getAudioData(Filename):
      print(Filename)
      recognizer = speechr.Recognizer()
      y, sr = librosa.load(Path( Filename ))
      #print(y, sr)
      Recordingduration=librosa.get_duration(y=y, sr=sr)
      Totaltext = ""
      PerMinuteWords = []
      audioFile = speechr.AudioFile(Filename)
      pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
      pi = np.arange(pitches.shape[1])
    #  print(np.average(pi))
      p = np.average(pitches, axis=0)
      pr = np.average(pitches, axis=1)


      pitch = np.average(p) + np.average(pr)
      duration = Recordingduration
      countMinutes = int(duration / 60)
      if countMinutes > 0:
            offse = 0
            end = 60
            for i in range(0,countMinutes):
                  with audioFile as source:
                        data = recognizer.record(source,offset=offse, duration = end)
                        text = recognizer.recognize_google(data, key=None)
                        Totaltext = Totaltext + ' ' +  text
                        PerMinuteWords.append(len(text.split())) 
                  offse = end
                  end += 60
            duration = int(duration-(end-60))
            with audioFile as source:
                  data = recognizer.record(source,offset=offse, duration = offse+duration)
                  text = recognizer.recognize_google(data, key=None)
                  Totaltext = Totaltext + ' '+  text 
                  PerMinuteWords.append(len(text.split()))

      else:
            with audioFile as source:
                  data = recognizer.record(source,offset=0, duration = duration)
                  text = recognizer.recognize_google(data, key=None)
                  Totaltext = text
                  roundedDuration = math.ceil(duration)
                  multiplier = len(text.split()) / roundedDuration 
                  noOfWordsInMint = math.ceil( multiplier * 60 )
                  PerMinuteWords.append(noOfWordsInMint)
          


      return { "text":Totaltext,"pace":np.average(PerMinuteWords),"TotalNumberOfWords": len(Totaltext.split()),"Recordingduration":Recordingduration,"Pitch":np.average(pitch) }  
 
def insertFileInDB(userid, fileroute, filter, topic, fileforDB):
      query = 'INSERT INTO `speaches`(`file`, `time`, `words`, `pace`, `filter`, `pitch`, `speach`, `topic`, `date`, `UserID`, `showToTeacher`, `assign_id`) VALUES (%s, %s,%s, %s,%s, %s,%s, %s, %s, %s, %s, %s)'
     
      audioFile = getAudioData(fileroute)
      val = ([fileforDB], [audioFile["Recordingduration"]], [audioFile["TotalNumberOfWords"]], [audioFile["pace"]], [str(filter)], [audioFile["Pitch"]], [audioFile["text"]], [topic], [date.today()], [userid], False, 0)
      
      cur = mysql.connection.cursor()
      cur.execute(query, val)
      mysql.connection.commit()
      cur.close()

def insertAnswer(questionid,userid,audioid):
     
      query = 'INSERT INTO `interview_record`(`speech_id`, `user_id`, `quest_id`) VALUES (%s, %s, %s)'

      val = ([audioid],[userid],  [questionid] )
      
      cur = mysql.connection.cursor()
      cur.execute(query, val)
      mysql.connection.commit()
      cur.close()

def insertTopicInDB(topicid, userid, audioid):
     
      query = 'INSERT INTO `exercises`(`exercise_id`, `user_id`, `speech_id`) VALUES (%s, %s, %s)'

      val = ([topicid], [userid], [audioid] )
      
      cur = mysql.connection.cursor()
      cur.execute(query, val)
      mysql.connection.commit()
      cur.close()

def readandSaveFile():
      return jsonify(text = 'fileuploaded Successfuller')

def write_file(data, filename):
      
    with open(filename, 'wb') as file:
        file.write(data)

@app.route('/uploadFile', methods = ['GET', 'POST'])
def upload_file():
   
   if request.method == 'POST':
      f = request.files['file']
     # f1 = request.files['file1']
      filePath = "Recordings/" + str(f.filename)
      #filePath1 = "Recordings/wav/" + str(f1.filename)
      userID =  request.form["userID"]
      filefilter =  request.form["filter"]
      filetopic =  request.form["topic"]
      f.save(filePath)
     # f1.save(filePath1)
      
      insertFileInDB(userID, filePath,filefilter,filetopic, str(f.filename))
      
      return jsonify(text = 'fileuploaded Successfuller')

@app.route('/getUsers', methods = ['GET', 'POST'])
def getUsers():
         
      users = []
      cur = mysql.connection.cursor()
      cur.execute("SELECT * FROM users")
      data = cur.fetchall()      
      
      for row in data:
            users.append({"id":row[0],"name":row[1],"email":row[2],"password":row[3],"phone":row[4],"date":row[5],"role":row[6],"token":row[7]})
      
      mysql.connection.commit()
      cur.close()
      return jsonify(respone = users)

@app.route('/allinterviewquestions', methods = ['GET', 'POST'])
def allinterviewquestions():
      questions = []
      cur = mysql.connection.cursor()
      cur.execute("SELECT * FROM `interview_questions`")
      data = cur.fetchall()      
      
      for row in data:
            questions.append({"quest_id":row[0],"question":row[1],"Category":row[2],"suggested_answer":row[3],"instruction":row[4]})
      
      mysql.connection.commit()
      cur.close()
      return jsonify(respone = questions)

@app.route('/getFile', methods = ['GET', 'POST'])
def getFile():

      if 'filename' in request.args:
            filenaaaam = str(request.args['filename'])

      try:
        return send_from_directory("Recordings/", path= filenaaaam, as_attachment=True)
      except FileNotFoundError:
        abort(404)

@app.route('/getFileDetailsByUserID', methods = ['GET', 'POST'])
def getFileDetailsByUserID():
         
         
      speeches = []
      cur = mysql.connection.cursor()
              
      if 'userID' in request.args:
            userID = int(request.args['userID'])
      
      cur.execute("SELECT * FROM speaches where UserID = {0}".format(userID))
      data = cur.fetchall()      
      

      for row in data:
            fileRoute = "/getFile?filename=" + str(row[1])
            speeches.append({"ID":row[0],"fileName":str(row[1]),"fileRoute":fileRoute,"duration":row[2],"NoOFTotalWords":row[3],"pace":row[4],"filter":row[5],"pitch":row[6],"speechText":row[7],"topic":row[8],"date":row[9],"UserID":row[10] })
            #speeches.append({"id":row[0],"fileRoute":row[1],"words":row[2],"pace":row[3],"time":row[4],"filter":row[5],"pitch":row[6],"speach":row[7],"date":row[9] })
      
      mysql.connection.commit()
      cur.close()
      
      return jsonify(respone = speeches)

@app.route('/uploadanswer', methods = ['GET', 'POST'])
def uploadanswer():
     # questionIDs = []
      # try:
      #        except FileNotFoundError:
      #       return jsonify(respone = 'something went wrong')
      if request.method == 'POST':
            f = request.files['file']
            questionID = str(request.form['questionIDs']) #QUESTION ID STRING CONCATINATED WITH ',' 
            userID =  int(request.form["userID"])
            filefilter = str(request.form["filter"]) #just send empty string
            filetopic = str(request.form["topic"])   #just send empty string
      filePath = "Recordings/" + str(f.filename)
      questionIDs = questionID.split(',')
      f.save(filePath)

      insertFileInDB(userID, filePath, filefilter, filetopic, str(f.filename))

      print(questionIDs)

      cur = mysql.connection.cursor()
      cur.execute("SELECT MAX(id) FROM `speaches`")
      data = cur.fetchall()   
      audioFileID = data[0][0]


      for id in questionIDs:
            insertAnswer(id, userID, audioFileID)
                  #questions.append({"quest_id ":row[0],"question":row[1],"Category":row[2],"suggested_answer":row[3],"instruction":row[4]})
            
      return jsonify(respone = 'answer submitted successfully')

@app.route('/uploadtopic', methods = ['GET', 'POST'])
def uploadtopic():
      # questionIDs = []
      # try:
      #        except FileNotFoundError:
      #       return jsonify(respone = 'something went wrong')
      if request.method == 'POST':
            f = request.files['file']
            topicID = int(request.form["topicID"]) #QUESTION ID STRING CONCATINATED WITH ',' 
            userID =  int(request.form["userID"])
            filefilter = str(request.form["filter"]) #just send empty string
            filetopic = str(request.form["topic"])   #just send empty string
      filePath = "Recordings/" + str(f.filename)
      
      f.save(filePath)

      insertFileInDB(userID, filePath, filefilter, filetopic, str(f.filename))

      cur = mysql.connection.cursor()
      cur.execute("SELECT MAX(id) FROM `speaches`")
      data = cur.fetchall()   
      audioFileID = data[0][0]

      insertTopicInDB(topicID, userID, audioFileID)
      
      return jsonify(respone = 'ypic ')

@app.route('/getmaxid', methods = ['GET', 'POST'])
def getmaxid():
      cur = mysql.connection.cursor()
      cur.execute("SELECT MAX(id) FROM `speaches`")
      data = cur.fetchall()   
      audioFileID = data[0][0]
      return jsonify(respone = audioFileID)

@app.route('/getAllTopics', methods = ['GET', 'POST'])
def getAllTopics():
              
      topics = []
      cur = mysql.connection.cursor()
              
      
      cur.execute("SELECT * FROM `flip_card_exercise`")
      data = cur.fetchall()      
      

      for row in data:
            topicFileName = "topic_{0}_img.PNG".format(int(row[0]))
            topicHintFileName = "topicHint_{0}_img.PNG".format(int(row[0]))
            
            topicfileRoute = "/getTopicFiles?filename={0}".format(topicFileName)
            topicHintfileRoute = "/getTopicFiles?filename={0}".format(topicHintFileName)
            
            topics.append({"ID":row[0], "topicfileRoute": topicfileRoute, "topicHintfileRoute": topicHintfileRoute })
            
            my_topicfile = Path("Topics/{0}".format(topicFileName))
            my_hintfile  = Path("Topics/{0}".format(topicHintFileName))
                  
            if my_topicfile.is_file() == False:
                  write_file(row[1],my_topicfile)

            if my_hintfile.is_file() == False:
                   write_file(row[2],my_hintfile)
 
      
      mysql.connection.commit()
      cur.close()
      
      return jsonify(respone = topics)

@app.route('/getTopicFiles', methods = ['GET', 'POST'])
def getTopicFiles():
     
      if 'filename' in request.args:
            filenaaaam = str(request.args['filename'])

      try:
        return send_from_directory("Topics/", path= filenaaaam, as_attachment=False)
      except FileNotFoundError:
        abort(404)

@app.route('/getAllTopicSpeeches', methods = ['GET', 'POST'])
def getAllTopicSpeeches():
              
      speeches = []
      cur = mysql.connection.cursor()
              
      if 'userID' in request.args:
            userID = int(request.args['userID'])
      
      cur.execute("SELECT * FROM `speaches` where id in (select `speech_id` from `exercises` where UserID = {0})".format(userID))
      data = cur.fetchall()      
      

      for row in data:
            fileRoute = "/getFile?filename=" + str(row[1])
            speeches.append({"ID":row[0],"fileName":str(row[1]),"fileRoute":fileRoute,"duration":row[2],"NoOFTotalWords":row[3],"pace":row[4],"filter":row[5],"pitch":row[6],"speechText":row[7],"topic":row[8],"date":row[9],"UserID":row[10] })
            #speeches.append({"id":row[0],"fileRoute":row[1],"words":row[2],"pace":row[3],"time":row[4],"filter":row[5],"pitch":row[6],"speach":row[7],"date":row[9] })
      
      mysql.connection.commit()
      cur.close()
      
      return jsonify(respone = speeches)

@app.route('/getAllInterviewSpeeches', methods = ['GET', 'POST'])
def getAllInterviewSpeeches():
              
      speeches = []
      cur = mysql.connection.cursor()
              
      if 'userID' in request.args:
            userID = int(request.args['userID'])
      
      
      
      cur.execute("SELECT * FROM `speaches` where id in (select DISTINCT `speech_id` from `interview_record` where user_id = {0})".format(userID))
      data = cur.fetchall()      
      

      for row in data:
            fileRoute = "/getFile?filename=" + str(row[1])
            speeches.append({"ID":row[0],"fileName":str(row[1]),"fileRoute":fileRoute,"duration":row[2],"NoOFTotalWords":row[3],"pace":row[4],"filter":row[5],"pitch":row[6],"speechText":row[7],"topic":row[8],"date":row[9],"UserID":row[10] })
            #speeches.append({"id":row[0],"fileRoute":row[1],"words":row[2],"pace":row[3],"time":row[4],"filter":row[5],"pitch":row[6],"speach":row[7],"date":row[9] })
      
      mysql.connection.commit()
      cur.close()
      
      return jsonify(respone = speeches)

@app.route('/getSpeeches', methods = ['GET', 'POST'])
def getSpeeches():
              
      allSpeeches = []
      topicsSpeeches = []
      interviewSpeeches = []
      cur = mysql.connection.cursor()
              
      if 'userID' in request.args:
            userID = int(request.args['userID'])
      
      #topics
      cur.execute("SELECT * FROM `speaches` where id not in (select `speech_id` from `exercises` where user_id = {0}) and id not in (select DISTINCT `speech_id` from `interview_record` where user_id = {0}) and `UserID` = {0} order by id desc ".format(userID))
      data1 = cur.fetchall()      
      
      #exercises
      cur.execute("SELECT * FROM `speaches` where id in (select `speech_id` from `exercises` where user_id = {0}) order by id desc".format(userID))
      data2 = cur.fetchall()      
       
      #interview
      cur.execute("SELECT * FROM `speaches` where id in (select DISTINCT `speech_id` from `interview_record` where user_id = {0}) order by id desc".format(userID))
      data3 = cur.fetchall()    

      for row in data1:
            fileRoute = "/getFile?filename=" + str(row[1])
            allSpeeches.append({"ID":row[0],"fileName":str(row[1]),"fileRoute":fileRoute,"duration":row[2],"NoOFTotalWords":row[3],"pace":row[4],"filter":row[5],"pitch":row[6],"speechText":row[7],"topic":row[8],"date":row[9],"UserID":row[10],"showToTeacher": bool(row[11]), "assign_id": row[12] })
            #speeches.append({"id":row[0],"fileRoute":row[1],"words":row[2],"pace":row[3],"time":row[4],"filter":row[5],"pitch":row[6],"speach":row[7],"date":row[9] }) 
      

      for row in data2:
            fileRoute = "/getFile?filename=" + str(row[1])
            topicsSpeeches.append({"ID":row[0],"fileName":str(row[1]),"fileRoute":fileRoute,"duration":row[2],"NoOFTotalWords":row[3],"pace":row[4],"filter":row[5],"pitch":row[6],"speechText":row[7],"topic":row[8],"date":row[9],"UserID":row[10],"showToTeacher": bool(row[11]), "assign_id": row[12]  })
            #speeches.append({"id":row[0],"fileRoute":row[1],"words":row[2],"pace":row[3],"time":row[4],"filter":row[5],"pitch":row[6],"speach":row[7],"date":row[9] })
      
      
      for row in data3:
            fileRoute = "/getFile?filename=" + str(row[1])
            interviewSpeeches.append({"ID":row[0],"fileName":str(row[1]),"fileRoute":fileRoute,"duration":row[2],"NoOFTotalWords":row[3],"pace":row[4],"filter":row[5],"pitch":row[6],"speechText":row[7],"topic":row[8],"date":row[9],"UserID":row[10],"showToTeacher": bool(row[11]), "assign_id": row[12]  })
            #speeches.append({"id":row[0],"fileRoute":row[1],"words":row[2],"pace":row[3],"time":row[4],"filter":row[5],"pitch":row[6],"speach":row[7],"date":row[9] })

      mysql.connection.commit()
      cur.close()
      
      return jsonify(respone = { "allSpeeches": allSpeeches,"topicsSpeeches": topicsSpeeches,"interviewSpeeches": interviewSpeeches  })

@app.route('/getUserByID', methods = ['GET', 'POST'])
def getUserByID():
      cur = mysql.connection.cursor()
              
      if 'userID' in request.args:
            userID = int(request.args['userID'])
      
      cur.execute("SELECT * FROM `users` where id = {0} ".format(userID))
      data = cur.fetchall()
      
      row = data[0]
 
      return jsonify(respone = {"id":row[0],"name":row[1],"email":row[2],"password":row[3],"phone":row[4],"date":row[5],"role":row[6],"token":row[7]})

@app.route('/updatePassword', methods = ['GET', 'POST'])
def updatePassword():
                 
      cur = mysql.connection.cursor()
              
      if 'userID' in request.args:
            userID = int(request.args['userID'])
      
      if 'name' in request.args:
            name = str(request.args['name'])
            
      if 'password' in request.args:
            psswrd = str(request.args['password'])

      if 'contact' in request.args:
            cntct = str(request.args['contact'])
      
      query = "update users set `name` = '{0}', `password` = '{1}', `phone` = '{2}' where `id`= '{3}'".format(name, psswrd, cntct, userID)
      print(query)
      cur.execute(query)
      mysql.connection.commit()
      cur.close()
      return jsonify(respone = bool(True))

@app.route('/deleteFileByTypeAndID', methods = ['GET', 'POST'])
def deleteFileByTypeAndID():
               
      cur = mysql.connection.cursor()
              
      if 'fileID' in request.args:
            fileID = str(request.args['fileID'])
      
      if 'type' in request.args:
            type = str(request.args['type']) 
      
      query = "DELETE FROM `speaches` WHERE id = '{0}'".format(fileID)
      print(query)
      cur.execute(query)
      mysql.connection.commit()
      cur.close()
      
      return jsonify(respone = bool(True))
 
@app.route('/login', methods = ['GET', 'POST'])
def login():
               
              
      if 'email' in request.args:
            email = str(request.args['email'])
      
      if 'password' in request.args:
            passsword = str(request.args['password']) 
      
      cur = mysql.connection.cursor()
      query = "SELECT * FROM `users` WHERE `email` = '{0}' AND `password` = '{1}';".format(email, passsword)
      print(query)
      cur.execute(query)
      data = cur.fetchall()  
      mysql.connection.commit()
      cur.close() 
            
      try:
            return jsonify(respone = {'responseMsg': 'logged in successussfully', 'id' :  data[0][0], 'name' :  data[0][1], 'email' :  data[0][2], 'password' :  data[0][3], 'phone' :  data[0][4], 'date' :  data[0][5], 'role' :  data[0][6], 'token' :  data[0][7]  })  
      except Exception:
            return jsonify(respone = { 'responseMsg': 'invalid username or passwrord' })  

@app.route('/signup', methods = ['GET', 'POST'])
def signup():
               
      cur = mysql.connection.cursor()
              
      if 'name' in request.args:
            name = str(request.args['name'])
                    
      if 'email' in request.args:
            email = str(request.args['email'])
                                
      if 'password' in request.args:
            password = str(request.args['password'])
                                
      if 'phone' in request.args:
            phone = str(request.args['phone'])
                                
      
      today = date.today()
      d1 = today.strftime("%d/%m/%Y")                
      
      query = 'INSERT INTO `users`(`name`, `email`, `password`, `phone`, `date`, `role`, `token`) VALUES (%s, %s, %s, %s, %s, %s, %s)'
      val = ([name], [email], [password], [phone], [d1], '', '')

      cur = mysql.connection.cursor()
      cur.execute(query, val)
      mysql.connection.commit()
      cur.close()
      
      return jsonify(respone = bool(True))

@app.route('/updateshowToTeacherByID', methods = ['GET', 'POST'])
def updateshowToTeacherByID():
      cur = mysql.connection.cursor()
                          
      if 'fileID' in request.args:
            fileID = str(request.args['fileID'])
                     
     
      qeury = 'update `speaches` set `showToTeacher` = not `showToTeacher` where id = {0};'.format( fileID )

      cur.execute(qeury)
      mysql.connection.commit()
      cur.close()       

      return jsonify(respone = bool(True))


@app.route('/getAllAssignments', methods = ['GET', 'POST'])
def getAllAssignments():
      cur = mysql.connection.cursor()

      assignments = []

      query = 'SELECT * FROM `student_assignment`'
      cur.execute(query)
      data1 = cur.fetchall()      
     
      for row in data1:
            assignments.append({ 'ID': row[0], 'Name': row[1], 'Subject': row[2], 'Code': row[3], 'TeacherID': row[4] })
      mysql.connection.commit()
      cur.close()       

      return jsonify(respone =  assignments )
     # return jsonify(respone = { 'Assignments': assignments } )

@app.route('/updateAssignmentBySpeechID', methods = ['GET', 'POST'])
def updateAssignmentBySpeechID():
      cur = mysql.connection.cursor()
    
      if 'fileID' in request.args:
            fileID = str(request.args['fileID'])
      
      if 'assignmentID' in request.args:
            assignmentID = str(request.args['assignmentID'])
                     
      query = 'update `speaches` set `assign_id` = {0} where id = {1}'.format( assignmentID, fileID )
      
      cur.execute(query)
      mysql.connection.commit()
      cur.close()       

      return jsonify(respone = bool(True))


if __name__=="__main__":
      app.run(host='0.0.0.0', debug=True, threaded=True)
      
	