import datetime
import hashlib
import linecache
import os
import random
import requests
import subprocess
import threading
import time

import datefinder
from pywebio.input import *
from pywebio.output import *
from pywebio.platform import *
from pywebio.session import *


# to do list directory is sync-thinged to an rpi :)
# no need to write code for that


todolist = []
# to-do list items are stored as text files in the /todo directory
# active items are in the /todo/active directory
# completed items are in the /todo/completed directory
# each file contains a title and a description of the item, time added and time completed
# the title is the first line of the file, description is the second and time added is the third and time completed is the fourth

# if todo/active doesnt exist, create it
if not os.path.exists("todo/active"):
    os.mkdir("todo/active")

if not os.path.exists("todo/completed"):
    os.mkdir("todo/completed")

if not os.path.exists("habits"):
    os.mkdir("habits")

habits = dict()
for habit in os.listdir("habits"):
    print(habit)
    with open("habits/" + habit, "r") as f:
        lines = f.readlines()
        habitname = lines[0].strip()
        habits[habitname] = {}
        weekdays = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        for line, weekday in list(zip(lines[1:], weekdays)):
            habits[habitname][weekday] = int(line.strip())
print(habits)

class counter():
    def __init__(self):
        self.Count = 0
        self.Data = "hn-urls.txt"
    def countfunc(self):
        self.Count +=1
counting = counter()

# okay, yeah, this shouldve been a for loop, but Man, in his own hubris, has, yet again, went too far.
'''
Now it is such a bizarrely improbable coincidence that anything so mind-bogglingly stupid could have evolved purely by chance that some thinkers have chosen to see it as a final and clinching proof of the NON-existence of God.
The argument goes like this:
I refuse to prove that I exist,' says God, for proof denies faith, and without faith I am nothing.'
But,' says Man, The Bad PrOgRamMiNg Kirby is a dead giveaway, isn't it? It could not have evolved by chance. It proves you exist, and so therefore, by your own arguments, you don't. QED.'
Oh dear,' says God, I hadn't thought of that,' and promptly disappears in a puff of logic.
'''

url_file_length_call = [eval("counting.countfunc()") for line in open(counting.Data)]

def random_hn_link():
    randomno = random.randint(1, counting.Count)
    with open("hn-urls.txt", "r") as f:
        return linecache.getline("hn-urls.txt", randomno)


# function that reloads everytime there is a change in the todolist
def update_list():
    global todolist
    todolistchangestracker = []
    # for every item in the active directory, add it to the todolist as a tuple of (title, description)
    for item in os.listdir("todo/active"):
        with open("todo/active/" + item, "r") as f:
            todolistchangestracker.append((f.readline().strip(), f.readline().strip()))

    if todolistchangestracker == todolist:
        return
    else:
        todolist = todolistchangestracker
        with use_scope("todo", clear=True):
            display_list()
        


# function that adds an item to the todolist
def add_item():
    # ask for title and description
    title = str(input("Title: "))
    # create a hash of the title and grab the first 10 chars
    hash_title = hashlib.sha256(title.encode("utf-8")).hexdigest()[:10]
    description = input("Description: ")
    dates_included = datefinder.find_dates(description)
    if dates_included:
        try: 
            
            taskdate = [date for date in dates_included][0].strftime("%H:%M %b %d")
            title = title + " " + taskdate
             
            command = "at "+  taskdate+" <<< 'notify-send " + title+ "'"
            try: 
                sub = subprocess.Popen(command, shell=True)
                with use_scope("todo"):
                    toast(title, "automatic notification set")
            except: toast(title, "notification not set")
        except: pass


    # create a new file with the title and description
    with open("todo/active/" + title, "w") as f:
        f.write(title + "\n")
        f.write(description)
    # update the list
    update_list()


# function that removes an item from the todolist
def remove_item(item):
    # misbehaves when item title is an int :/
    # move the item to the completed directory
    os.rename("todo/active/" + item, "todo/completed/" + item)
    # update the list
    update_list()


