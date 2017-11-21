#!/usr/bin/python3

# written by Mingkai Ma October 2017
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os
from flask import Flask, render_template, session, request
from collections import defaultdict
from shutil import copyfile, rmtree
import re, collections
import datetime
import fileinput
import subprocess

students_dir = "static/dataset-medium";

app = Flask(__name__)

#Show unformatted details for student "n".
# Increment  n and store it in the session cookie

@app.route('/', methods=['GET','POST'])
@app.route('/start', methods=['GET','POST'])
def start():
    n = session.get('n', 0)
    students = sorted(os.listdir(students_dir))
    student_to_show = students[n % len(students)]
    details_filename = os.path.join(students_dir, student_to_show, "student.txt")
    student_details = read_student_details()
    student_posts = read_student_post(student_to_show)
        
    img_original_src = os.path.join(students_dir, student_to_show, "img.jpg")
    if(os.path.exists(img_original_src)):
      
        img_src = '/'.join(img_original_src.split('/')[1:])
    else:
        img_src = 0
        

		
    session['n'] = n + 1
    return render_template('start.html', student_details=student_details,
                           img_src=img_src, zid=student_to_show,
                           student_post = student_posts)



# start_login
@app.route('/start_login', methods=['GET', 'POST'])
def start_login():
    return render_template('login.html')

# login
@app.route('/login', methods=['POST'])
def login():

    
    submit_type = request.form.get('action')
    zid = request.form.get('username')
    password = request.form.get('password')

    

    if submit_type == "Sign Up":
        return render_template('signup.html')
    elif submit_type == 'Forgot':
        return render_template('password_recovery.html')

    student_details = read_student_details()

    
    if submit_type == "Login" or submit_type == "home":
        if zid not in student_details:
            return render_template('login.html', message="Unknown username, you need to sign up")
        elif (student_details[zid]['password'] != password):
           
            return render_template('login.html', message='wrong password')
        else:
            session['zid'] = zid
           
            student_details = read_student_details()
            student_posts = read_student_post(zid)
            student_comments = read_student_comment(zid)
            student_replys = read_student_reply(zid)                         
            surname = student_details[zid]['full_name'].split()[0]
            to_print_post, postcomment, postcommentreply = get_post_comment_reply(zid)
            course_session_dic = get_course_session_dic()
            likely_friend_list = []
            for course_session in course_session_dic:
                if zid in course_session_dic[course_session]:
                    if len(course_session_dic[course_session]) != 1:
                        likely_friend_list = course_session_dic[course_session]
                        break

            temp_list = []
            for stu in likely_friend_list:
                if stu == zid:
                    continue
                if stu in student_details[zid]['friends']:
                    continue

                temp_list.append(stu)
                

            likely_friend_list = temp_list
     
            return render_template('homepage.html', student_details = student_details,
                                                    student_post = student_posts,
                                                    student_comment = student_comments,
                                                    student_reply = student_replys,
                                                    zid = zid, surname = surname,
                                                    to_print_post = to_print_post,
                                                    postcomment = postcomment,
                                                    postcommentreply = postcommentreply,
                                                    likely_friend_list = likely_friend_list[:10])

    elif submit_type == "Log out":
        return render_template('login.html')
            
    return "hello world"

# password recovery
@app.route('/password_recovery', methods=['GET', 'POST'])
def password_recovery():
    student_details = read_student_details()
    reset_zid = 0
    reset_password = ''
    if request.method == 'POST':
        reset_zid = request.form.get('username')
        if reset_zid not in student_details:
            return render_template('password_recovery.html', error="Unknown username, you need to sign up first.")
        reset_password = request.form.get('password')
        reset_dic[reset_zid] = reset_password

        reset_password_filename = os.path.join(students_dir, reset_zid, "reset.txt")
        with open(reset_password_filename, 'w') as file:
            file.write(reset_password)
            

        send_email(student_details[reset_zid]['email'], 'UNSWtalk_Password_Recovery',  'click this link  https://cgi.cse.unsw.edu.au/~z5135897/ass2/UNSWtalk.cgi/password_recovery?reset_zid=' + reset_zid + ' to reset your password ')


        return render_template('password_email_sent.html')
    

    if request.method == 'GET':
        reset_zid = request.args.get('reset_zid')
        
        reset_password_filename = os.path.join(students_dir, reset_zid, "reset.txt")
        with open(reset_password_filename) as file:
            reset_password = file.read()
            
        
        details_filename = os.path.join(students_dir, reset_zid, "student.txt")

        for line in fileinput.input(details_filename, inplace=True):
            line = line.strip('\n')
            if 'password' in line:
                s = line.split(':')
                s[1] = reset_password
                line = 'password: ' + s[1]
                print(line)

            else:
                print(line)

        return render_template('reset_successfully.html')
        return 'You have successfully reset your password.'
        
        




