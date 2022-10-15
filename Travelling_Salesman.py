import random
import math
import tkinter
import matplotlib.pyplot as plt
import numpy as np
from tkinter import *
from tkinter import Tk, Label, Button
from PIL import Image, ImageTk
from matplotlib.animation import FuncAnimation
from gurobipy import Model, GRB, quicksum


#### index of the line to animate ####
current_line = 0
#### draw the current line up to the point of this index ####
up_to_point = 1


def plotting():
    plt.plot(xc[0], yc[0], 'r', marker='s')
    for i in N:
        if q[i] > 0:
            plt.scatter(xc[i], yc[i], c='b', s=100 * math.sqrt(q[i]) / 5)
        else:
            plt.scatter(xc[i], yc[i], c='y', s=100 * math.sqrt(abs(q[i])) / 5)


def generate_packs():
    global panel_image, display, N, q, xc, yc, n, packs
    integer = True

    #### Definiowanie danych początkowych ####
    a = input_panel.get()
    try:
        n = int(a)
    except ValueError:
        print(a, "is not a number")
        integer = False

    if integer is False:
        input_text.configure(foreground='red', text='Podaj poprawną\nliczbę paczek!', font=('times', 20, 'bold'))
        input_text.place(x=1015, y=50)
    else:
        input_text.configure(foreground='black', font=('times', 18, 'bold'), text="Podaj ilość paczek")
        input_text.place(x=1015, y=80)
        panel1.configure(state=DISABLED)
        panel2.configure(state=NORMAL)
        rnd = np.random
        # rnd.seed(0)
        xc = rnd.rand(n + 1) * 200
        yc = rnd.rand(n + 1) * 100
        xc[0] = 100
        yc[0] = 50

        N = [i for i in range(1, n + 1)]

        if delivery_status():
            q = {i: rnd.randint(1, 10) for i in N}
        else:
            q = {i: random.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) for i in N}

        plotting()
        plt.xlim(0, 200)
        plt.ylim(0, 100)
        plt.savefig('Packs.jpg')
        plt.clf()

        image = Image.open('Packs.jpg')
        display = ImageTk.PhotoImage(image)
        panel_image = Label(root, image=display)
        panel_image.pack()


def travel():
    global display2, final_arcs, panel_image2

    V = [0] + N
    E = [(i, j) for i in V for j in V if i != j]
    c = {(i, j): np.hypot(xc[i] - xc[j], yc[i] - yc[j]) for i, j in E}
    Q = 30

    #### Obliczanie trasy CVRP ####

    mdl = Model('CVRP')

    x = mdl.addVars(E, vtype=GRB.BINARY)
    u = mdl.addVars(N, vtype=GRB.CONTINUOUS)

    mdl.modelSense = GRB.MINIMIZE
    mdl.setObjective(quicksum(x[i, j] * c[i, j] for i, j in E))

    mdl.addConstrs(quicksum(x[i, j] for j in V if j != i) == 1 for i in N)
    mdl.addConstrs(quicksum(x[i, j] for i in V if i != j) == 1 for j in N)
    mdl.addConstrs((x[i, j] == 1) >> (u[i] + q[j] == u[j])
                   for i, j in E if i != 0 and j != 0)
    mdl.addConstrs(u[i] >= q[i] for i in N)
    mdl.addConstrs(u[i] <= Q for i in N)

    mdl.Params.MIPGap = 0.1
    mdl.Params.TimeLimit = 30  # seconds
    mdl.optimize()

    #### Trasy, które musi pokonać samochód są zapisywane do "active_arcs" ####

    active_arcs = [a for a in E if x[a].x > 0.99]

    #### Sortowanie ścieżek ####

    final_arcs = []
    roads = 0
    temp_j = 0
    while len(active_arcs) != 0:
        temp_arcs = [active_arcs[0]]
        for i, j in temp_arcs:
            temp_j = j

        i2 = 0
        while temp_j != 0:
            for i, j in active_arcs:
                if temp_j == i and temp_j != 0:
                    temp_arcs.append(active_arcs[i2])
                    temp_j = j
                i2 += 1
            i2 = 0

        i = 0
        while i < len(temp_arcs):
            i2 = 0
            while i2 < len(active_arcs):
                if temp_arcs[i] == active_arcs[i2]:
                    active_arcs.pop(i2)
                i2 += 1
            i += 1

        final_i = 0
        while final_i < len(temp_arcs):
            final_arcs.append(temp_arcs[final_i])
            final_i += 1
        roads += 1

    panel_image.destroy()

    tmp = 0
    plotting()
    plt.xlim(0, 200)
    plt.ylim(0, 100)
    for i, j in final_arcs:
        plt.plot([xc[i], xc[j]], [yc[i], yc[j]], colors_base[tmp], zorder=0)
        if j == 0 and tmp < len(colors_base):
            tmp += 1
    plt.savefig('Routes.jpg')
    plt.clf()
    image2 = Image.open('Routes.jpg')
    display2 = ImageTk.PhotoImage(image2)
    panel_image2 = Label(root, image=display2)
    panel_image2.pack()
    panel2.configure(state=DISABLED)
    panel3.configure(state=NORMAL)


