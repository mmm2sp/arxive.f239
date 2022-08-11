import requests
import os  

def no_spaces(string):
    '''
    Убирает лишние пробелы и переносы строк
    '''
    if string == "":
        return string
    string = string.replace("\n", "")
    string = string.replace("\r", "")
    string = string.lstrip()#Убирает пробелы в начале строки
    string = string.rstrip()#Убирает пробелы в конце строки
    
##    while string.find("  ", 0) >= 0: string = string.replace("  ", " ")
    string = string.replace("###!123###", "\n") #Бывший  <br />

    string = string.replace("$$\n\n$$", "")
    
    string = string.replace("&gt;", ">")
    string = string.replace("&lt;", "<")
    string = string.replace("&mdash;", "-")
    string = string.replace("%", "\%")
    string = string.replace("&#x27;", "'")
    string = string.replace("π", "\pi ")
    string = string.replace("&times;", "$\\times$")
    string = string.replace("&laquo;", '"')
    string = string.replace("&raquo;", '"')
    string = string.replace("$,$", ", \,")

    #Костыль про patch-clamp
    string = string.replace("_\max", "_{\max}")
    
    return string


def save_MScheme(f, data):
    data = data.replace("<br />", "###!123###")
    first_idx = data.find('<td style="width:90%;">', 0)
    if first_idx != -1:
        last_idx = data.find('</td>', first_idx)
        text = data[first_idx + len('<td style="width:90%;">'):last_idx:]
        tmp_idx_0 = text.find('<span', 0)
        if tmp_idx_0 >= 0:
            tmp_idx_1 = text.find('>', tmp_idx_0)
            tmp_idx_2 = text.find('</span>', tmp_idx_1)
            version = text[tmp_idx_1 + 1:tmp_idx_2:]
            text = text[:tmp_idx_0:] + text[tmp_idx_2 + len('</span>'):]
        else:
            version = ""    
       
        text = no_spaces(text)

        first_idx = data.find('<td style="width:10%; text-align: center;">', last_idx)
        last_idx = data.find('</td>', first_idx)
        cost = data[first_idx + len('<td style="width:10%; text-align: center;">'):last_idx:]
        cost = no_spaces(cost)

        if version == "":
            f.write("\MBlock{" + cost + "}{" + text + "}\n\n")
        else:
            f.write("\MMBlock{" + cost + "}{" + version +  "}{" + text + "}\n\n")


def save_QBlock(f, data):
    data = data.replace("<br />", "###!123###")
    first_idx = data.find('<span class="label label-lg font-weight-normal label-rounded label-inline label-primary mr-2">', 0)
    if first_idx != -1:
        name_first_idx = data.find('>', first_idx) + 1
        name_last_idx = data.find('</span>', name_first_idx)
        if name_last_idx == -1: return
        name_str = data[name_first_idx:name_last_idx:]
        
        cost_first_idx = name_str.find('<sup>&nbsp;', 0)
        if cost_first_idx != -1:
            cost_last_idx = name_str.find('</sup>', 0)
            cost_str = name_str[cost_first_idx + len('<sup>&nbsp;'):cost_last_idx:]
            name_str = name_str[:cost_first_idx:] + name_str[cost_last_idx + len('</sup>')::]
        else: cost_str = ""

        name_str = no_spaces(name_str)

        first_idx = data.find('</span>', first_idx)
        if first_idx == -1: return
        last_idx = -1
        last_idx_1 = data.find("<phors-answer", first_idx + len('</span>'))
        last_idx_2 = data.find("<p></p>", first_idx + len('</span>'))
        if (last_idx_1 != -1) and (last_idx_2 > last_idx_1 or last_idx_2 == -1):
            last_idx = last_idx_1
        else:
            last_idx = last_idx_2
        #print(last_idx, " | ", last_idx_1, " ### ", last_idx_2)
        if last_idx == -1: return
        
        block = data[first_idx + len('</span>'):last_idx:]
        block = no_spaces(block)
        
        f.write("\QBlock{" + name_str + "}{" + cost_str + "}{" + block + "}\n\n")


