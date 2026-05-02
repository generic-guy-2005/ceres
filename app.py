from flask import Flask, render_template, redirect, request, url_for, current_app
from datetime import datetime, time, timezone, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from sqlalchemy import func

import json
import os
import pytz
import platform

app = Flask(__name__)
db_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(db_dir, 'instance', 'management.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(32), nullable=False)
    cost = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(8), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return '<Expense %r' % self.id

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    filetype = db.Column(db.String(20))
    uploaded_at = db.Column(db.DateTime, default=datetime.now)

DATA_FILE = 'settings.json'
UPLOAD_FOLDER = 'static/media'

def get_next():
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    count = Media.query.filter(Media.uploaded_at >= today_start).count()
    return f"{count + 1:03d}"

def load_all_data():
    if not os.path.exists(DATA_FILE):
        return {'cash': 0.0, 'digital': 0.0, 'target': 0.0, 'current': 0.0}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)
    
def save_all_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

@app.template_filter('currency')
def currency_filter(value):
    try:
        value = float(value)
        formatted = "{:,.0f}".format(value)
        return formatted.replace(",", ".")
    except (ValueError, TypeError):
        return "0.00"
    
def sync_time():
    now = datetime.now()
    day_name = now.strftime("%A")
    month_name = now.strftime("%B")
    current_year = now.strftime("%Y")
    today_start = datetime.combine(now.date(), time.min)
    tomorrow_start = today_start + timedelta(days=1)
    return now, day_name, month_name, current_year, today_start, tomorrow_start
    #      [0]  [1]       [2]         [3]           [4]          [5] 
    
def load_target():
    if not os.path.exists(DATA_FILE):
        return 0.0
    
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        return float(data.get('target', 0.0))
    
def load_current():
    if not os.path.exists(DATA_FILE):
        return 0.0
    
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        return float(data.get('current', 0.0))
    
@app.route('/em-update-saving', methods=['GET', 'POST'])    
def update_target():
    target = request.form.get('target', 0)
    current = request.form.get('current', 0)
    data = load_all_data()
    data['target'] = float(target)
    data['current'] = float(current)
    save_all_data(data)
    return redirect('/em-dashboard')
    
def load_digital():
    if not os.path.exists(DATA_FILE):
        return 0.0
    
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        return float(data.get('digital', 0.0))
    
@app.route('/em-update-digital', methods=['GET', 'POST'])    
def update_digital():
    cash = request.form.get('digital', 0)
    data = load_all_data()
    data['digital'] = float(cash)
    save_all_data(data)
    return redirect('/em-dashboard')

def load_cash():
    if not os.path.exists(DATA_FILE):
        return 0.0
    
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        return float(data.get('cash', 0.0))

@app.route('/em-update-cash', methods=['GET', 'POST'])    
def update_cash():
    cash = request.form.get('cash', 0)
    data = load_all_data()
    data['cash'] = float(cash)
    save_all_data(data)
    return redirect('/em-dashboard')

@app.template_filter('ordinal')
def ordinal_filter(n):
    n = int(n)
    if 11 <= n <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"

date_number = ordinal_filter(sync_time()[0].strftime("%d"))

@app.route('/', methods=['GET'])
def index():
    print("Hit")
    return render_template('index.html')

@app.route('/jm-dashboard', methods=['POST', 'GET'])
def journal_dashboard():
    print("Hit")
    return render_template('expense-manage/test.html')

@app.route('/em-dashboard', methods=['POST', 'GET'])
def expense_dashboard():
    print("Hit")
    featured_media = Media.query.filter(Media.uploaded_at >= sync_time()[4], Media.uploaded_at < sync_time()[5]).order_by(Media.uploaded_at.desc()).first()

    if featured_media:
        pass
    else:
        featured_media = None

    cash_value = load_cash()
    cash_value = currency_filter(cash_value)
    digital_value = load_digital()
    digital_value = currency_filter(digital_value)
    target_value = load_target()
    target_value = currency_filter(target_value)
    current_value = load_current()
    current_value = currency_filter(current_value)

    if request.method == "POST":
        expense_item = request.form['name']
        expense_cost = request.form['cost']
        expense_type = request.form['type']
        new_expense = Expense(item = expense_item, cost = expense_cost, type = expense_type)

        try:
            db.session.add(new_expense)
            db.session.commit()
            return redirect('/em-dashboard')
        except:
            return "Data Not Created"
        
    else:
        # expenses = Expense.query.order_by(Expense.date_created).all()
        expenses = Expense.query.filter(Expense.date_created >= sync_time()[4], Expense.date_created < sync_time()[5]).all()
        return render_template(
            'expense-manage/dashboard.html', 
            day_name = sync_time()[1], 
            date_number = date_number, 
            month_name = sync_time()[2], 
            current_year = sync_time()[3], 
            cash = cash_value, 
            digital = digital_value, 
            target = target_value, 
            current = current_value,
            expenses = expenses,
            formatter = currency_filter,
            media = featured_media
        )

