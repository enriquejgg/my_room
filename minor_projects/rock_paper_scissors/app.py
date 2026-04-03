# from tkinter import Tk, Label, Button, LabelFrame
from tkinter import *
import tkinter as tk
import tkinter.ttk as ttk
import random


class RPS:
    def __init__(self, master):

        # main window
        self.wind = master
        self.wind.title("Rock - Paper - Scissors")
        self.wind.resizable(1, 1)

        # main frame
        frame = LabelFrame(self.wind, text='This is a "Rock - Paper - Scissors" game!', font=('Helvetica', 16, 'bold'))
        frame.grid(row=0, column=0, columnspan=3, pady=20, sticky=W+E)


        # self.game = Label(frame, text="Rock, Paper, Scissors...your call!!", font=('Calibri', 13))
        # self.game.grid(row=0, column=0, sticky=W)

        # label name
        self.label_name = Label(frame, text='Enter your name...', font=('Calibri', 13))
        self.label_name.grid(row=1, column=0, sticky=W)
        self.name = Entry(frame, font=('Calibri', 13))
        self.name.focus()
        self.name.grid(row=1, column=1)

        # label choice
        self.label_choice = Label(frame, text='Your choice...', font=('Calibri', 13))
        self.label_choice.grid(row=2, column=0, sticky=W)

        cat = tk.StringVar()
        self.input_choice = ttk.Combobox(frame, width=18, textvariable=cat, state="readonly")
        self.input_choice['values'] = ['Rock',
                                       'Paper',
                                       'Scissors']
        self.input_choice.grid(row=2, column=1)

        # button
        s = ttk.Style()
        s.configure('my.TButton', font=('Calibri', 14, 'bold'))
        button_play = ttk.Button(text='PLAY', command=self.play, style='my.TButton')
        button_play.grid(row=3, columnspan=3, sticky=W + E)

        # message
        self.message = Label(text='', fg='red')
        self.message.grid(row=4, columnspan=3, sticky=W + E)

    # users choice cannot be empty
    def validation_name(self):
        users_name = self.name.get()
        return len(users_name) !=0

    # users choice cannot be empty
    def validation_choice(self):
        users_choice = self.input_choice.get()
        return len(users_choice) !=0

    def play(self):
        self.choose = ['Rock', 'Paper', 'Scissors']
        m_choice = random.choice(self.choose)
        # print('computer '+m_choice)
        # print(self.input_choice.get())
        if self.validation_name() and self.validation_choice() and (self.input_choice.get() == m_choice):
            #print('It is a draw')
            self.message['text'] = 'It is a draw'
        elif self.validation_name() == False and self.validation_choice() == False:
            self.message['text'] = 'Name and choice cannot be empty'
        elif self.validation_name() == False and self.validation_choice():
            self.message['text'] = 'Name cannot be empty'
        elif self.validation_name() and self.validation_choice() == False:
            self.message['text'] = 'You must choose something ' +self.name.get()
        elif self.input_choice.get() == 'Rock' and m_choice == 'Paper':
            self.message['text'] = 'I have paper, I win!!'
        elif self.input_choice.get() == 'Rock' and m_choice == 'Scissors':
            self.message['text'] = 'I have scissors, '+self.name.get()+' wins!!'
        elif self.input_choice.get() == 'Paper' and m_choice == 'Rock':
            self.message['text'] = 'I have rock, '+self.name.get()+' wins!!'
        elif self.input_choice.get() == 'Paper' and m_choice == 'Scissors':
            self.message['text'] = 'I have scissors, I win!!'
        elif self.input_choice.get() == 'Scissors' and m_choice == 'Paper':
            self.message['text'] = 'I have paper, '+self.name.get()+' wins!!'
        elif self.input_choice.get() == 'Scissors' and m_choice == 'Rock':
            self.message['text'] = 'I have rock, I win!!'

if __name__ == '__main__':
    root = Tk()
    rocks = RPS(root)
    root.mainloop()