def animation():
    global panel_animation1, panel_animation, display_gif, frames, frameCnt
    gif_creation()
    panel_image2.destroy()
    frames = []
    frameCnt = len(final_arcs) + 1

    with Image.open('animation.gif') as im:
        for i in range(frameCnt):
            im.seek(i)
            im.save('frames/Frame' + str(i) + '.png')

    panel_animation = Label(root)
    panel_animation.pack()
    root.after(0, sequence, 0)
    panel3.configure(state=DISABLED)


def sequence(ind):
    global frame
    img = Image.open('frames/Frame' + str(ind) + '.png')
    frame = ImageTk.PhotoImage(img)
    ind += 1
    if ind == frameCnt:
        ind = 0
    panel_animation.configure(image=frame)
    root.after(600, sequence, ind)


def gif_creation():
    global lines_data, lines

    fig, ax = plt.subplots()
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 100)

    plotting()

    # precompute each line coordinates
    lines_data = []
    xd, yd = [], []
    for i, j in final_arcs:
        xd.append(xc[i])
        yd.append(yc[i])
        if j == 0:
            xd.append(xc[0])
            yd.append(yc[0])
            lines_data.append([xd, yd])
            xd, yd = [], []

    # add empty lines with the specified colors
    lines = []
    for i in range(len(lines_data)):
        lines.append(ax.plot([], [], color=colors_base[i])[0])

    #### Zapisywanie GIFu ####
    ani = FuncAnimation(fig, update, frames=len(final_arcs) + 1, interval=100)
    ani.save('animation.gif', fps=2)
    plt.clf()


def update(p):
    global current_line, up_to_point
    if p != 0:
        # reset after each animation cycle is complete
        if current_line > len(lines_data) - 1:
            current_line = 0
            for l in lines:
                l.set_data([], [])

        up_to_point += 1
        xd, yd = lines_data[current_line]
        lines[current_line].set_data(xd[:up_to_point], yd[:up_to_point])
        if len(xd[:up_to_point]) == len(xd):
            current_line += 1
            up_to_point = 1


def simpletoggle():
    if toggle_button.config('text')[-1] == 'Dostarczanie':
        toggle_button.config(text='Odbieranie/\nDostarczanie')
    else:
        toggle_button.config(text='Dostarczanie')


def delivery_status():
    if toggle_button.config('text')[-1] == 'Dostarczanie':
        delivery = True
    else:
        delivery = False
    return delivery


def reset():
    panel1.configure(state=NORMAL)
    panel2.configure(state=DISABLED)
    panel3.configure(state=DISABLED)
    panel_image.destroy()
    panel_image2.destroy()
    panel_animation.destroy()


####### MAIN ########

root = Tk()
root.title("Komiwojażer")
root.geometry("1240x560")
root.iconbitmap('./meta/Icon_bus.ico')

im = Image.open('./meta/Delivery_bus.png')
im = im.resize((300, 233), Image.ANTIALIAS)
wp_img = ImageTk.PhotoImage(im)
panel_bus = Label(root, image=wp_img)
panel_bus.place(x=0, y=100)

colors_base = ['g', 'r', 'cyan', 'black', 'orange', 'm', 'darkorchid',
               'dimgray', 'indigo', 'lawngreen', 'darkred']
text_label = Label(root, font=('times', 26, 'bold'), text="System obliczający trasę przejazdu kuriera")
text_label.pack()

input_text = Label(root, font=('times', 18, 'bold'), text="Podaj ilość paczek")
input_text.place(x=1015, y=80)

input_panel = tkinter.Entry(root, width=13, font=('times', 24))
input_panel.place(x=1004, y=120)

panel1 = Button(root, text='Wygeneruj paczki', command=lambda: generate_packs(), width=15, borderwidth=2,
                bg='gray', fg='black', font=('times', 18, 'bold'))
panel1.place(x=1000, y=200)

panel2 = Button(root, text='Oblicz trasy', command=lambda: travel(), width=15, borderwidth=2,
                bg='gray', fg='black', font=('times', 18, 'bold'), state=DISABLED)
panel2.place(x=1000, y=250)

panel3 = Button(root, text='GIF', command=lambda: animation(), width=15, borderwidth=2,
                bg='gray', fg='black', font=('times', 18, 'bold'), state=DISABLED)
panel3.place(x=1000, y=300)

toggle_button = Button(text="Dostarczanie", command=simpletoggle, width=15, borderwidth=2,
                       bg='gray', fg='black', font=('times', 18, 'bold'))
toggle_button.place(x=40, y=420)

toggle_text = Label(root, font=('times', 18, 'bold'), text="Wybierz rodzaj usługi")
toggle_text.place(x=36, y=380)

panel_reset = Button(root, text='Reset', command=lambda: reset(), width=15, borderwidth=2,
                     bg='gray', fg='black', font=('times', 18, 'bold'))
panel_reset.place(x=1000, y=450)

root.mainloop()