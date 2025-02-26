from flask import Flask, render_template, request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dasa_date_adjuster import adjust_dasa_start_date  # import from separate module

app = Flask(__name__)

# Define the Vimshottari Dasha periods (in years) in cyclic order.
dasha_periods = [
    ("Sun", 6),
    ("Moon", 10),
    ("Mars", 7),
    ("Rahu", 18),
    ("Jupiter", 16),
    ("Saturn", 19),
    ("Mercury", 17),
    ("Ketu", 7),
    ("Venus", 20)
]

# Helper function to format durations.
def format_duration(duration_in_months):
    if duration_in_months < 1:
        days = duration_in_months * 30.44
        return f"{days:.2f} days"
    else:
        return f"{duration_in_months:.2f} months"

app.jinja_env.filters['format_duration'] = format_duration

def generate_full_dasha_chart(birth_date, present_date, current_dasa, lifespan=120):
    age = present_date.year - birth_date.year
    future_years = lifespan - age

    current_index = next((i for i, (planet, _) in enumerate(dasha_periods)
                          if planet.lower() == current_dasa.lower()), None)
    if current_index is None:
        raise ValueError("Current Dasa not found in the list.")

    future_chart = []
    remaining_future = future_years
    dt = present_date
    idx = current_index
    while remaining_future > 0:
        planet, full_duration = dasha_periods[idx]
        duration = full_duration if full_duration <= remaining_future else remaining_future
        dt_end = dt.replace(year=dt.year + duration)
        future_chart.append((planet,
                             dt.strftime('%d-%m-%Y (%H:%M:%S)'),
                             dt_end.strftime('%d-%m-%Y (%H:%M:%S)'),
                             duration))
        dt = dt_end
        remaining_future -= duration
        idx = (idx + 1) % len(dasha_periods)

    past_chart_reversed = []
    remaining_past = age
    dt = present_date
    idx = (current_index - 1) % len(dasha_periods)
    while remaining_past > 0:
        planet, full_duration = dasha_periods[idx]
        duration = full_duration if full_duration <= remaining_past else remaining_past
        dt_start = dt.replace(year=dt.year - duration)
        past_chart_reversed.append((planet,
                                    dt_start.strftime('%d-%m-%Y (%H:%M:%S)'),
                                    dt.strftime('%d-%m-%Y (%H:%M:%S)'),
                                    duration))
        dt = dt_start
        remaining_past -= duration
        idx = (idx - 1) % len(dasha_periods)
    past_chart = list(reversed(past_chart_reversed))
    full_chart = past_chart + future_chart
    return full_chart, past_chart, future_chart

def generate_antardasha(main_planet, main_duration_years, main_start_date):
    antardasha_chart = []
    start_index = next((i for i, (planet, _) in enumerate(dasha_periods)
                        if planet.lower() == main_planet.lower()), 0)
    current_dt = main_start_date
    for i in range(len(dasha_periods)):
        planet, p2_duration = dasha_periods[(start_index + i) % len(dasha_periods)]
        antardasha_duration_months = (main_duration_years * p2_duration) / 10.0
        days_to_add = antardasha_duration_months * 30.44
        new_end = current_dt + timedelta(days=days_to_add)
        antardasha_chart.append((f"{main_planet}-{planet}",
                                  current_dt.strftime('%d-%m-%Y (%H:%M:%S)'),
                                  new_end.strftime('%d-%m-%Y (%H:%M:%S)'),
                                  antardasha_duration_months))
        current_dt = new_end
    return antardasha_chart

def generate_pratyantara_dasa(antardasha_full_name, antardasha_duration_months, antardasha_start_date):
    total_days = antardasha_duration_months * 30.44
    base_planet = antardasha_full_name.split('-')[-1]
    start_index = next((i for i, (planet, _) in enumerate(dasha_periods)
                        if planet.lower() == base_planet.lower()), 0)
    sub_durations = []
    for i in range(len(dasha_periods)):
        _, p2_duration = dasha_periods[(start_index + i) % len(dasha_periods)]
        d = (p2_duration / 120.0) * total_days
        sub_durations.append(d)
    diff = total_days - sum(sub_durations)
    sub_durations[-1] += diff
    pratyantara_chart = []
    current_dt = antardasha_start_date
    for i in range(len(dasha_periods)):
        planet, _ = dasha_periods[(start_index + i) % len(dasha_periods)]
        name = f"{antardasha_full_name}-{planet}"
        d = sub_durations[i]
        duration_months = d / 30.44
        new_end = current_dt + timedelta(days=d)
        pratyantara_chart.append((name,
                                   current_dt.strftime('%d-%m-%Y (%H:%M:%S)'),
                                   new_end.strftime('%d-%m-%Y (%H:%M:%S)'),
                                   duration_months))
        current_dt = new_end
    return pratyantara_chart