@app.route('/em-add-cash', methods=['GET', 'POST'])
def expense_cash():
    cash_value = int(load_cash())
    return render_template('expense-manage/add_cash.html', current_cash = cash_value)

@app.route('/em-add-digital', methods=['GET', 'POST'])
def expense_digital():
    digital_value = load_digital()
    digital_value = int(digital_value)
    return render_template('expense-manage/add_digital.html', current_digital = digital_value)

@app.route('/em-add-saving', methods=['GET', 'POST'])
def expense_saving():
    target_value = load_target()
    current_value = load_current()
    return render_template('expense-manage/add_saving.html', target = target_value, current = current_value)

@app.route('/em-edit-expenses/<int:id>', methods=['GET'])
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    return render_template('expense-manage/edit_expense.html', expense = expense)

@app.route('/em-update-expense/<int:id>', methods=['POST'])
def update_expense(id):
    expense = Expense.query.get_or_404(id)

    if request.method == 'POST':
        expense.item = request.form['name']
        expense.cost = request.form['cost']

        try:
            db.session.commit()
            return redirect('/em-dashboard')
        except:
            print(f"Expense {expense.id} is failed to update")
    else:
        return render_template('expense-manage/edit_expense.html', expense = expense)
    
@app.route('/em-delete-expenses/<int:id>')
def delete_expense(id):
    expense = Expense.query.get_or_404(id)

    try:
        db.session.delete(expense)
        db.session.commit()
        return redirect('/em-dashboard')
    except:
        print(f'Expense {expense.id} is failed to delete')

@app.route('/em-upload-media', methods=['GET'])
def upload_media():
    return render_template('expense-manage/upload_media.html')

@app.route('/save-media', methods=['POST'])
def save_media():
    file = request.files.get('media')
    folder = request.form.get('type')
    file_type = request.form.get('filetype')

    if file and file.filename != '':
        extension_name = os.path.splitext(file.filename)[1].lower()
        datestr = datetime.now().strftime("%Y%m%d")

        filename = f"Upload_{datestr}_{get_next()}{extension_name}"
        target_dir = os.path.join(UPLOAD_FOLDER, folder)

        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        save_path = os.path.join(target_dir, filename)
        file.save(save_path)

        db_path = f"/media/{folder}/{filename}"
        new_media = Media(
            filename = filename,
            filetype = file_type,
            filepath = db_path
        )

        db.session.add(new_media)
        db.session.commit()

    return redirect('/em-dashboard')

@app.route('/em-delete-media/<int:id>')
def delete_media(id):
    media = Media.query.get_or_404(id)
    file_path = os.path.join(current_app.root_path, 'static', media.filepath.lstrip('/'))
    print(file_path)

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print("File removed")

            db.session.delete(media)
            db.session.commit()
            return redirect('/em-dashboard')
        else:
            print(file_path)
            print("File doesn't exist. Not removing")
            return redirect('/em-dashboard')
    except:
        print(f"Media {media.id} is failed to delete")

@app.route('/em-transfer-to-cash', methods=['POST', 'GET'])
def transfer():

    if request.method == 'POST':
        total_transfer = request.form.get('transfer')
        total_transfer = float(total_transfer)
        digital_value = load_digital()
        
        if total_transfer > digital_value:
            return redirect(url_for('expense_digital', error='amount'))
        
        cash_value = load_cash()
        digital_value = digital_value - total_transfer
        cash_value = cash_value + total_transfer

        data = load_all_data()
        data['cash'] = float(cash_value)
        data['digital'] = float(digital_value)

        save_all_data(data)
        return redirect('/em-dashboard')