# process profile
@app.route('/profile', methods=['POST','GET'])
def profile():

    if request.method == 'POST':
        submit_type = request.form.get('action')
        

        if(submit_type == 'Intro myself'):
           
            bio_content = request.form.get('bio_content')
            bio_zid = request.form.get('bio_zid')
            details_filename = os.path.join(students_dir, bio_zid, "student.txt")
            with open(details_filename, 'a') as file:
                file.write('bio: ' + bio_content + '\n')
            student_details = read_student_details()
            return render_template('profile.html', student_details = student_details, zid = bio_zid)

        if(submit_type == 'unfriend'):
            unfriend_name = request.form.get('friend_name')
            who_unfriend_zid = request.form.get('who_unfriend')
            
            details_filename = os.path.join(students_dir, who_unfriend_zid, "student.txt")
            for line in fileinput.input(details_filename, inplace=True):
                line = line.strip('\n')
                if 'friends' in line:
                    s = line.split(':')
                    s[1] = re.sub(r'^\s*\(','', s[1])
                    s[1] = re.sub(r'\)\s*$','', s[1])
                    s[1] = s[1].split(',')
                    s[1] = [i.strip() for i in s[1]]
                    s[1].remove(unfriend_name)
                    new_line = ','.join(s[1])
                    line = 'friends: (' + new_line + ')'
                    print(line)

                else:
                    print(line)
                    
            student_details = read_student_details()
    
            return render_template('profile.html', student_details = student_details, zid=who_unfriend_zid)


    if request.method == 'GET':
        pro_zid = request.args.get('pro_zid')
        print('hereafdsf', pro_zid)
        student_details = read_student_details()
        return render_template('profile.html', student_details = student_details, zid=pro_zid)
        
# public personal page
@app.route('/page')
def page():
    home_zid = request.args.get('home_zid')
    look_for_zid = request.args.get('user')
    
    student_details = read_student_details()

    return render_template('page.html', student_details=student_details, home_zid = home_zid, look_for_zid=look_for_zid)
    



# search friend
@app.route('/search', methods=['POST'])
def search():
    search_input = request.form.get('search_input')
    searcher_zid = request.form.get('searcher_zid')
    student_details = read_student_details()
    search_result_list = []
    for student_zid in student_details:

        m = re.search(search_input, student_details[student_zid]['full_name'], re.IGNORECASE)
        if m:
            search_result_list.append(student_zid)

    return render_template('search.html', student_details = student_details,
                                           search_result_list = search_result_list,
                                           zid = searcher_zid)
            
# search post
@app.route('/search_post', methods=['POST'])
def search_post():
    if 'zid' not in session:
        return render_template('login.html')

    zid = session['zid']


    search_post_content = request.form.get('search_post_content')
    search_post_content = repr(search_post_content)
    search_post_content = search_post_content.replace('\\r','')
    search_post_content = search_post_content.replace('\\xa0','')
    search_post_content = search_post_content.strip("'")
    search_post_content = search_post_content.strip('"')


    to_print_post, postcomment, postcommentreply = get_search_post_comment_reply(zid, search_post_content)
    student_details = read_student_details()
    student_posts = read_student_post(zid)
    student_comments = read_student_comment(zid)
    student_replys = read_student_reply(zid)
    surname = student_details[zid]['full_name'].split()[0]
    return render_template('search_post.html', student_details = student_details,
                                            student_post = student_posts,
                                            student_comment = student_comments,
                                            student_reply = student_replys,
                                            zid = zid, surname = surname,
                                            to_print_post = to_print_post,
                                            postcomment = postcomment,
                                            postcommentreply = postcommentreply,
                                            search_post_content = search_post_content)


# homepage. display post comment reply, make post, comment, reply

