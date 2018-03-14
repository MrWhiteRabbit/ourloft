# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, url_for, request
from app import app, db, routes, models, errors
from datetime import datetime
from app.forms import LoginForm, WeatherForm, RegistrationForm, EditProfileForm, PostForm, ExcelForm
import requests, smtplib
from app import conf #This module in the gitignore
from bs4 import BeautifulSoup as bs
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post
from werkzeug.urls import url_parse
import pandas as pd


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Твой пост опубликован!')
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)    
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)    
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None    
    return render_template('index.html', title='Главная', form=form, 
        posts=posts.items, next_url=next_url, prev_url=prev_url)


@app.route('/xls', methods=['GET', 'POST'])
@login_required
def xls():
    form = ExcelForm()
    file = 'v.xlsx'
    xl = pd.ExcelFile(file)
    sn = xl.sheet_names
    df1 = xl.parse(sn)
    writer = pd.ExcelWriter('e1.xlsx', engine='xlsxwriter')
    data = pd.read_excel('v.xlsx', index_col='ID')
    data.to_excel(writer, 'Sheet1')
    flash('Данные выгружены.')
    return render_template('xls.html', title='Главная', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неправильные Имя или Пароль!')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(url_for('index'))
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Поздравляем, вы зарегистрированы!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None    
    return render_template('user.html', user=user, posts=posts.items,
        next_url=next_url, prev_url=prev_url)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Данные сохранены.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Редактировать профиль', form=form)

@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None    
    return render_template('index.html', title='Поиск', 
        posts=posts.items, next_url=next_url, prev_url=prev_url)

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Пользователь {} не найден.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('Вы не можете подписаться на себя.')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('Вы подписались на {}'.format(username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Пользователь {} не найден.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('Вы не можете отписаться от себя.')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('Вы отписались от {}'.format(username))
    return redirect(url_for('user', username=username))    


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

#parsing weather site function. 
@app.route('/w', methods=['POST'])
@login_required
def w():

    f = open(conf.weather_file, 'w')
    f.write('Привет, Семья! Вот прогноз погоды в наших городах на сегодня:' + '\n' + '\n')

    for element in range(0, len(conf.city_arr)):
        city = conf.city_arr[element]
        rqst = requests.get('https://sinoptik.com.ru/погода-' + city)
        soup = bs(rqst.text, 'html.parser')

        p3 = soup.select('.temperature .p3')
        weather1 = p3[0].getText()

        p4 = soup.select('.temperature .p4')
        weather2 = p4[0].getText()

        p5 = soup.select('.temperature .p5')
        weather3 = p5[0].getText()

        p6 = soup.select('.temperature .p6')
        weather4 = p6[0].getText()

        p = soup.select('.rSide .description')
        weather = p[0].getText()

        f.write('----------------------------------' + '\n' +
                weather.strip() + '\n' +
                'Утром: ' + weather1 + ' ' + weather2 + '\n' +
                'Вечером: ' + weather3 + ' ' + weather4 + '\n')

    pw = soup.select('.oDescription .rSide .description')
    people_weather = pw[0].getText()

    f.write('----------------------------------' + '\n' +
        '\n' + people_weather.strip() + '\n' + '\n' +
        '----------------------------------' + '\n')

    rqst_news = requests.get('https://eadaily.com/ru/dossier/etot-den-v-istorii')
    soup_news = bs(rqst_news.text, 'html.parser')

    f.write('А вот что произошло в этот день в истории Человечества: ' + '\n')
    
    news = soup_news.select('.news-feed a')
    for i in news:
        a = i.getText()
        b = a[a.find(': '):]
        f.write(b + '\n')

    f.write('----------------------------------' + '\n' +
        'Хорошего всем настроения! Ваш новостной робот. :)')


    f.close()
    flash('Данные сформированы.')    

    with open(conf.weather_file, 'r') as f:
        msg_body = f.read()
        
    msg = MIMEMultipart()
    msg['From'] = conf.fromaddr
    msg['To'] = conf.toaddr
    msg['Subject'] = 'Привет от робота'

    msg.attach(MIMEText(str(msg_body), 'plain'))

    server = smtplib.SMTP(conf.serv, conf.port)
    server.starttls()
    server.login(conf.fromaddr, conf.mypass)
    text = msg.as_string()
    server.sendmail(conf.fromaddr, conf.toaddr, text)
    server.quit()
    flash('Данные отправлены.')
    return redirect(url_for('weather'))


@app.route('/weather', methods=['GET', 'POST'])
@login_required
def weather():
    form = WeatherForm()
    return render_template('weather.html', title='Рассылка погоды', form=form)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)