# function that displays the todolist, with a button for each item that removes it
def display_list():
    # clear the todolist
    with use_scope("todo", clear=True):
        # for every item in the todolist, display it with a button to remove it
        for item in todolist:
            put_collapse(item[0], put_button("Remove", lambda x=item[0]: remove_item(x)))
            
           



# for every item in the active directory, add it to the todolist as a tuple of (title, description)
for item in os.listdir("todo/active"):
    with open("todo/active/" + item, "r") as f:
        todolist.append((f.readline().strip(), f.readline().strip()))


def show_time():
    while True:
        with use_scope(name="time", clear=True):

            put_markdown("# " + datetime.datetime.now().strftime("%H:%M %a %B %d "))
            time.sleep(10)


# habit tracker
# habits are stored as text files in the /habits directory

# 0 = not completed
# 1 = completed
# if habit is marked complete on a monday, then habit[monday] = 1, and if completed on a wednesday, then habit[wednesday] is marked as 1.

# a habit file is of the format:
# habitname
# 1
# 0
# 0
# 1
# 0
# 0
# 0

with use_scope("habits", clear=True):
    habits = dict()
    for habit in os.listdir("habits"):
        print(habit)
        with open("habits/" + habit, "r") as f:
            lines = f.readlines()
            habitname = lines[0].strip()
            habits[habitname] = {}

            weekdays = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            for line, weekday in list(zip(lines[1:], weekdays)):

                habits[habitname][weekday] = int(line.strip())

def display_habits():
    with use_scope("habits", clear=True):
        def progress():
        # for every habit in the habits directory, sum the values of the days of the week and divide by number of habits*7
        # convert this to a percentage
        # display a progress bar with the percentage
            with use_scope("progress", clear=True):
                progress = 0
                for habit in habits:
                    for day in habits[habit]:
                        progress += habits[habit][day]
                        
                progress = progress / (len(habits) * 7)
                
                put_processbar("bar");
                set_processbar("bar", progress)

        while True:
            
            for habit in habits:
                # display a row of buttons for each day of the week
                
                checks = checkbox(
                    habit,
                    # options is a list of dicts with the following keys:
                    #   - label: the day of the week
                    #   - value: 1 if the habit is checked, 0 otherwise
                    #   - selected: True if the habit is checked, False otherwise
                    options=[
                        {
                            "label": day,
                            "value": day,
                            "selected": habits[habit][day] == 1,
                        }
                        for day in habits[habit]
                    ],
                    inline=True,
                )
                
                # not_checks is a list weekdays without the elements of checks
                not_checks = [i for i in weekdays if i not in checks]
                for day in not_checks:
                    habits[habit][day] = 0

                for day in checks:
                    habits[habit][day] = 1
                # write in the habits file
                with open("habits/" + habit, "w") as f:
                    # clear the filechecks
                    f.write(habit + "\n")
                    progress()
                    for day in habits[habit]:
                        f.write(str(habits[habit][day]) + "\n")





def open_link():
    subprocess.Popen(["xdg-open", random_hn_link()])

def main():
    config(theme="dark")
    t = threading.Thread(target=show_time)
    habit_tracker = threading.Thread(target=display_habits)
    

    
    register_thread(t)
    register_thread(habit_tracker)
    
    t.start()
    habit_tracker.start()
    

    with use_scope("button"):
        put_button("Add ToDo", add_item, outline=True)

    with use_scope("todo", clear=True):
        display_list()
    
    put_markdown("## ")
    
    put_button("random reading link", open_link, outline=True)
    
    # with use_scope("comics"):
    #     # xkcd = "https://xkcd.com/"
    #     # # get the latest comic
    #     # comic = requests.get(xkcd + "info.0.json").json()
    #     # # get the image url
    #     # image_url = comic["img"]
    #     # # get the title
    #     # title = comic["safe_title"]
    #     # # get the alt text
    #     # alt = comic["alt"]
    #     # # put the image
    #     # put_image(image_url, title, alt)
    
    
    # update the list
    while True:
        time.sleep(1)
        update_list()
        


if __name__ == "__main__":
    start_server(main(), debug=True)