@app.route('/homepage', methods=['POST'])
def homepage():


    if (request.form.get('post_content') != None):
        zid = request.form.get('home_zid')
        post_content = request.form.get('post_content')
        post_content = repr(post_content)
        post_content = post_content.replace('\\r','')
        post_content = post_content.replace('\\xa0','')
        post_content = post_content.strip("'")
        post_content = post_content.strip('"')
        
        student_posts = read_student_post(zid)
        post_to_save_filename = str(len(student_posts[zid])) + '.txt'
        post_to_save = os.path.join(students_dir, zid, post_to_save_filename)

        with open(post_to_save, 'a') as f:
            f.write('time: ' + get_time() + '\n')
            f.write('from: ' + zid + '\n')
            f.write('message: ' + post_content + '\n')
            f.write('latitude: -33.9190' + '\n')
            f.write('longitude: 151.2278' + '\n')



        to_print_post, postcomment, postcommentreply = get_post_comment_reply(zid)
        student_details = read_student_details()
        student_posts = read_student_post(zid)
        student_comments = read_student_comment(zid)
        student_replys = read_student_reply(zid)
        surname = student_details[zid]['full_name'].split()[0]
        return render_template('homepage.html', student_details = student_details,
                                                student_post = student_posts,
                                                student_comment = student_comments,
                                                student_reply = student_replys,
                                                zid = zid, surname = surname,
                                                to_print_post = to_print_post,
                                                postcomment = postcomment,
                                                postcommentreply = postcommentreply)

    elif (request.form.get('comment_content') != None):
        zid = request.form.get('home_zid')
        comment_content = request.form.get('comment_content')
        comment_content = repr(comment_content)
        comment_content = comment_content.replace('\\r','')
        comment_content = comment_content.replace('\\xa0','')
        comment_content = comment_content.strip("'")
        comment_content = comment_content.strip('"')
        temp_zid = request.form.get('poster_zid')
        temp_post_nb = request.form.get('post_nb')

        i = 0
        while True:

            temp_comment = os.path.join(students_dir, temp_zid, temp_post_nb + '-' + str(i) + '.txt')
            print(temp_comment)
            if (os.path.isfile(temp_comment)):
                i += 1
                continue
            else:
                comment_to_save = os.path.join(students_dir, temp_zid, temp_post_nb + '-' + str(i) + '.txt')
                break

        with open(comment_to_save, 'a') as f:
            f.write('time: ' + get_time() + '\n')
            f.write('from: ' + zid + '\n')
            f.write('message: ' + comment_content + '\n')

        to_print_post, postcomment, postcommentreply = get_post_comment_reply(zid)
        student_details = read_student_details()
        student_posts = read_student_post(zid)
        student_comments = read_student_comment(zid)
        student_replys = read_student_reply(zid)
        surname = student_details[zid]['full_name'].split()[0]
        return render_template('homepage.html', student_details = student_details,
                                                student_post = student_posts,
                                                student_comment = student_comments,
                                                student_reply = student_replys,
                                                zid = zid, surname = surname,
                                                to_print_post = to_print_post,
                                                postcomment = postcomment,
                                                postcommentreply = postcommentreply)


    elif (request.form.get('reply_content') != None):
        zid = request.form.get('home_zid')
        reply_content = request.form.get('reply_content')
        reply_content = repr(reply_content)
        reply_content = reply_content.replace('\\r','')
        reply_content = reply_content.replace('\\xa0','')
        reply_content = reply_content.strip("'")
        reply_content = reply_content.strip('"')
        temp_zid = request.form.get('poster_zid')
        temp_post_nb = request.form.get('post_nb')
        temp_comment_nb = request.form.get('comment_nb')

        i = 0
        while True:
            temp_reply = os.path.join(students_dir, temp_zid, temp_post_nb + '-' + temp_comment_nb + '-' + str(i) + '.txt')
            if(os.path.isfile(temp_reply)):
                i += 1
                continue
            else:
                reply_to_save = os.path.join(students_dir, temp_zid, temp_post_nb + '-' + temp_comment_nb + '-' + str(i) + '.txt')
                break

        with open(reply_to_save, 'a') as f:
            f.write('time: ' + get_time() + '\n')
            f.write('from: ' + zid + '\n')
            f.write('message: ' + reply_content + '\n')
        
        to_print_post, postcomment, postcommentreply = get_post_comment_reply(zid)
        student_details = read_student_details()
        student_posts = read_student_post(zid)
        student_comments = read_student_comment(zid)
        student_replys = read_student_reply(zid)
        surname = student_details[zid]['full_name'].split()[0]
        return render_template('homepage.html', student_details = student_details,
                                                student_post = student_posts,
                                                student_comment = student_comments,
                                                student_reply = student_replys,
                                                zid = zid, surname = surname,
                                                to_print_post = to_print_post,
                                                postcomment = postcomment,
                                                postcommentreply = postcommentreply)

    elif (request.form.get('delete_submit') != None):
        zid = request.form.get('home_zid')
        poster_zid  =request.form.get('poster_zid')
     
        post_nb = request.form.get('post_nb')
        student_file = sorted(os.listdir(students_dir + '/' + poster_zid))
        for file in student_file:

            regex = re.compile('^{}.*\.txt$'.format(post_nb))
            m = regex.match(file)
            if m:
              
                remove_file = os.path.join(students_dir, poster_zid, file)
          
                os.remove(remove_file)

        
        to_print_post, postcomment, postcommentreply = get_post_comment_reply(zid)
        student_details = read_student_details()
        student_posts = read_student_post(zid)
        student_comments = read_student_comment(zid)
        student_replys = read_student_reply(zid)
        surname = student_details[zid]['full_name'].split()[0]
        return render_template('homepage.html', student_details = student_details,
                                                student_post = student_posts,
                                                student_comment = student_comments,
                                                student_reply = student_replys,
                                                zid = zid, surname = surname,
                                                to_print_post = to_print_post,
                                                postcomment = postcomment,
                                                postcommentreply = postcommentreply)

    elif (request.form.get('delete_comment') != None):
        zid = request.form.get('home_zid')
        poster_zid = request.form.get('poster_zid')
        post_nb = request.form.get('post_nb')
        comment_nb = request.form.get('comment_nb')
        student_file = sorted(os.listdir(students_dir + '/' + poster_zid))
        for file in student_file:
            regex = re.compile('^{}\-{}(\-[0-9]+)?\.txt\s*$'.format(post_nb, comment_nb))
            m = regex.match(file)
            if m:
                
                remove_file = os.path.join(students_dir, poster_zid, file)

                os.remove(remove_file)


        to_print_post, postcomment, postcommentreply = get_post_comment_reply(zid)
        student_details = read_student_details()
        student_posts = read_student_post(zid)
        student_comments = read_student_comment(zid)
        student_replys = read_student_reply(zid)
        surname = student_details[zid]['full_name'].split()[0]
        return render_template('homepage.html', student_details = student_details,
                                                student_post = student_posts,
                                                student_comment = student_comments,
                                                student_reply = student_replys,
                                                zid = zid, surname = surname,
                                                to_print_post = to_print_post,
                                                postcomment = postcomment,
                                                postcommentreply = postcommentreply)




    elif (request.form.get('delete_reply') != None):
        zid = request.form.get('home_zid')
        poster_zid = request.form.get('poster_zid')
        post_nb = request.form.get('post_nb')
        comment_nb = request.form.get('comment_nb')
        reply_nb = request.form.get('reply_nb')
        student_file = sorted(os.listdir(students_dir + '/' + poster_zid))
        for file in student_file:
            temp_file = '{}-{}-{}.txt'.format(post_nb, comment_nb, reply_nb)
            if file == temp_file:
                
                remove_file = os.path.join(students_dir, poster_zid, file)

                os.remove(remove_file)

        to_print_post, postcomment, postcommentreply = get_post_comment_reply(zid)
        student_details = read_student_details()
        student_posts = read_student_post(zid)
        student_comments = read_student_comment(zid)
        student_replys = read_student_reply(zid)
        surname = student_details[zid]['full_name'].split()[0]
        return render_template('homepage.html', student_details = student_details,
                                                student_post = student_posts,
                                                student_comment = student_comments,
                                                student_reply = student_replys,
                                                zid = zid, surname = surname,
                                                to_print_post = to_print_post,
                                                postcomment = postcomment,
                                                postcommentreply = postcommentreply)





