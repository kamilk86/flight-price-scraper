import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib import style
import tkinter as tk
import matplotlib.animation as animation
import json
import seaborn as sns
from random import randrange
import datetime
import socket
import time


"""TO DO: add clear button for track trip"""


with open('trip_ids.json', 'r') as f:
    trip_ids = json.load(f)

with open('db.json', 'r') as f:
    db = json.load(f)


class ScraperClientApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self)

        self.ip = kwargs.pop('ip', None)
        self.port = kwargs.pop('port', None)
        self.req_proc_id = None
        self.update_proc_id = None
        container = tk.Frame(self)
        container.grid()

        if not self.ip or not self.port:
            print('Missing arguments: IP, PORT')
            return

        self.geometry('1100x850')
        self.frames = {}
       
        for F in (OptionsPane, PlotPane):
            frame = F(container, self)
            self.frames[F] = frame

        # Server performing data scrapring
        self.busy_times = {'05:00', '05:01', '05:02', '05:03', '05:04', '05:05', '11:00', '11:01', '11:02', '11:03',
                           '11:04', '11:05', '17:00', '17:01', '17:02', '17:03', '17:04', '17:05', '23:00', '23:01',
                           '23:02', '23:03', '23:04', '23:05'}

        self.var_status_msg = tk.StringVar()
        self.status_bar = tk.Label(
            self, textvariable=self.var_status_msg, relief=tk.SUNKEN, anchor=tk.W, font=('Calibri', 12))
        self.status_bar.grid(row=1, columnspan=2, sticky='we')

        self.menu = tk.Menu(self)
        self.config(menu=self.menu)
        self.subMenu = tk.Menu(tearoff=False)
        self.menu.add_cascade(label='File', menu=self.subMenu)
        self.subMenu.add_command(label='Quit', command=self.quit_client)

        self.update_trips()

    @staticmethod
    def ids_local_update():
        with open('trip_ids.json', 'w') as f:
            json.dump(trip_ids, f, indent=1)

    @staticmethod
    def db_local_update():
        with open('db.json', 'w') as f:
            json.dump(db, f, indent=1)

    def get_pane(self, pane_class):
        return self.frames[pane_class]

    def update_status(self, status):
        self.var_status_msg.set(' ' + status)

    def quit_client(self):
        if self.req_proc_id:
            self.after_cancel(self.req_proc_id)
        self.after_cancel(self.update_proc_id)
        self.destroy()
        exit()

    def update_trips(self):

        plots = self.get_pane(PlotPane)
        req = ['update']
        self.send_request(req)
        
        plots.update_plots()
        self.db_local_update()
        self.update_proc_id = self.after(300000, self.update_trips)

    def track_trip(self, options):
        # send request to create new trip
        plots = self.get_pane(PlotPane)
        opt_pane = self.get_pane(OptionsPane)
        i = 1
        while i in trip_ids:
            i += 1
        options['trip_id'] = i
        self.send_request([options])
        trip_ids.insert(i - 1, i)
        db.append(options)
        self.ids_local_update()
        self.db_local_update()
        plots.update_plots()
        opt_pane.update_ids_menu()
        opt_pane.display_msg('Added New Trip with ID: ' +
                             str(options['trip_id']))

    def remove_trip(self):
        plots = self.get_pane(PlotPane)
        opt_pane = self.get_pane(OptionsPane)
        trip_id = opt_pane.var_trip_id.get()
        if len(trip_id) < 2 and int(trip_id) in trip_ids:
            req = [{'remove': trip_id}]
            self.send_request(req)
            self.remove_local_record(int(trip_id))
            plots.update_plots()
            opt_pane.update_ids_menu()

    def send_request(self, req):
        global db
        buff_size = 4096
        now = str(datetime.datetime.now()).split(' ')[1][:5]

        if now in self.busy_times:
            self.req_proc_id = self.after(350000, self.send_request, req)
            self.update_status(
                'Server is busy. Database Update request rescheduled in 6min.')
        else:
            if self.req_proc_id:
                self.after_cancel(self.update_proc_id)
            self.update_status('Updating database...')
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                soc.connect((self.ip, self.port))
            except ConnectionRefusedError:
                print("Server Socket: Connection Refused")
                return

            soc.sendall(json.dumps(req).encode())
            data = b''
            while True:
                part = soc.recv(buff_size)
                data += part
                if len(part) < buff_size:
                    break
            self.update_status('Last updated: ' + now)

            db = json.loads(data.decode())
            return

    def remove_local_record(self, trip_id):
        if trip_id in trip_ids:
            trip_ids.remove(trip_id)
            record = next(
                (rec for rec in db if rec['trip_id'] == trip_id), None)
            if record:
                db.remove(record)
            self.ids_local_update()
            self.db_local_update()
            options_pane = self.get_pane(OptionsPane)
            options_pane.display_msg(
                'Removed Trip record with ID: ' + str(trip_id))
        return


