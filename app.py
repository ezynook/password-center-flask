from flask import Flask,render_template, redirect, flash, request, url_for, send_file
import base64
import random
import sqlite3
import pandas as pd
from datetime import datetime
from configparser import ConfigParser
import os

app = Flask(__name__)
app.secret_key = 'MjkwOQ=='

conn = sqlite3.connect('db/datastore.db', check_same_thread=False)
config = ConfigParser()
config.read("app.cfg")
HOST = config["DEFAULT"]['HOST']
PORT = config["DEFAULT"]['PORT']

def getToday():
    now = datetime.now()
    today = now.strftime("%d/%m/%Y %H:%M:%S")
    new_text = now.strftime("%d%m%Y%H%M%S")
    return [today, new_text]

def checkDup(macaddr):
    check = conn.execute(f"SELECT COUNT(*) from tbl_password WHERE mac_address = '{macaddr}'").fetchone()[0]
    if check == 0:
        return True
    else:
        return False

@app.route("/")
def index():
    listfile = os.listdir("./")
    for item in listfile:
        if item.endswith(".xlsx"):
            os.remove(os.path.join("./", item))

    result = pd.read_sql("SELECT DISTINCT * FROM tbl_password", con=conn)
    return render_template('index.html', data=result)

@app.route("/encode")
def encode():
    result = conn.execute("SELECT * FROM tbl_password").fetchall()
    return render_template('encode.html', data2=result)

@app.route("/encode_action", methods=['POST'])
def encode_action():
    mac_address = request.form.get('mac')
    mac_address = mac_address.replace(':','')
    device_name = request.form.get('device_name')
    customer = request.form.get('customer')
    site = request.form.get('site')
    camaraname = request.form.get('camaraname')
    if len(mac_address) >= 10:
        length_db = conn.execute("SELECT * from config").fetchone()[1]
        # special_cahractor = "!#$%&*+-?@^"
        pass1 = base64.b64encode(mac_address.encode('ascii'))[:length_db]
        pass2 = base64.b64encode(mac_address.encode('ascii'))
        # map_special_charactor = "".join([random.choice(special_cahractor) for n in range(2)])
        map_special_charactor = "!#"
        final = str(pass1)
        result = final+map_special_charactor
        cut_single = result.replace("'",'')[1:]
        full2 = str(pass2)
        decompress = full2.replace("'",'')[1:]
        if checkDup(mac_address) == True:
            conn.execute(f"""
                INSERT INTO
                    tbl_password (mac_address, pass1, pass2, device_name, customer, site, update_dt, router_name)
                VALUES
                    ('{mac_address}','{cut_single}','{decompress}','{device_name}','{customer}','{site}','{getToday()[0]}', '{camaraname}')
            """)
            conn.commit()
        else:
            flash(f"มีการเข้ารหัสของ {mac_address} แล้ว สามารถไปค้นหาได้จากหน้าแรก")
        return render_template('encode.html', data=cut_single)
    else:
        flash(f"จำนวนของ {mac_address} ไม่ถูกต้อง ทั่วไปจะมากกว่า 10 หลักเป็นต้นไป")
        return render_template('encode.html')

@app.route("/decode")
def decode():
    return render_template('decode.html')

@app.route("/decode_action", methods=['POST'])
def decode_action():
    passwd = request.form.get('passwd')
    try:
        decode = base64.b64decode(passwd)
        decode_str = str(decode)
        result = decode_str.replace("'",'')[1:]
        if "\\" in result:
            flash('รูปแบบรหัสผ่านที่ท่านต้องการถอดระบุไม่ถูกต้อง กรุณาลองอีกครั้ง')
            return render_template('decode.html')
        return render_template('decode.html', data=result)
    except:
        flash('รูปแบบรหัสผ่านที่ท่านต้องการถอดระบุไม่ถูกต้อง กรุณาลองอีกครั้ง')
        return render_template('decode.html')

@app.route("/setting")
def setting():
    length_db = conn.execute("SELECT length from config").fetchone()[0]
    return render_template('setting.html', data=length_db)

@app.route("/save_setting", methods=['POST'])
def save_setting():
    setting = request.form.get('length')
    conn.execute(f"UPDATE config SET length = {setting} WHERE id = 1")
    conn.commit()
    flash(f'บันทึกการตั้งค่าจำนวนของการเข้ารหัสผ่านเป็น {setting} หลักแล้ว')
    return redirect(url_for('setting'))

@app.route("/delete/<int:id_rsa>")
def delete(id_rsa):
    if id_rsa == 459860:
        conn.execute("DELETE FROM tbl_password")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='tbl_password';")
        conn.commit()
        return redirect(url_for('index'))
    else:
        return {'message': 'Access Key Denied'}

@app.route("/backup")
def backup():
    tb_pass = pd.read_sql("""
            SELECT 
                id AS รหัสอัตโนมัติ,
                mac_address AS แม็คแอดเดรส,
                device_name AS ชื่ออุปกรณ์,
                customer AS ชื่อลูกค้า,
                site AS ชื่อสาขา,
                pass1 AS รหัสอุปกรณ์,
                pass2 AS รหัสใช้ในการถอด,
                update_dt AS วันที่ออกรหัส,
                router_name AS ชื่อกล้อง
            FROM
                tbl_password
    """, con=conn)
    tb_config = pd.read_sql("""
            SELECT 
                id AS ConfigID,
                length AS จำนวนหลักการเข้ารหัส
            FROM
                config
    """, con=conn)

    with pd.ExcelWriter(f"./backup_db_{getToday()[1]}.xlsx") as writer:
        tb_pass.to_excel(writer, sheet_name="รายการรหัสผ่าน", index=False)
        tb_config.to_excel(writer, sheet_name="ตั้งค่า", index=False)

    filename = f"./backup_db_{getToday()[1]}.xlsx"
    return send_file(filename, as_attachment=True)
    


if __name__ == "__main__":
    app.run(host=f'{HOST}', port=int(PORT), debug=True)