# signup

@app.route('/signup', methods=['POST'])
def signup():

    signup_zid = request.form.get('username')
    signup_password = request.form.get('password')
    signup_email = request.form.get('email')
    signup_fullname = request.form.get('full_name')
    signup_birthday = request.form.get('birthday')
    signup_home_suburb = request.form.get('home_suburb')
    signup_program = request.form.get('program')
    signup_course = request.form.get('course')

    student_details = read_student_details()

    if signup_zid in student_details:
        return render_template('signup.html', zid_error='zid exists.')

    valid_email = re.compile(r'^[\S]+@[\S]+\.[\S]+$')

    if not valid_email.match(signup_email):
        return render_template('signup.html', email_error='invalid email')

    signup_directory = students_dir + '/' + 'signup'

    if not os.path.isdir(signup_directory):
        os.makedirs(signup_directory)

    detail_filename = os.path.join(students_dir, 'signup', signup_zid + '.txt')

    with open(detail_filename, 'w') as file:
        file.write('zid: ' + signup_zid + '\n')
        file.write('password: ' + signup_password + '\n')
        file.write('email: ' + signup_email + '\n')
        file.write('full_name: ' + signup_fullname + '\n')
        file.write('birthday: ' + signup_birthday + '\n')
        file.write('home_suburb: ' + signup_home_suburb + '\n')
        file.write('program: ' + signup_program + '\n')
        file.write('courses: (' + signup_course + ')\n')




    send_email(signup_email, 'UNSWtalk Sign Up', 'click here to response: https://cgi.cse.unsw.edu.au/~z5135897/ass2/UNSWtalk.cgi/signup_link?user=' + signup_zid)
    
    return render_template('signup_finish.html')


# process sign up link clicked in email

@app.route('/signup_link')
def signup_link():
    new_zid = request.args.get('user')
   

    new_directory = students_dir + '/' + new_zid
    os.makedirs(new_directory)

    signup_detail_filename = os.path.join(students_dir, 'signup', new_zid + '.txt')
    
    detail_filename = os.path.join(students_dir, new_zid, 'student.txt')

    copyfile(signup_detail_filename, detail_filename)

    delete_signup = os.path.join(students_dir, 'signup')
    rmtree(delete_signup)

    return render_template('sign_link.html')
    

# friend add
@app.route('/friend_add', methods=["POST"])
def friend_add():
    send_zid = request.form.get('send_zid')
    receive_zid = request.form.get('receive_zid')
    student_details = read_student_details()
    


    send_email(student_details[receive_zid]['email'], 'UNSWtalk_Friend_request', student_details[send_zid]['full_name'] + ' wants to add you friend, click here to response: https://cgi.cse.unsw.edu.au/~z5135897/ass2/UNSWtalk.cgi/friend_add_response?send_zid=' + send_zid + '&receive_zid=' \
                    + receive_zid)

    
    return render_template('friend_add.html', home_zid = send_zid, student_details = student_details, sent_to_zid = receive_zid)


# friend add response

@app.route('/friend_add_response', methods=['GET', 'POST'])
def friend_add_response():
    student_details = read_student_details()
    
    if request.method == 'GET':
        send_zid = request.args.get('send_zid')
        receive_zid = request.args.get('receive_zid')
        return render_template('friend_add_response.html', send_zid = send_zid, receive_zid = receive_zid, student_details = student_details)

    if request.method == 'POST':
        send_zid = request.form.get('send_zid')
        receive_zid = request.form.get('receive_zid')
        submit_type = request.form.get('response')
        print(submit_type)
        if submit_type == 'Confirm':

            send_find_friend = 0
            receive_find_friend = 0
            details_filename_sent = os.path.join(students_dir, send_zid, "student.txt")
            for line in fileinput.input(details_filename_sent, inplace=True):
                line = line.strip('\n')
                if 'friends' in line:
                    send_find_friend = 1
                    s = line.split(':')
                    s[1] = re.sub(r'^\s*\(','', s[1])
                    s[1] = re.sub(r'\)\s*$','', s[1])
                    s[1] = s[1].split(',')
                    s[1] = [i.strip() for i in s[1]]
                    s[1].append(receive_zid)
                    new_line = ','.join(s[1])
                    line = 'friends: (' + new_line + ')'
                    print(line)

                else:
                    print(line)

            if send_find_friend == 0:
                with open(details_filename_sent, 'a') as file:
                    file.write('friends: (' + receive_zid + ')\n')

                    
            

            details_filename_receive = os.path.join(students_dir, receive_zid, "student.txt")
            for line in fileinput.input(details_filename_receive, inplace=True):
                line = line.strip('\n')
                if 'friends' in line:
                    receive_find_friend = 1
                    s = line.split(':')
                    s[1] = re.sub(r'^\s*\(','', s[1])
                    s[1] = re.sub(r'\)\s*$','', s[1])
                    s[1] = s[1].split(',')
                    s[1] = [i.strip() for i in s[1]]
                    s[1].append(send_zid)
                    new_line = ','.join(s[1])
                    line = 'friends: (' + new_line + ')'
                    print(line)

                else:
                    print(line)


            if receive_find_friend == 0:
                with open(details_filename_receive, 'a') as file:
                    file.write('friends: (' + send_zid + ')\n')



            send_email(student_details[send_zid]['email'], 'UNSWtalk_Friend_request_result', student_details[receive_zid]['full_name'] + ' has confirmed your friend request, you are now friends ')
            
            return render_template('friend_response_result.html', send_zid = send_zid, zid = receive_zid, student_details = student_details, flag = 1)
        
        elif submit_type == 'Reject':
            
            email_command = 'echo ' + student_details[receive_zid]['full_name'] + ' has rejected your friend request ' \
                            + '| mail -s UNSWtalk_Friend_request_result ' + student_details[send_zid]['email']
            return render_template('friend_response_result.html', send_zid = send_zid, zid = receive_zid, student_details = student_details, flag = 0)

    
        
        