class OptionsPane(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.controller = controller
        self.config(height='800', width='300', bg='powder blue')
        self.grid_propagate(0)
        self.grid(row=0, column=0, padx=10, pady=10)

        self.lbl_main = tk.Label(
            self, text='Track Trip', font=('Arial', 14), bg='powder blue')
        self.lbl_main.grid(row=0, columnspan=2, pady=2)

        self.var_airline = tk.StringVar(self)
        self.var_airline.set('Choose Airline')
        self.menu_airline = tk.OptionMenu(
            self, self.var_airline, 'Choose Airline', 'Easyjet', 'Ryanair')
        self.menu_airline.grid(row=1, columnspan=2)

        self.one_way = tk.IntVar()
        self.check_way = tk.Checkbutton(self, text='One Way', variable=self.one_way, onvalue=1,
                                        offvalue=0, height=2, width=8, bg='powder blue', command=self.one_way_check)
        self.check_way.grid(row=2, columnspan=2)

        # Source City
        self.lbl_src_city = tk.Label(
            self, text='Source City', bg='powder blue')
        self.lbl_src_city.grid(row=3, column=0, pady=2, sticky='e')

        self.var_src_city = tk.StringVar(self)
        self.var_src_city.set('Edinburgh')
        self.menu_src_city = tk.OptionMenu(
            self, self.var_src_city, 'Krakow', 'Edinburgh')
        self.menu_src_city.config(width=10)
        self.menu_src_city.grid(row=3, column=1, pady=2)

        # Destination city
        self.lbl_dst_city = tk.Label(
            self, text='Destination City', bg='powder blue')
        self.lbl_dst_city.grid(row=4, column=0, pady=2, sticky='e')

        self.var_dst_city = tk.StringVar(self)
        self.var_dst_city.set('Krakow')
        self.menu_dst_city = tk.OptionMenu(
            self, self.var_dst_city, 'Krakow', 'Edinburgh')
        self.menu_dst_city.config(width=10)
        self.menu_dst_city.grid(row=4, column=1, pady=2)

        # Outbound date
        self.lbl_to_date = tk.Label(self, text='To Date', bg='powder blue')
        self.lbl_to_date.grid(row=5, column=0,  sticky='e')
        self.inp_to_date = tk.Entry(self, width=15)
        self.inp_to_date.grid(row=5, column=1, padx=5, pady=2)

        self.lbl_back_date = tk.Label(
            self, text='Return Date', bg='powder blue')
        self.lbl_back_date.grid(row=6, column=0, sticky='e')
        self.inp_back_date = tk.Entry(self, width=15)
        self.inp_back_date.grid(row=6, column=1, padx=5, pady=2)

        self.btn_add_adult = tk.Button(
            self, text='Adult', command=self.add_adult)
        self.btn_add_adult.grid(row=7, column=0, padx=5, pady=5, sticky='e')
        self.num_adults = tk.IntVar()
        self.num_adults.set(1)
        self.lbl_num_adults = tk.Label(
            self, textvariable=self.num_adults, font=('Arial', 14), bg='powder blue')
        self.lbl_num_adults.grid(
            row=7, column=1, sticky='news', padx=5, pady=5)

        self.btn_add_child = tk.Button(
            self, text='Child', command=self.add_child)
        self.btn_add_child.grid(row=8, column=0, padx=5, pady=5, sticky='e')
        self.num_child = tk.IntVar()
        self.num_child.set(0)
        self.lbl_num_child = tk.Label(
            self, textvariable=self.num_child, font=('Arial', 14), bg='powder blue')
        self.lbl_num_child.grid(row=8, column=1, sticky='news', padx=5, pady=5)

        self.btn_add_trip = tk.Button(
            self, text='Add Trip', command=self.add_trip)
        self.btn_add_trip.grid(row=9, columnspan=2, padx=5, pady=5)

        self.lbl_separator = tk.Label(
            self, text='---------------------------------------------------------', bg='powder blue')
        self.lbl_separator.grid(row=10, columnspan=3)

        self.lbl_db_controls = tk.Label(
            self, text='Trip Settings', font=('Arial', 14), bg='powder blue')
        self.lbl_db_controls.grid(row=11, columnspan=2)

        self.btn_update_trips = tk.Button(
            self, text='Sync Data', width=10, command=self.controller.update_trips)
        self.btn_update_trips.grid(row=12, column=0, padx=5, pady=5)

        self.btn_remove_trip = tk.Button(
            self, text='Remove Trip', width=15, command=self.controller.remove_trip)
        self.btn_remove_trip.grid(row=13, column=0, padx=5, pady=5)

        self.var_trip_id = tk.StringVar(self)
        self.ids_lst = trip_ids[:]
        self.ids_lst.insert(0, 'Select ID')
        self.var_trip_id.set(self.ids_lst[0])
        self.menu_curr_ids = tk.OptionMenu(
            self, self.var_trip_id, *self.ids_lst, command=self.show_trip_details)
        self.menu_curr_ids.config(width=10)
        self.menu_curr_ids.grid(row=13, column=1, pady=5)

        self.lbl_info = tk.Label(self, text='Info', font=(
            'Calibri', 12), bg='powder blue')
        self.lbl_info.grid(row=14, columnspan=2, padx=5, pady=(20, 1))
        self.out_info = tk.Text(self, state='disabled', width=25, height=15,
                                wrap=tk.WORD, bg='gainsboro', borderwidth=2, relief='groove')
        self.out_info.grid(row=15, columnspan=2, padx=5, pady=5)

    def add_adult(self):
        num = self.num_adults.get()
        num += 1
        self.num_adults.set(num)

    def add_child(self):
        num = self.num_child.get()
        num += 1
        self.num_child.set(num)

    def show_trip_details(self, selected):

        if isinstance(selected, int):

            rec = next((t for t in db if t['trip_id'] == selected))
            msg = f"ID: {rec['trip_id']}\nAirline: {rec['airline']}\nSource: {rec['src_city']}\nDestination: {rec['dst_city']}\nDate Out: {rec['to_date']}\nReturn Date: {rec['back_date']}"
            self.display_msg(msg)

    def update_ids_menu(self):
        self.ids_lst = trip_ids[:]
        self.ids_lst.insert(0, 'Select ID')
        menu = self.menu_curr_ids['menu']
        menu.delete(0, 'end')
        for id in self.ids_lst:
            menu.add_command(
                label=id, command=lambda value=id: self.var_trip_id.set(value))

    def one_way_check(self):
        if self.one_way.get():
            self.inp_back_date.configure(state='disabled')
        else:
            self.inp_back_date.configure(state='normal')

    def add_trip(self):
        options = {
            'trip_id': None,
            'one_way': False,
            'adult': self.num_adults.get(),
            'child': self.num_child.get(),
            'airline': self.var_airline.get(),
            'src_city': self.var_src_city.get(),
            'dst_city': self.var_dst_city.get(),
            'to_date': self.inp_to_date.get(),
            'back_date': self.inp_back_date.get(),
            'trip_data': {'to': {}, 'back': {}}

        }
        if self.one_way.get():
            options['one_way'] = True
            options['back_date'] = None
            options['trip_data'] = {'to': {}}

        self.controller.track_trip(options)

    def display_msg(self, msg):

        self.out_info.configure(state='normal')
        self.out_info.delete(1.0, tk.END)
        self.out_info.insert(tk.END, msg, '\n')
        self.out_info.configure(state='disabled')


class PlotPane(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.grid_propagate(0)
        self.controller = controller
        self.config(height='800', width='750', bg='linen')
        self.grid(row=0, column=1, padx=10, pady=10)

        self.subplots = {}
        #self.update_plots()

    def update_plots(self):
        self.subplots = {}
        plt.close('all')
        sns.set_style('darkgrid', {'axes.linewidth': 1, 'axes.edgecolor': 'black'})
        
        fig = plt.figure(figsize=(9, 10), dpi=80, facecolor='gainsboro')

        for i in range(len(db)):
            sub_plot_num = str(len(db)) + '1' + str(i + 1)
            ax = fig.add_subplot(int(sub_plot_num))
            self.subplots['ax' + str(i)] = ax
        fig.set_tight_layout(True)
        # plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.2, hspace=0.2)
        canvas = FigureCanvasTkAgg(fig, self)
        
        self.populate_figs()
        before = datetime.datetime.now()
    
        canvas.draw()
        after = datetime.datetime.now()
        print(" it took: ", after - before)
        canvas.get_tk_widget().grid(row=0, column=0)

    @staticmethod
    def determine_label(y, city):
        if y:
            if y[-1] == 0:
                lbl = f"to {city} Price: SOLD OUT"
            elif len(y) > 1:
                if y[-1] > y[-2]:
                    lbl = f"to {city} Price: {y[-1]} +{(y[-1]-y[-2])/y[-2]*100:.1f}%"
                elif y[-1] < y[-2]:
                    lbl = f"to {city} Price: {y[-1]} -{(y[-2] - y[-1])/y[-2] * 100:.1f}%"
                else:
                    lbl = f"to {city} Price: {y[-1]} +0%"
            else:
                    lbl = f"to {city} Price: {y[-1]} +0%"
        else:
            lbl = f"to {city} curr. price: None"

        return lbl

    def get_x_labels(self, x_data):
        # Creates array of labels showing every nth label depending on x data length. PRevents overlapping of labels
        x_labels = []
        if len(x_data) > 30 and len(x_data) < 100:
            show_every = 5
        elif len(x_data) > 100:
            show_every = 10

        ctr = 0
        for lbl in x_data:
            ctr += 1
            if ctr == show_every:
                x_labels.append(lbl)
                ctr = 0
            else:
                x_labels.append("")
                
        return x_labels

    def populate_figs(self):

        for idx, trip in enumerate(db):
            xs = []
            ys = []
            xs2 = []
            ys2 = []
            x_labels = []

            if trip['one_way']:
               
                for item in trip['trip_data']['to'].items():
                    xs.append(item[0])
                    ys.append(item[1])

                ax = self.subplots['ax' + str(idx)]
                ax.clear()
                title = f"Airline: {trip['airline']} Out: {trip['to_date']} Back: 'One way' ID: {trip['trip_id']}"
                ax.set_title(title, fontweight='bold', size=12)
                ax.set_xlabel('Date')
                ax.set_ylabel('Price £')
              
                lbl = self.determine_label(ys, trip['dst_city'])

                ax.plot(xs, ys, color='dodgerblue', label=lbl, marker='o')
                ax.legend(loc='upper left')

                x_labels = self.get_x_labels(xs)
                ax.set_xticklabels(x_labels, rotation=45)

            if not trip['one_way']:
                
                for item in trip['trip_data']['to'].items():
                    xs.append(item[0])
                    ys.append(item[1])

                for item in trip['trip_data']['back'].items():
                    xs2.append(item[0])
                    ys2.append(item[1])

                ax = self.subplots['ax' + str(idx)]
                ax.clear()
                title = f"Airline: {trip['airline']} Out: {trip['to_date']} Back: {trip['back_date']} ID: {trip['trip_id']}"
                ax.set_title(title, fontweight='bold', size=12)
                ax.set_xlabel('Date')
                ax.set_ylabel('Price £')
                lbl1 = self.determine_label(ys, trip['dst_city'])
                lbl2 = self.determine_label(ys, trip['src_city'])

            

                ax.plot(xs, ys, color='dodgerblue', label=lbl1, marker='o')
                ax.plot(xs2, ys2, color='darkorange', label=lbl2, marker='o')
                ax.legend(loc='upper left')
                
                x_labels = self.get_x_labels(xs)
                ax.set_xticklabels(x_labels, rotation=45)



def main():

    app = ScraperClientApp(ip='127.0.0.1', port=64535)
    app.mainloop()


if __name__ == '__main__':
    main()