def save(f, data):
    data = data.replace("<br />", "###!123###")
    
    #Обработка вложенных <p></p>
    first_idx = data.find('<p>', 0)
    if first_idx != -1:
        last_idx = data.find('</p>', first_idx)
        tmp_idx = data.find('</p>', last_idx + 1)
        while tmp_idx != -1:
            last_idx = tmp_idx
            tmp_idx = data.find('</p>', last_idx + 1)
        save(f, data[first_idx + len('<p>'):last_idx:])
        data = data[:first_idx:] + data[last_idx + len('</p>')::]

    #Удаление неинформативного куска
    first_idx = data.find('<a', 0) 
    while first_idx != -1:
        last_idx = data.find('</a>', first_idx)
        data = data[:first_idx:] + data[last_idx + len('</a>')::]
        first_idx = data.find('<a', 0)

    first_idx = data.find('<', 0)

    #Если в дате только текст
    if first_idx == -1:
        data = no_spaces(data)
        if data == "": return
        f.write("\QText{" + data + "}")
        f.write("\n\n")
    else:
        #Если в дате первым идет "блок"
        if first_idx == data.find('<span class="label label-lg font-weight-normal label-rounded label-inline label-primary mr-2">', 0):
            save_QBlock(f, data)
        else:
            #Если в дате первым идет заголовок
            if first_idx == data.find('<span class="font-weight-boldest">', 0):
                last_idx = data.find('</span>', first_idx)
                chapter = data[first_idx + len('<span class="font-weight-boldest">'):last_idx:]
                chapter = no_spaces(chapter)
                f.write("\Chapter{" + chapter + "}\n\n")
            else:
                old_idx = first_idx
                first_idx = data.find('<span>Ответ:', 0)
                #Блок с ответом
                if first_idx >= 0:
                    last_idx = data.find('</span>', first_idx)
                    answer_block = data[first_idx + len('<span>Ответ:'):last_idx:]
                    answer_block = no_spaces(answer_block)
                    f.write("\ABlock{" + answer_block + "}\n\n")
                else:
                    #Картинка
                    first_idx = data.find('<img src="', 0)
                    if first_idx != -1:
                        last_idx = data.find('.jpeg', first_idx)
                        pic_name = data[first_idx + len('<img src="'):last_idx:] + '.jpeg'
                        
                        first_idx = data.find('style=', last_idx) + len ('style=')
                        last_idx = data.find('/>', first_idx)
                        pic_params = data[first_idx:last_idx:]
                        pic_params = no_spaces(pic_params)

                        first_idx = data.find('<div class="kt-section__info"', last_idx)
                        if first_idx != -1:
                            first_idx = data.find('>', first_idx) + 1
                            last_idx = data.find('</div>', first_idx)
                            pic_sub = data[first_idx:last_idx:]
                        else:
                            pic_sub = ''
                        first_idx = data.find('<div class="col-md-8 latexinput" >', 0)
                        if first_idx != -1:
                            last_idx = data.find('</div>', first_idx)
                            text = data[first_idx + len('<div class="col-md-8 latexinput" >'):last_idx:]
                            text = no_spaces(text)
                        else:
                            text = ""
                        f.write("\QPicture{" + pic_name + "}{" + pic_params + "}{" + pic_sub + "}{" + text + "}\n\n")
                    else:
                         print("idx = "+ str(old_idx))
                    
                    
                