# upload iamge

@app.route('/upload', methods=['POST'])
def upload():
    student_details = read_student_details()
    home_zid = request.form.get('home_zid')
    upload_for = request.form.get('upload')
    if upload_for == "profile_img":
        return render_template('upload_process.html', zid = home_zid, message="Upload images for profile.", student_details = student_details)
    elif upload_for == "backg_img":
        return render_template('upload_process.html', zid = home_zid, message="Upload images for background.", student_details = student_details)


# upload process

@app.route('/upload_process', methods=['POST'])
def upload_process():
    
    file = request.files['file']
    uploader_zid = request.form.get('uploader_zid')
    img_type = request.form.get('img_type')


    if img_type == 'Upload images for profile.':
        profile_img_filename = os.path.join(students_dir, uploader_zid, 'img.jpg')
        if os.path.exists(profile_img_filename):
            os.remove(profile_img_filename)

        file.save(profile_img_filename)

    elif img_type == "Upload images for background.":
        background_img_filename = os.path.join(students_dir, uploader_zid, 'background_img.jpg')
        if os.path.exists(background_img_filename):
            os.remove(background_img_filename)

        file.save(background_img_filename)
        

    student_details = read_student_details()
    return render_template('profile.html', student_details = student_details, zid=uploader_zid)
    
    
    
# update profile information

@app.route('/update_pro', methods=['POST'])
def update_pro():
    submit_type = request.form.get('update_pro_button')
    updater_zid = request.form.get('updater_zid')
    if submit_type == "Update":
        student_details = read_student_details()
        return render_template('update_process.html', student_details = student_details, zid=updater_zid)

    if submit_type == "submit":
        dic = {}
        
        update_email = request.form.get('email')
        Update_full_name = request.form.get('full_name')
        update_birthday = request.form.get('birthday')
        update_home_suburb = request.form.get('home_suburb')
        update_program = request.form.get('program')
        update_course = request.form.get('course')
        update_bio = request.form.get('Introduction')
        if update_email:
            dic['email'] = update_email
        if Update_full_name:
            dic['full_name'] = Update_full_name
        if update_birthday:
            dic['birthday'] = update_birthday
        if update_home_suburb:
            dic['home_suburb'] = update_home_suburb
        if update_program:
            dic['program'] = update_program
        if update_course:
            dic['courses'] = update_course
        if update_bio:
            dic['bio'] = update_bio

        bio_find = 0
        
        details_filename = os.path.join(students_dir, updater_zid, "student.txt")
        for line in fileinput.input(details_filename, inplace=True):
            line = line.strip('\n')
            s = line.split(':')
            s = [i.strip() for i in s]
            
            if s[0] in dic:
                if s[0] == 'courses':
                    s = line.split(':')
                    
                    line = 'courses: (' + dic[s[0]] + ')'
                    print(line)

                elif s[0] == 'bio':
                    bio_find = 1
                    line = s[0] +': ' + dic[s[0]]
                    print(line)
                    
                else:

                    line = s[0] +': ' + dic[s[0]]
                    print(line)
                    
            else:
                print(line)


            if bio_find == 0 and dic['bio'] != None:
                with open(details_filename, 'a') as file:
                    file.write('bio: ' + dic['bio'])
            

        student_details = read_student_details()
        return render_template('profile.html', student_details = student_details, zid=updater_zid)


# read student information:

def read_student_details():
    student_details = defaultdict(dict)
    students = sorted(os.listdir(students_dir))
    for student_to_show in students:
        details_filename = os.path.join(students_dir, student_to_show, "student.txt")
        img_original_src = os.path.join(students_dir, student_to_show, "img.jpg")
        background_img = os.path.join(students_dir, student_to_show, "background_img.jpg")
        with open(details_filename) as f:
            for line in f:
                temp_line = line.strip('\n')
                if not temp_line.strip():
                    continue
                
                s = line.split(':')
                s = [i.strip() for i in s]
                if (s[0] == 'friends' or s[0] == 'courses'):
                    s[1] = re.sub(r'^\s*\(','', s[1])
                    s[1] = re.sub(r'\)\s*$','', s[1])
                    s[1] = s[1].split(',')
                    s[1] = [i.strip() for i in s[1]]
                    student_details[student_to_show][s[0]] = s[1]
                else:
                    student_details[student_to_show][s[0]] = s[1]
                    
        if(os.path.exists(img_original_src)):
            student_details[student_to_show]['img'] = '/'.join(img_original_src.split('/')[1:])
        else:
            student_details[student_to_show]['img'] = 0

        if(os.path.exists(background_img)):
            student_details[student_to_show]['background_img'] = '/'.join(background_img.split('/')[1:])
        else:
            student_details[student_to_show]['background_img'] = 0


    return student_details

# read student post:
def read_student_post(home_zid):
    home_zid = home_zid
    student_post = defaultdict(dict)
    student_details = read_student_details()
    students = sorted(os.listdir(students_dir))
    for student_to_show in students:
        if student_to_show == 'signup':
            continue
        student_post_file = sorted(os.listdir(students_dir + '/' + student_to_show))
        post_nb = {}
        for stu_post in student_post_file:
            m = re.match(r'^[0-9]+\.txt$', stu_post)
            if m:
                post_filename = os.path.join(students_dir, student_to_show, stu_post)
                with open(post_filename) as file:
                    dic_post_content = {}
                    for line in file:
                        s = line.split(':', maxsplit=1)
                        s = [i.strip() for i in s]
                        if(s[0] == 'message'):
                    
                            if home_zid in s[1]:
                                s[1] = s[1].replace(home_zid, '<a href=/~z5135897/ass2/UNSWtalk.cgi/profile?pro_zid=' + home_zid + ' target="_blank" style="text-decoration:none;"><span style="margin-left:5px;font-size:100%;color:black;">'\
                                                    + student_details[home_zid]['full_name'] + '</span></a>')

                            L = re.findall(r'z\d{7}', s[1])
                     
                            if home_zid in L:
##                                S = set(L)
##                                S.remove(home_zid)
##                                L = list(S)

                                temp_R = []
                                for i in L:
                                    if i != home_zid and i != 'z5135897':
                                        temp_R.append(i)

                                L = temp_R
        
                       
                            for rl in L:
                               
                                replace_e = "<a href=/~z5135897/ass2/UNSWtalk.cgi/page?home_zid=" + home_zid + "&user=" + rl  + ' target="_blank" style="text-decoration:none;"><span style="margin-left:5px;font-size:100%;color:black;">'\
                                                                                           + student_details[rl]['full_name'] + '</span></a>'


                     
                                s[1] = re.sub(rl, replace_e, s[1])
        
                            s[1] = s[1].replace('\\n', '<br>')
                                                  
                        dic_post_content[s[0]] = s[1]
                        
                        
                post_nb[int(stu_post[0 : len(stu_post) - 4])] = dic_post_content

            else:
                continue
        post_nb = collections.OrderedDict(sorted(post_nb.items(), reverse = True))
        student_post[student_to_show] = post_nb

            

    return student_post
             
                        
# read student comment
def read_student_comment(home_zid):
    home_zid = home_zid
    student_details = read_student_details()
    students = sorted(os.listdir(students_dir))
    student_comment = {}
    for student_zid in students:
        student_file = sorted(os.listdir(students_dir + '/' + student_zid))
        post_to_comment = {}
        for stu_comment in student_file:
            m = re.match(r'^(\d+)-(\d+)\.txt$', stu_comment)
            if m:
                post_nb = int(m.group(1))
                comment_nb = int(m.group(2))
                comment_filename = os.path.join(students_dir, student_zid, stu_comment)
                with open(comment_filename) as file:
                    dic_comment_content = {}
                    for line in file:
                        s = line.split(':', maxsplit=1)
                        s = [i.strip() for i in s]
                        if(s[0] == 'message'):
                    
                            if home_zid in s[1]:
                                s[1] = s[1].replace(home_zid, "<a href=/~z5135897/ass2/UNSWtalk.cgi/profile?pro_zid=" + home_zid  + ' target="_blank" style="text-decoration:none;"><span style="margin-left:5px;font-size:100%;color:black;">'\
                                                    + student_details[home_zid]['full_name'] + '</span></a>')

                            L = re.findall(r'z\d{7}', s[1])
                     
                            if home_zid in L:



                                temp_R = []
                                for i in L:
                                    if i != home_zid and i != 'z5135897':
                                        temp_R.append(i)
                                    

                                L = temp_R

                       
                            for rl in L:
##                                print('^', rl)
##                                print('*',rl, student_details[rl]['full_name'])
                                replace_e = "<a href=/~z5135897/ass2/UNSWtalk.cgi/page?home_zid=" + home_zid + "&user=" + rl  + ' target="_blank" style="text-decoration:none;"><span style="margin-left:5px;font-size:100%;color:black;">'\
                                                                                           + student_details[rl]['full_name'] + '</span></a>'

                              
                                s[1] = re.sub(rl, replace_e, s[1])

                            s[1] = s[1].replace('\\n', '<br>')
                            
                        dic_comment_content[s[0]] = s[1]
                        
                
                post_to_comment[(post_nb, comment_nb)] = dic_comment_content
        post_to_comment = collections.OrderedDict(sorted(post_to_comment.items(), reverse = True))
        student_comment[student_zid] = post_to_comment

    return student_comment




                
