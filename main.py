import numpy as np
import random

from matplotlib.figure import Figure

import base64
from io import BytesIO
from flask import Flask, request, render_template

app = Flask(__name__)


# Parametry równania
alpha = 0.01
R0 = 0.4 # Początkowe natężenie   # do znaleziena czy dobrze
k = 0.0005

# Warunki poczatkowe
I0 = 0.0
t0 = 0.0
dt = 0.1  # krok czasu

emptying_interval = 600  # okres opróżniania pojemnika
max_weight = 25.0  # maksymalna pojemność pojemnika
refill_threshold = 5.0  # próg uzupełnienia pojemnika

emptying_intensity = 300  # natężenie opróżniania pojemnika 3kilo/sekunda

# Funkcja opisująca natężenie paszy dostarczanej z pojemnika głównego
def R(t):   # Kilo/sekunde
    return R0 * np.exp(-k * t)

# Funkcja opróżniająca pojemnik
def emptying(I_value, t):
    if t > 0 and I_value > 0:
        emptying_amount = min(emptying_intensity * dt, I_value)
        return I_value - emptying_amount
    else:
        return I_value

# Rozwiązanie równania różniczkowego 
def solve_differential_equation_refill(I_value, t):

    # Równania różniczkowe
    dI_dt = R(t) - alpha * I_value
    I_new = I_value + dt * dI_dt

    return I_new

# Symulacja dozownika
def run_dozownik(pig_number, pig_weight, T):
    
    ammount_to_eat = float(pig_weight) * 0.04 * pig_number

    time_points = np.arange(t0, T, dt)
    I_values = [I0]
    state_of_emptying = False
    state_of_refilling = False
    is_eating = False
    time_of_refilling = 0
    probability_of_truth = 10

    for i, t in enumerate(time_points):

        if t > 0:

            # symulacja jedzących świń
            los = random.uniform(0,100)
            if los < probability_of_truth:
                time_of_eat_random =random.uniform(30, 120)
                eating_per_interval = ammount_to_eat * 2 * (dt / time_of_eat_random)
                ammount_ate = random.uniform(0, eating_per_interval)
                I_value = I_values[-1] - ammount_ate
                is_eating = True
            elif is_eating and I_values[-1] > 0:
                ammount_ate += random.uniform(0, eating_per_interval)
                I_value = max(0, I_values[-1] - ammount_ate)
                if ammount_ate >= ammount_to_eat:
                    is_eating = False

            # Opróżnianie
            if t % emptying_interval == 0 or state_of_emptying:
                I_value = emptying(I_values[-1], t)
                state_of_emptying = True
                if I_value == 0:
                    state_of_emptying = False

            # Napełnianie gdy waga karmy spadnie poniżej określonej wartości
            elif I_values[-1] <= refill_threshold or state_of_refilling:
                if state_of_refilling == False:
                    time_of_refilling = 0
                if I_values[-1] < max_weight:
                    I_value = solve_differential_equation_refill(I_values[-1], time_of_refilling)
                    state_of_refilling = True
                else:
                    I_value = I_values[-1]
                    state_of_refilling = False
                time_of_refilling += dt

            I_values.append(I_value)

    return time_points, I_values


@app.route("/", methods=['POST'])
def form():
    pig_number = int(request.form['pig_number'])
    pig_weight = int(request.form['pig_weight'])
    time = int(request.form['time'])
    return web(pig_number, pig_weight, time)



@app.route("/", methods=["GET"])
def web(pig_number = 2, pig_weight = 50, T = 1200):
    # Wykres
    fig = Figure()
    ax = fig.subplots()
    time, pasza_w_dozowniku = run_dozownik(pig_number, pig_weight, T)
    ax.plot(time, pasza_w_dozowniku, label='Ilość karmy w pojemniku')

    ax.set_xlabel('Czas [sekundy]')
    ax.set_ylabel('Waga karmy [kilogramy]')
    ax.set_title('Symulacja zachowania dozownika w czasie {} sekund'.format(T))

    buf = BytesIO()
    fig.savefig(buf, format="png")
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return render_template('index.html', data=data, pig_number=pig_number, pig_weight=pig_weight, T=T)