def generate_sookshma_dasa(pratyantara_full_name, pratyantara_duration_months, pratyantara_start_date):
    total_days = pratyantara_duration_months * 30.44
    base_planet = pratyantara_full_name.split('-')[-1]
    start_index = next((i for i, (planet, _) in enumerate(dasha_periods)
                        if planet.lower() == base_planet.lower()), 0)
    sub_durations = []
    for i in range(len(dasha_periods)):
        _, p2_duration = dasha_periods[(start_index + i) % len(dasha_periods)]
        d = (p2_duration / 120.0) * total_days
        sub_durations.append(d)
    diff = total_days - sum(sub_durations)
    sub_durations[-1] += diff
    sookshma_chart = []
    current_dt = pratyantara_start_date
    for i in range(len(dasha_periods)):
        planet, _ = dasha_periods[(start_index + i) % len(dasha_periods)]
        name = f"{pratyantara_full_name}-{planet}"
        d = sub_durations[i]
        duration_months = d / 30.44
        new_end = current_dt + timedelta(days=d)
        sookshma_chart.append((name,
                               current_dt.strftime('%d-%m-%Y (%H:%M:%S)'),
                               new_end.strftime('%d-%m-%Y (%H:%M:%S)'),
                               duration_months))
        current_dt = new_end
    return sookshma_chart

# ---------------------------
# Route: Dasa Start Date Adjuster
# ---------------------------
@app.route('/dasa_calculator', methods=['GET', 'POST'])
def dasa_calculator():
    if request.method == 'POST':
        given_date_str = request.form['given_date']  # Expected format: YYYY-MM-DD
        current_dasa = request.form['current_dasa']
        pada = request.form['pada']
        try:
            given_date = datetime.strptime(given_date_str, "%Y-%m-%d")
        except ValueError:
            return render_template('error.html', title="Error - Dasa Calculator",
                                   error_message="Invalid date format. Please use YYYY-MM-DD.")
        try:
            new_date = adjust_dasa_start_date(given_date, pada, current_dasa)
        except Exception as e:
            return render_template('error.html', title="Error - Dasa Calculator",
                                   error_message=str(e))
        return render_template('dasa_result.html', title="Dasa Start Date Result",
                               new_date=new_date.strftime('%d-%m-%Y'))
    return render_template('dasa_calculator.html', title="Dasa Start Date Calculator")

# ---------------------------
# Route: Main Dasha Calculator
# ---------------------------
@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        current_date_str = request.form['current_date']  # Format: YYYY-MM-DD
        current_time_str = request.form['current_time']    # Format: HH:MM:SS
        current_dt_str = f"{current_date_str} {current_time_str}"
        try:
            present_date = datetime.strptime(current_dt_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return render_template('error.html', title="Error - Prashna",
                                   error_message="Invalid date/time format. Please check your calendar and clock inputs.")
        age = int(request.form['age'])
        current_dasa = request.form['current_dasa']
        # Default pada to "1" since it's not provided in this form.
        pada = "1"
        
        adjusted_present_date = adjust_dasa_start_date(present_date, pada, current_dasa)
        birth_date = adjusted_present_date.replace(year=adjusted_present_date.year - age)
        full_chart, past_chart, future_chart = generate_full_dasha_chart(birth_date, adjusted_present_date, current_dasa, lifespan=120)
        return render_template('chart.html',
                               title="Dasha Calculator",
                               current_dt=adjusted_present_date.strftime('%d-%m-%Y (%I:%M:%S %p)'),
                               birth_date=birth_date.strftime('%d-%m-%Y (%I:%M:%S %p)'),
                               age=age, current_dasa=current_dasa,
                               past_chart=past_chart, future_chart=future_chart)
    return render_template('index.html', title="Dasha Calculator")



@app.route('/antardasha', methods=['POST'])
def antardasha():
    mahadasha = request.form['mahadasha']
    duration = float(request.form['duration'])
    start_dt_str = request.form['start_dt']
    start_dt = datetime.strptime(start_dt_str, '%d-%m-%Y (%H:%M:%S)')
    antardasha_chart = generate_antardasha(mahadasha, duration, start_dt)
    return render_template('antardasha.html', title=f"Antardasha - {mahadasha}",
                           mahadasha=mahadasha, duration=duration,
                           antardasha_chart=antardasha_chart)

@app.route('/pratyantara', methods=['POST'])
def pratyantara():
    antardasha_name = request.form['antardasha_name']
    duration = float(request.form['duration'])
    start_dt_str = request.form['start_dt']
    start_dt = datetime.strptime(start_dt_str, '%d-%m-%Y (%H:%M:%S)')
    pratyantara_chart = generate_pratyantara_dasa(antardasha_name, duration, start_dt)
    return render_template('pratyantara.html', title=f"Pratyantara - {antardasha_name}",
                           antardasha_name=antardasha_name, duration=duration,
                           pratyantara_chart=pratyantara_chart)

@app.route('/sookshma', methods=['POST'])
def sookshma():
    pratyantara_name = request.form['pratyantara_name']
    duration = float(request.form['duration'])
    start_dt_str = request.form['start_dt']
    start_dt = datetime.strptime(start_dt_str, '%d-%m-%Y (%H:%M:%S)')
    sookshma_chart = generate_sookshma_dasa(pratyantara_name, duration, start_dt)
    return render_template('sookshma.html', title=f"Sookshma - {pratyantara_name}",
                           pratyantara_name=pratyantara_name, duration=duration,
                           sookshma_chart=sookshma_chart)

@app.route('/error')
def error():
    return render_template('error.html', title="Error - Prashna")

@app.route('/home')
@app.route('/')
def home():
    return render_template('home.html', title="Prashna")

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