# read student reply

def read_student_reply(home_zid):
    home_zid = home_zid
    student_details = read_student_details()
    students = sorted(os.listdir(students_dir))
    student_reply = {}
    for student_zid in students:
        student_file = sorted(os.listdir(students_dir + '/' + student_zid))
        post_to_comment_to_reply = {}
        for stu_reply in student_file:
            m = re.match(r'^(\d+)-(\d+)-(\d+)\.txt$', stu_reply)
            if m:
                post_nb = int(m.group(1))
                comment_nb = int(m.group(2))
                reply_nb = int(m.group(3))
                reply_filename = os.path.join(students_dir, student_zid, stu_reply)
                with open(reply_filename) as file:
                    dic_reply_content = {}
                    for line in file:
                        s = line.split(':', maxsplit=1)
                        s = [i.strip() for i in s]
                        if(s[0] == 'message'):
                    
                            if home_zid in s[1]:
                                s[1] = s[1].replace(home_zid, "<a href=/~z5135897/ass2/UNSWtalk.cgi/profile?pro_zid=" + home_zid  + ' target="_blank" style="text-decoration:none;"><span style="margin-left:5px;font-size:100%;color:black;">'\
                                                    + student_details[home_zid]['full_name'] + '</span></a>')

                            L = re.findall(r'z\d{7}', s[1])
                     
                            if home_zid in L:


                                temp_R = []
                                for i in L:
                                    if i != home_zid and i != 'z5135897':
                                        temp_R.append(i)

                                L = temp_R

                       
                            for rl in L:
                               
                                replace_e = "<a href=/~z5135897/ass2/UNSWtalk.cgi/page?home_zid=" + home_zid + "&user=" + rl + ' target="_blank" style="text-decoration:none;"><span style="margin-left:5px;font-size:100%;color:black;">'\
                                                                                           + student_details[rl]['full_name'] + '</span></a>'
                                s[1] = re.sub(rl, replace_e, s[1])
                            s[1] = s[1].replace('\\n', '<br>')
                            
                        dic_reply_content[s[0]] = s[1]

                post_to_comment_to_reply[(post_nb, comment_nb, reply_nb)] = dic_reply_content

        post_to_comment_to_reply = collections.OrderedDict(sorted(post_to_comment_to_reply.items(), reverse = True))
        student_reply[student_zid] = post_to_comment_to_reply

    return student_reply

        
                    
# get post time

def get_time():
    time_1 = str(datetime.datetime.now())
    s = time_1.split()
    a = s[1]
    b = a.split('.')
    return s[0] + 'T' + b[0] + '+0000'

                

# get all post comment reply

def get_post_comment_reply(zid):

    zid = zid
    
    student_details = read_student_details()
    student_posts = read_student_post(zid)
    student_comments = read_student_comment(zid)
    student_replys = read_student_reply(zid)

    to_print_post = []


    for stu_zid in student_posts:

        if stu_zid == zid:
            for post_nb in student_posts[stu_zid]:
                a = (stu_zid, post_nb, student_posts[stu_zid][post_nb]['time'])

                to_print_post.append(a)

        elif 'friends' in student_details[zid] and stu_zid in student_details[zid]['friends']:
            for post_nb in student_posts[stu_zid]:
                a = (stu_zid, post_nb, student_posts[stu_zid][post_nb]['time'])
  
                to_print_post.append(a)

        else:
            for post_nb in student_posts[stu_zid]:
                if ('message' not in student_posts[stu_zid][post_nb]):
                    continue
                m = re.search(student_details[zid]['full_name'], student_posts[stu_zid][post_nb]['message'])
                if m:
                    a = (stu_zid, post_nb, student_posts[stu_zid][post_nb]['time'])
 
                    to_print_post.append(a)
        

    for stu_zid in student_comments:
        if stu_zid == zid:
            continue
        if 'friends' in student_details[zid] and stu_zid in student_details[zid]['friends']:
            continue

        for post_comment in student_comments[stu_zid]:

            if ('message' not in student_comments[stu_zid][post_comment]):
                continue
            
            m = re.search(student_details[zid]['full_name'], student_comments[stu_zid][post_comment]['message'])
            if m:
                a = (stu_zid, post_comment[0], student_posts[stu_zid][post_comment[0]]['time'])
                if a not in to_print_post:
            
                    to_print_post.append(a)

    for stu_zid in student_replys:
        if stu_zid == zid:
            continue
        if 'friends' in student_details[zid] and stu_zid in student_details[zid]['friends']:
            continue

        for post_comment_reply in student_replys[stu_zid]:
            if ('message' not in student_replys[stu_zid][post_comment_reply]):
                continue
            
            m = re.search(student_details[zid]['full_name'], student_replys[stu_zid][post_comment_reply]['message'])
            if m:
                a = (stu_zid, post_comment_reply[0], student_posts[stu_zid][post_comment_reply[0]]['time'])
                print('here', a)
                if a not in to_print_post:
               
                    to_print_post.append(a)



    to_print_post = sorted(to_print_post, key = lambda x:x[2], reverse=True)
    
    postcomment = {}
    
    for zid_postnb_time in to_print_post:
        temp_zid = zid_postnb_time[0]
        post_nb = zid_postnb_time[1]
        
        to_print_comment = []
        for post_comment in student_comments[temp_zid]:
            if post_comment[0] == post_nb:
                a = (temp_zid, post_nb, post_comment[1], student_comments[temp_zid][post_comment]['time'])
                to_print_comment.append(a)

        to_print_comment = sorted(to_print_comment, key = lambda x:x[3], reverse=True)
        postcomment[zid_postnb_time] = to_print_comment


    postcommentreply = {}
    for zid_postnb_time in to_print_post:
        for zid_postnb_comment_time in postcomment[zid_postnb_time]:

            temp_zid = zid_postnb_comment_time[0]
            post_nb = zid_postnb_comment_time[1]

            to_print_reply = []
            for post_comment_reply in student_replys[temp_zid]:
              
                if (post_comment_reply[0] == post_nb and post_comment_reply[1] == zid_postnb_comment_time[2]):
      
                    a = (temp_zid, post_nb, post_comment_reply[1], post_comment_reply[2], student_replys[temp_zid][post_comment_reply]['time'])
                    to_print_reply.append(a)

                to_print_reply = sorted(to_print_reply, key = lambda x:x[4], reverse=True)


                postcommentreply[zid_postnb_comment_time] = to_print_reply
            
     
                

    return to_print_post, postcomment, postcommentreply
                        