@app.route('/em-finalize')
def finalize():
    total_spent = db.session.query(func.sum(Expense.cost).filter(Expense.date_created >= sync_time()[4], Expense.date_created < sync_time()[5])).scalar() or 0
    cash_spent = db.session.query(func.sum(Expense.cost).filter(Expense.date_created >= sync_time()[4], Expense.date_created < sync_time()[5], Expense.type == 'cash')).scalar() or 0
    digital_spent = db.session.query(func.sum(Expense.cost).filter(Expense.date_created >= sync_time()[4], Expense.date_created < sync_time()[5], Expense.type == 'digital')).scalar() or 0

    cash_value = load_cash()
    digital_value = load_digital()
    cash_left = cash_value - cash_spent
    digital_left = digital_value - digital_spent

    cash_value = load_cash()
    digital_value = load_digital()

    count_expenses = Expense.query.filter(Expense.date_created >= sync_time()[4], Expense.date_created < sync_time()[5]).all()
    latest = db.session.query(Media.filepath, Media.filetype, Media.filename).filter(Media.uploaded_at >= sync_time()[4], Media.uploaded_at < sync_time()[5]).order_by(Media.id.desc()).first()

    if not latest:    
        return redirect(url_for('expense_dashboard', error='no_media'))
    else:
        latest_path, latest_type, latest_media = latest
        print(f"Latest media path exist: {latest_path}")
        
        win_sys_path = os.path.join(r"D:\Obsidian\Server\static", latest_path.lstrip('/'))
        linux_sys_path = os.path.join(r"/mnt/data/Obsidian/Server/Ceres/static/", latest_path.lstrip('/'))
        print(f"System path available: {win_sys_path} / {linux_sys_path}")

        win_abs_path = "file:///" + win_sys_path.replace("\\", "/")
        linux_abs_path = "file://" + linux_sys_path
        
        print(f"Absolute path generated: {win_abs_path} / {linux_abs_path}")
        print(f"ReceivedData\nTotal: {total_spent} | CashUsage: {cash_spent} | DigitalUsage : {digital_spent} | CashLeft: {cash_left} | DigitalLeft: {digital_left}")

        rendered = render_template('expense-manage/report.html', cash_left = cash_left, digital_left = digital_left, total_spent = total_spent, expenses = count_expenses, media = latest_media, helper = currency_filter, type = latest_type)
        
        win_dir = r"D:\Obsidian\Management\Monetary"
        linux_dir = r"/mnt/data/Obsidian/Management/Monetary"

        win_target_dir = os.path.join(win_dir, sync_time()[3], sync_time()[2])
        linux_target_dir = os.path.join(linux_dir, sync_time()[3], sync_time()[2])

        os.makedirs(win_target_dir, exist_ok=True)
        os.makedirs(linux_target_dir, exist_ok=True)

        filename = f"{sync_time()[0].strftime("%d")}.md"

        win_filepath = os.path.join(win_target_dir, filename)
        linux_filepath = os.path.join(linux_target_dir, filename)
        print(f"Windows: {win_filepath}\nLinux: {linux_filepath}")

        if platform.system() == "Windows":
            if os.path.exists(win_filepath):
                return redirect(url_for('expense_dashboard', error='existed'))
        else:
            if os.path.exists(linux_filepath):
                return redirect(url_for('expense_dashboard', error='existed'))

        try:
            if platform.system() == "Windows":
                with open(win_filepath, 'w', encoding='utf-8') as f:
                    f.write(rendered)
            else:
                with open(linux_filepath, 'w', encoding='utf-8') as f:
                    f.write(rendered)
            print(f"File {filename} is successfully saved")

            data = load_all_data()
            data['cash'] = float(cash_left)
            data['digital'] = float(digital_left)
            save_all_data(data)

            return redirect(url_for('expense_dashboard', info='success'))
        except Exception as e:
            print(f"File {filename} failed to save: {e}")
            return redirect(url_for('expense_dashboard', error='save_file'))

@app.route('/em-debug')
def debug():
    med = db.session.query(Media.filepath).filter(Media.uploaded_at >= sync_time()[4], Media.uploaded_at < sync_time()[5]).order_by(Media.id.desc()).first()
    print(med)
    # expenses = Expense.query.filter(Expense.date_created >= sync_time()[4], Expense.date_created < sync_time()[5]).all()
    # print(f"`today_start` value: {sync_time()[4]}")
    # print(f"actual today: {sync_time()[0]}")
    # print("Date based on variable `today_start`:::::")
    # for exp in expenses:
    #     if exp.date_created < sync_time()[4]:
    #         print(f"Data {exp.id} is outdated: {exp.date_created}")
    #     else:
    #         print(f"Data {exp.id} is up to date: {exp.date_created}")
    # print("Date based on variable `now`:::::")
    # for exp in expenses:
    #     if exp.date_created < sync_time()[0]:
    #         print(f"Data {exp.id} is outdated: {exp.date_created}")
    #     else:
    #         print(f"Data {exp.id} is up to date: {exp.date_created}")

    return redirect('/em-dashboard')


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