def compile_page(url, url_num, url_type, url_name):
    if url_type == "-s":
        document_type = "Решение"
    else:
        if url_type == "-m":
            document_type = "Разбалловка"
        else:
            document_type = "Условие задачи"

    
    r = requests.get(url) #url - ссылка
    html = r.text

    #Считывание названия задачи
    first_idx = html.find('<title>', 0)
    last_idx = html.find('</title>', first_idx)
    problem_name = html[first_idx + len('<title>'):last_idx:]
    problem_name = problem_name.replace("Pho.rs:", "")
    problem_name = no_spaces(problem_name)

    if problem_name.find("Metronic | Login Page v3", 0) >= 0:
        print(url_num + " This page is empty now")
        return
    problem_name = problem_name.replace("?", "")

    file_name = url_name + " " + problem_name + url_type

    last_idx = 0
    first_idx = html.find("/p/img/", last_idx + 1)
    while first_idx >= 0:
        last_idx = html.find("/", first_idx + len("/p/img/"))
        num = html[first_idx + len("/p/img/"):last_idx:]

        #Сохранение картинок
        new_idx = html.find('"', last_idx + 1)
        tmp_type = html[last_idx:new_idx:]
        p = requests.get("https://pho.rs/p/img/"+num+tmp_type)
        try:
            os.mkdir(file_name + "_files")
        except:
            tmp = 0
        name_txt = file_name + "_files/ReadMe.txt"
        out = open(name_txt, "w")
        out.write("This file and folder were created automatically. There will be pictures that are usefull to create pdf. Do not remove it")
        out.close()
        name_img = file_name + "_files/" + num + ".jpeg"
        out = open(name_img, "wb")
        out.write(p.content)
        out.close()
        
        html = html[:first_idx:] + name_img + html[last_idx + len(tmp_type)::]
        first_idx = html.find("/p/img/", last_idx + 1)

    #Верстка html-страницы
    f = open(file_name + '.html', 'w', encoding='utf-8')
    f.write(html)
    f.close()

    f = open(file_name +'.tex', 'w', encoding='utf-8') 
    f.write("\n")
    f.write("\\input{Preambula.tex}\n\n" )
    f.write("\\newcommand\ProblemName{" + problem_name + "}\n\n")
    f.write("\\newcommand\Source{" + str(url_name) + "}\n\n")
    f.write("\\newcommand\Type{" + document_type + "}\n\n")
    f.write("\\input{Settings.tex}\n\n" )

    last_idx = 0
    first_idx = html.find('<p>', 0)#Обычный текст
    second_idx = html.find('<div class="card-body card-body-phors">', 0)#Блоки с условием на странице с решением
    third_idx = html.find('<tr>', 0)#Пункт разбалловки
    while first_idx >= 0 or second_idx >= 0 or third_idx >= 0:
        if first_idx >= 0 and (second_idx > first_idx or second_idx < 0) and (third_idx > first_idx or third_idx < 0):
            last_idx = html.find('</p>', first_idx)
            data = html[first_idx + len('<p>'):last_idx:]
            num_of_p = data.count('<p>')
            i = 0
            while i < num_of_p:
                last_idx = html.find('</p>', last_idx + 1)
                i = i + 1
            data = html[first_idx + len('<p>'):last_idx:]
            save(f, data)
            first_idx = html.find('<p>', last_idx)
        else:
            if second_idx >= 0 and (second_idx < first_idx or first_idx < 0) and (third_idx > second_idx or third_idx < 0):
                last_idx = html.find('<p></p>', second_idx)
                if last_idx >= 0:
                    data = html[second_idx + len('<div class="card-body card-body-phors">'):last_idx + len('<p></p>'):]
                    save_QBlock(f, data)
                    second_idx = html.find('<div class="card-body card-body-phors">', last_idx)
                else: second_idx = -1
            else:
                last_idx = html.find('</tr>', third_idx)
                data = html[third_idx + len('<tr>'): last_idx:]
                save_MScheme(f, data)
                third_idx = html.find('<tr>', last_idx)

    f.write("\end{document}")
    f.close()
    os.system('pdflatex "' + file_name + '.tex"')
    os.system('pdflatex "' + file_name + '.tex"')

#############################

def error():
    print("URL is incorrect")
    
print("Введите номер страницы на pho.rs")
url_num = input()
url_num = str(url_num)
print("Выберите, что нужно собрать: Условие (t), Решение (s), Разбалловка (m), Подсказка (h) или сразу все (a)")
url_type = input()
print('Введите источник задачи. Например, "Χ21-Τ6"')
url_name = input()

##for i in range(222, 223):
##    url_num = str(i)
##    url_type = "t"
##    url_name = "T" + url_num

if (not url_num.isdigit()) or not (url_type == 't' or url_type == 's' or url_type == 'm' or url_type == 'h' or url_type == 'a'):
    error()
else:
    url = 'https://pho.rs/p/'
    url = url + str(url_num)
    if url_type == "a":
        compile_page(url, url_num, "", url_name)
        compile_page(url + '/s', url_num, "-s", url_name)
        compile_page(url + '/m', url_num, "-m", url_name)
        compile_page(url + '/h', url_num, "-h", url_name)
    else:
        if url_type != "t":
              url = url + '/' + str(url_type)
              url_type = "-" + url_type
        else: url_type = ""
        compile_page(url, url_num, url_type, url_name)
