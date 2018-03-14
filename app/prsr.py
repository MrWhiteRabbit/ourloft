import requests
from bs4 import BeautifulSoup as bs

weather_file = 'weather.txt'
city_arr = [
    'москва',
    'ставрополь',
    'ростов-на-дону',
    'иву'
]

f = open(weather_file, 'w')
f.write('Привет, Семья! Вот прогноз погоды в наших городах на сегодня:' + '\n' + '\n')



for element in range(0, len(city_arr)):
    city = city_arr[element]
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

#_Этот функционал дорабатываю - парсится без текста ссылок_

#rqst_news_wiki = requests.get('https://ru.wikipedia.org/wiki/Заглавная_страница')
#soup_news_wiki = bs(rqst_news_wiki.text, 'html.parser')
#news_find = soup_news_wiki.find('div', {'id': 'mf-mf-day'})
#news_select = news_find.select('a')
#f_news_wiki = open('news_wiki.txt', 'w')
#for j in news_select:
#    f_news_wiki.write(j.getText() + '\n')
#f_news_wiki.close()


#Выгружаем новости "в этот день произошло..."

rqst_news = requests.get('https://eadaily.com/ru/dossier/etot-den-v-istorii')
soup_news = bs(rqst_news.text, 'html.parser')

f.write('А вот что произошло в этот день в истории Человечества: ' + '\n')
#f_news = open('news.txt', 'w')
news = soup_news.select('.news-feed a')
for i in news:
    a = i.getText()
    b = a[a.find(':'):]
    f.write(b + '\n')
#    f_news.write(b + '\n')

f.write('----------------------------------' + '\n' +
    'Хорошего всем настроения! Ваш новостной робот. :)')

#f_news.close()
f.close()


print('Данные сформированы.')