# search post content

def get_search_post_comment_reply(zid, search_content):

    zid = zid
    search_content = search_content
    student_details = read_student_details()
    student_posts = read_student_post(zid)
    student_comments = read_student_comment(zid)
    student_replys = read_student_reply(zid)

    to_print_post = []


    for stu_zid in student_posts:

        if stu_zid == zid:
            for post_nb in student_posts[stu_zid]:
                if(search_content.lower() in student_posts[stu_zid][post_nb]['message'].lower()):
                    
                    a = (stu_zid, post_nb, student_posts[stu_zid][post_nb]['time'])
                    to_print_post.append(a)


        elif stu_zid in student_details[zid]['friends']:
            for post_nb in student_posts[stu_zid]:
                if(search_content.lower() in student_posts[stu_zid][post_nb]['message'].lower()):
                    
                    a = (stu_zid, post_nb, student_posts[stu_zid][post_nb]['time'])
                    to_print_post.append(a)

        else:
            for post_nb in student_posts[stu_zid]:
                if ('message' not in student_posts[stu_zid][post_nb]):
                    continue
                m = re.search(student_details[zid]['full_name'], student_posts[stu_zid][post_nb]['message'])
                if m:
                    if(search_content.lower() in student_posts[stu_zid][post_nb]['message'].lower()):
                        
                        a = (stu_zid, post_nb, student_posts[stu_zid][post_nb]['time'])
                        to_print_post.append(a)
        



    to_print_post = sorted(to_print_post, key = lambda x:x[2], reverse=True)
    
    postcomment = {}
    
    for zid_postnb_time in to_print_post:
        temp_zid = zid_postnb_time[0]
        post_nb = zid_postnb_time[1]
        
        to_print_comment = []
        for post_comment in student_comments[temp_zid]:
            if post_comment[0] == post_nb:
                a = (temp_zid, post_nb, post_comment[1], student_comments[temp_zid][post_comment]['time'])
                to_print_comment.append(a)

        to_print_comment = sorted(to_print_comment, key = lambda x:x[3], reverse=True)
        postcomment[zid_postnb_time] = to_print_comment


    postcommentreply = {}
    for zid_postnb_time in to_print_post:
        for zid_postnb_comment_time in postcomment[zid_postnb_time]:

            temp_zid = zid_postnb_comment_time[0]
            post_nb = zid_postnb_comment_time[1]

            to_print_reply = []
            for post_comment_reply in student_replys[temp_zid]:
              
                if (post_comment_reply[0] == post_nb and post_comment_reply[1] == zid_postnb_comment_time[2]):
      
                    a = (temp_zid, post_nb, post_comment_reply[1], post_comment_reply[2], student_replys[temp_zid][post_comment_reply]['time'])
                    to_print_reply.append(a)

                to_print_reply = sorted(to_print_reply, key = lambda x:x[4], reverse=True)
        

                postcommentreply[zid_postnb_comment_time] = to_print_reply
            
     
                

    return to_print_post, postcomment, postcommentreply
        

## get prepared for friend suggestion
def get_course_session_dic():
    students = sorted(os.listdir(students_dir))
    course_session_dic = defaultdict(list)
    
    for temp_zid in students:
        details_filename = os.path.join(students_dir, temp_zid, "student.txt")
        with open(details_filename) as file:
            for line in file:
                if 'courses:' not in line:
                    continue
                s = line.split(':')
                course_information = s[1]
                course_information = re.sub(r'^\s*\(','', course_information)
                course_information = re.sub(r'\)\s*$','', course_information)
                course_list = course_information.split(',')
                course_list = [i.strip() for i in course_list]
                for course_session in course_list:
                    course_session_dic[course_session].append(temp_zid)

    return course_session_dic

## send email reference from Lecturer

def send_email(to, subject, message):

    mutt = [
            'mutt',
            '-s',
            subject,
            '-e', 'set copy=no',
            '-e', 'set realname=UNSWtalk',
            '--', to
    ]

    subprocess.run(
            mutt,
            input = message.encode('utf8'),
            stderr = subprocess.PIPE,
            stdout = subprocess.PIPE,
    )     




if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)
